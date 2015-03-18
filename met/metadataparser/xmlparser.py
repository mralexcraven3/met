#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
# Current version of MET has been revised for performance improvements by Andrea Biancini,
# Consortium GARR, http://www.garr.it
#########################################################################################

from lxml import etree

NAMESPACES = {
    'xml': 'http://www.w3.org/XML/1998/namespace',
    'xs': 'xs="http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'md': 'urn:oasis:names:tc:SAML:2.0:metadata',
    'mdui': 'urn:oasis:names:tc:SAML:metadata:ui',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'saml': 'urn:oasis:names:tc:SAML:2.0:assertion',
    'samlp': 'urn:oasis:names:tc:SAML:2.0:protocol',
    'mdrpi': 'urn:oasis:names:tc:SAML:metadata:rpi',
    'shibmd': 'urn:mace:shibboleth:metadata:1.0',
    }

SAML_METADATA_NAMESPACE = NAMESPACES['md']

XML_NAMESPACE = NAMESPACES['xml']
XMLDSIG_NAMESPACE = NAMESPACES['ds']
MDUI_NAMESPACE = NAMESPACES['mdui']

#DESCRIPTOR_TYPES = ('RoleDescriptor', 'IDPSSODescriptor',
#                    'SPSSODescriptor', 'AuthnAuthorityDescriptor',
#                    'AttributeAuthorityDescriptor', 'PDPDescriptor',
#                    'AffiliationDescriptor',)

DESCRIPTOR_TYPES = ('IDPSSODescriptor', 'SPSSODescriptor',)
DESCRIPTOR_TYPES_DISPLAY = {}
for item in DESCRIPTOR_TYPES:
    DESCRIPTOR_TYPES_DISPLAY[item] = item.replace('SSODescriptor', '')

DESCRIPTOR_TYPES_UTIL = ["md:%s" % item for item in DESCRIPTOR_TYPES]


def addns(node_name, namespace=SAML_METADATA_NAMESPACE):
    '''Return a node name qualified with the XML namespace'''
    return '{' + namespace + '}' + node_name


def delns(node, namespace=SAML_METADATA_NAMESPACE):
    return node.replace('{' + namespace + '}', '')


def getlang(node):
    if 'lang' in node.attrib:
        return node.attrib['lang']
    elif addns('lang', NAMESPACES['xml']) in node.attrib:
        return node.attrib[addns('lang', NAMESPACES['xml'])]

FEDERATION_ROOT_TAG = addns('EntitiesDescriptor')
ENTITY_ROOT_TAG = addns('EntityDescriptor')


