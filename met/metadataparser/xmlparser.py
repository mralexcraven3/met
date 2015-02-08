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

    def __init__(self, filename=None, data=None):
        if filename:
            try:
                etree_parser = etree.parse(filename)
            except etree.XMLSyntaxError:
                raise ValueError('invalid metadata XML')
        elif data:
            try:
                etree_parser = etree.XML(data)
            except etree.XMLSyntaxError:
                raise ValueError('invalid metadata XML')
        else:
            raise ValueError('filename or data are required')

        self.etree = etree_parser.getroot()
        self.file_id = self.etree.get('ID', None)
        self.is_federation = (self.etree.tag == FEDERATION_ROOT_TAG)
        self.is_entity = not self.is_federation

    def get_federation(self, attrs=None):
        assert self.is_federation
        federation_attrs = attrs or ('ID', 'Name',)
        federation = {}

        for attr in federation_attrs:
            federation[attr] = self.etree.get(attr, None)

        return federation

    def get_entity(self, entityid):
        entity_xpath = self.etree.xpath("//md:EntityDescriptor[@entityID='%s']"
                                         % entityid, namespaces=NAMESPACES)
        if len(entity_xpath):
            entity_etree = entity_xpath[0]
        else:
            raise ValueError("Entity not found: %s" % entityid)

        entity_attrs = (('entityid', 'entityID'), ('file_id', 'ID'))
        lang_seen = []
        entity = {}
        for (dict_attr, etree_attr) in entity_attrs:
           entity[dict_attr] = entity_etree.get(etree_attr, None)
        entity['xml'] = etree.tostring(entity_etree, pretty_print=True)

        entity_types = self.entity_types(entity_etree)
        if entity_types:
            entity['entity_types'] = entity_types
        displayName = self.entity_displayname(entity_etree)
        if displayName:
            entity['displayName'] = displayName
            for lang in displayName.keys():
                if not lang in lang_seen:
                    lang_seen.append(lang)
        description = self.entity_description(entity_etree)
        if description:
            entity['description'] = description
            for lang in description.keys():
                if not lang in lang_seen:
                    lang_seen.append(lang)
        info_url = self.entity_information_url(entity_etree)
        if info_url:
            entity['infoUrl'] = info_url
            for lang in info_url.keys():
                if not lang in lang_seen:
                    lang_seen.append(lang)
        privacy_url = self.entity_privacy_url(entity_etree)
        if privacy_url:
            entity['privacyUrl'] = privacy_url
            for lang in privacy_url.keys():
                if not lang in lang_seen:
                    lang_seen.append(lang)
        protocols = self.entity_protocols(entity_etree)
        if protocols:
            entity['protocols'] = protocols
        organization = self.entity_organization(entity_etree)
        if organization:
            entity['organization'] = organization
            for lang in organization.keys():
                if not lang in lang_seen:
                    lang_seen.append(lang)
        logos = self.entity_logos(entity_etree)
        if logos:
            entity['logos'] = logos
        reg_info = self.registration_information(entity_etree)
        if reg_info and 'authority' in reg_info:
           entity['registration_authority'] = reg_info['authority']
        if reg_info and 'instant' in reg_info:
           entity['registration_instant'] = reg_info['instant']
        entity['languages'] = lang_seen
        scopes = self.entity_attribute_scope(entity_etree)
        if scopes:
            entity['scopes'] = scopes
        attr_requested = self.entity_requested_attributes(entity_etree)
        if attr_requested:
            entity['attr_requested'] = attr_requested
        contacts = self.entity_contacts(entity_etree)
        if contacts:
            entity['contacts'] = contacts
        return entity

    def entity_exist(self, entityid):
        entity_xpath = self.etree.xpath("//md:EntityDescriptor[@entityID='%s']"
                                         % entityid, namespaces=NAMESPACES)
        return (len(entity_xpath) > 0)

    def get_entities(self):
        # Return entityid list
        return self.etree.xpath("//@entityID")

    def entity_types(self, entity):
        expression = ("|".join([desc for desc in DESCRIPTOR_TYPES_UTIL]))

        elements = entity.xpath(expression, namespaces=NAMESPACES)
        types = [element.tag.split("}")[1] for element in elements]
        return types

    def entities_by_type(self, entity_type):
        return self.etree.xpath("//md:EntityDescriptor[md:%s]/@entityID"
                                % entity_type, namespaces=NAMESPACES)

    def count_entities_by_type(self, entity_type):
        return int(self.etree.xpath("count(//md:EntityDescriptor[md:%s])" %
                               entity_type, namespaces=NAMESPACES))

    def count_entities(self):
        return int(self.etree.xpath("count(//md:EntityDescriptor)",
                                namespaces=NAMESPACES))

    def entity_protocols(self, entity):
        raw_protocols = entity.xpath("./md:IDPSSODescriptor"
                                     "/@protocolSupportEnumeration",
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