class MetadataParser(object):
    def __init__(self, filename=None):
        if filename is None:
            raise ValueError('filename is required')

        self.filename = filename
        context = etree.iterparse(self.filename, events=('start',))
        context = iter(context)
        event, self.rootelem = context.next()
        self.file_id = self.rootelem.get('ID', None)
        self.is_federation = (self.rootelem.tag == FEDERATION_ROOT_TAG)
        self.is_entity = not self.is_federation

    def _get_entity_by_id(self, context, entityid, details):
        for event, element in context:
            if element.attrib['entityID'] == entityid:
                entity_attrs = (('entityid', 'entityID'), ('file_id', 'ID'))
                lang_seen = []
                entity = {}
                for (dict_attr, etree_attr) in entity_attrs:
                   entity[dict_attr] = element.get(etree_attr, None)
                entity['xml'] = etree.tostring(element, pretty_print=True)

                entity_types = self.entity_types(element)
                e_type = None
                if entity_types:
                    entity['entity_types'] = entity_types
                    e_type = entity_types[0]
                displayName = self.entity_displayname(element)
                if displayName:
                    entity['displayName'] = displayName
                    for lang in displayName.keys():
                        if not lang in lang_seen:
                            lang_seen.append(lang)
                reg_info = self.registration_information(element)
                if reg_info and 'authority' in reg_info:
                   entity['registration_authority'] = reg_info['authority']
                protocols = self.entity_protocols(element, e_type)
                if protocols:
                    entity['protocols'] = protocols

                if details:
                    description = self.entity_description(element)
                    if description:
                       entity['description'] = description
                       for lang in description.keys():
                            if not lang in lang_seen:
                                lang_seen.append(lang)
                    info_url = self.entity_information_url(element)
                    if info_url:
                        entity['infoUrl'] = info_url
                        for lang in info_url.keys():
                            if not lang in lang_seen:
                                lang_seen.append(lang)
                    privacy_url = self.entity_privacy_url(element)
                    if privacy_url:
                        entity['privacyUrl'] = privacy_url
                        for lang in privacy_url.keys():
                            if not lang in lang_seen:
                                lang_seen.append(lang)
                    organization = self.entity_organization(element)
                    if organization:
                        entity['organization'] = organization
                        for lang in organization.keys():
                            if not lang in lang_seen:
                                lang_seen.append(lang)
                    logos = self.entity_logos(element)
                    if logos:
                        entity['logos'] = logos
                    if reg_info and 'instant' in reg_info:
                       entity['registration_instant'] = reg_info['instant']
                    entity['languages'] = lang_seen
                    scopes = self.entity_attribute_scope(element)
                    if scopes:
                        entity['scopes'] = scopes
                    attr_requested = self.entity_requested_attributes(element)
                    if attr_requested:
                        entity['attr_requested'] = attr_requested
                    contacts = self.entity_contacts(element)
                    if contacts:
                        entity['contacts'] = contacts

                yield entity
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        del context

    def get_federation(self, attrs=None):
        assert self.is_federation
        federation_attrs = attrs or ('ID', 'Name',)
        federation = {}

        for attr in federation_attrs:
            federation[attr] = self.rootelem.get(attr, None)

        return federation

    def get_entity(self, entityid, details=True):
        context = etree.iterparse(self.filename, tag=addns('EntityDescriptor'), events=('end',))

        element = None
        for element in self._get_entity_by_id(context, entityid, details):
            return element

        raise ValueError("Entity not found: %s" % entityid)

    def entity_exist(self, entityid):
        entity_xpath = self.rootelem.xpath("//md:EntityDescriptor[@entityID='%s']"
                                         % entityid, namespaces=NAMESPACES)
        return (len(entity_xpath) > 0)

    def _get_entities_id(self, context):
        for event, element in context:
            yield element.attrib['entityID']
            element.clear()
            while element.getprevious() is not None:
                del element.getparent()[0]
        del context

    def get_entities(self):
        # Return entityid list
        context = etree.iterparse(self.filename, tag=addns('EntityDescriptor'), events=('end',))
        return list(self._get_entities_id(context))

    def entity_types(self, entity):
        expression = ("|".join([desc for desc in DESCRIPTOR_TYPES_UTIL]))

        elements = entity.xpath(expression, namespaces=NAMESPACES)
        types = [element.tag.split("}")[1] for element in elements]
        return types

    def entity_protocols(self, entity, entity_type='IDPSSODescriptor'):
        raw_protocols = entity.xpath("./md:%s"
                                     "/@protocolSupportEnumeration" % (entity_type),
                                     namespaces=NAMESPACES)
        if raw_protocols:
            protocols = raw_protocols[0]
            return protocols.split(' ')
        return []

    def entity_displayname(self, entity):
        languages = {}

        names = entity.xpath(".//mdui:UIInfo"
                             "//mdui:DisplayName",
                             namespaces=NAMESPACES)

        for dn_node in names:
            lang = getlang(dn_node)
            if lang is None:
                continue  # the lang attribute is required

            languages[lang] = dn_node.text

        return languages

    def entity_description(self, entity):
        languages = {}

        names = entity.xpath(".//mdui:UIInfo"
                             "//mdui:Description",
                             namespaces=NAMESPACES)

        for dn_node in names:
            lang = getlang(dn_node)
            if lang is None:
                continue  # the lang attribute is required

            languages[lang] = dn_node.text

        return languages

    def entity_information_url(self, entity):
        languages = {}

        names = entity.xpath(".//mdui:UIInfo"
                             "//mdui:InformationURL",
                             namespaces=NAMESPACES)

        for dn_node in names:
            lang = getlang(dn_node)
            if lang is None:
                continue  # the lang attribute is required

            languages[lang] = dn_node.text

        return languages

    def entity_privacy_url(self, entity):
        languages = {}

        names = entity.xpath(".//mdui:UIInfo"
                             "//mdui:PrivacyStatementURL",
                             namespaces=NAMESPACES)

        for dn_node in names:
            lang = getlang(dn_node)
            if lang is None:
                continue  # the lang attribute is required

            languages[lang] = dn_node.text

        return languages

    def entity_organization(self, entity):
        orgs = entity.xpath(".//md:Organization",
                            namespaces=NAMESPACES)
        languages = {}
        for org_node in orgs:
            for attr in ('name', 'displayName', 'URL'):
                node_name = 'Organization' + attr[0].upper() + attr[1:]
                for node in org_node.findall(addns(node_name)):
                    lang = getlang(node)
                    if lang is None:
                        continue  # the lang attribute is required

                    lang_dict = languages.setdefault(lang, {})
                    lang_dict[attr] = node.text

        #result = []
        #for lang, data in languages.items():
        #    data['lang'] = lang
        #    result.append(data)
        return languages

    def entity_logos(self, entity):
        xmllogos = entity.xpath(".//mdui:UIInfo"
                                "/mdui:Logo",
                                namespaces=NAMESPACES)
        logos = []
        for logo_node in xmllogos:
            if logo_node.text is None:
                continue  # the file attribute is required
            logo = {}
            logo['width'] = int(logo_node.attrib.get('width', '0'))
            logo['height'] = int(logo_node.attrib.get('height', '0'))
            logo['file'] = logo_node.text
            logo['lang'] = getlang(logo_node)
            logos.append(logo)
        return logos

    def registration_information(self, entity):
        reg_info = entity.xpath(".//md:Extensions"
                                "/mdrpi:RegistrationInfo",
                                namespaces=NAMESPACES)
        info = {}
        if reg_info:
            info['authority'] = reg_info[0].attrib.get('registrationAuthority')
            info['instant'] = reg_info[0].attrib.get('registrationInstant')
        return info

    def entity_attribute_scope(self, entity):
        scope_node = entity.xpath(".//md:Extensions"
                                  "/shibmd:Scope",
                                  namespaces=NAMESPACES)

        scope = []
        for cur_scope in scope_node:
            if not cur_scope.text in scope:
                scope.append(cur_scope.text)
        return scope

    def entity_requested_attributes(self, entity):
        xmllogos = entity.xpath(".//md:AttributeConsumingService"
                                "/md:RequestedAttribute",
                                namespaces=NAMESPACES)
        attrs = {}
        attrs['required'] = []
        attrs['optional'] = []
        for attr_node in xmllogos:
            required = attr_node.attrib.get('isRequired', 'false')
            index = 'optional'
            if required == 'true':
                index = 'required'
            attrs[index].append(attr_node.attrib.get('Name', None))
        return attrs

    def entity_contacts(self, entity):
        contacts = entity.xpath(".//md:ContactPerson",
                                namespaces=NAMESPACES)
        cont = []
        for cont_node in contacts:
            c_type = cont_node.attrib.get('contactType', '')
            name = cont_node.xpath(".//md:GivenName", namespaces=NAMESPACES)
            if name: name = name[0].text
            else: name = None
            surname = cont_node.xpath(".//md:SurName", namespaces=NAMESPACES)
            if surname: surname = surname[0].text
            else: surname = None
            email = cont_node.xpath(".//md:EmailAddress", namespaces=NAMESPACES)
            if email: email = email[0].text
            else: email = None
            cont.append({ 'type': c_type, 'name': name, 'surname': surname, 'email': email })
        return cont
