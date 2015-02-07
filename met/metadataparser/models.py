from os import path
import requests
from urlparse import urlsplit, urlparse
from urllib import quote_plus
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import get_cache
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Count
from django.db.models.signals import pre_save
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from met.metadataparser.utils import compare_filecontents
from met.metadataparser.xmlparser import MetadataParser, DESCRIPTOR_TYPES_DISPLAY
from met.metadataparser.templatetags import attributemap


TOP_LENGTH = getattr(settings, "TOP_LENGTH", 5)

def update_obj(mobj, obj, attrs=None):
    for_attrs = attrs or getattr(mobj, 'all_attrs', [])
    for attrb in attrs or for_attrs:
        if (getattr(mobj, attrb, None) and
            getattr(obj, attrb, None) and
            getattr(mobj, attrb) != getattr(obj, attrb)):
            setattr(obj, attrb,  getattr(mobj, attrb))


class Base(models.Model):
    file_url = models.URLField(verbose_name='Metadata url',
                               blank=True, null=True,
                               help_text=_(u'Url to fetch metadata file'))
    file = models.FileField(upload_to='metadata', blank=True, null=True,
                            verbose_name=_(u'metadata xml file'),
                            help_text=_("if url is set, metadata url will be "
                                        "fetched and replace file value"))
    file_id = models.CharField(blank=True, null=True, max_length=500,
                               verbose_name=_(u'File ID'))

    editor_users = models.ManyToManyField(User, null=True, blank=True,
                                          verbose_name=_('editor users'))

    class Meta:
        abstract = True

    class XmlError(Exception):
        pass

    def __unicode__(self):
        return self.url or u"Metadata %s" % self.id

    def load_file(self):
        """Only load file and parse it, don't create/update any objects"""
        if not self.file:
            return None
        metadata = MetadataParser(filename=self.file.path)
        return metadata

    def fetch_metadata_file(self):
        req = requests.get(self.file_url)
        if req.ok:
            req.raise_for_status()
        parsed_url = urlsplit(self.file_url)
        if self.file:
            self.file.seek(0)
            original_file_content = self.file.read()
            if compare_filecontents(original_file_content, req.content):
                return

        filename = path.basename(parsed_url.path)
        self.file.save(filename, ContentFile(req.content), save=False)

    def process_metadata(self):
        raise NotImplemented()


class XmlDescriptionError(Exception):
    pass


class Federation(Base):

    name = models.CharField(blank=False, null=False, max_length=200,
                            unique=True, verbose_name=_(u'Name'))
    url = models.URLField(verbose_name='Federation url',
                          blank=True, null=True)
    logo = models.ImageField(upload_to='federation_logo', blank=True,
                             null=True, verbose_name=_(u'Federation logo'))
    is_interfederation = models.BooleanField(default=False, db_index=True,
                                         verbose_name=_(u'Is interfederation'))
    slug = models.SlugField(max_length=200, unique=True)

    @property
    def _metadata(self):
        if not hasattr(self, '_metadata_cache'):
            self._metadata_cache = self.load_file()
        return self._metadata_cache

    def __unicode__(self):
        return self.name

    def get_entity_metadata(self, entityid):
        return self._metadata.get_entity(entityid)

    def get_entity(self, entityid):
        return self.entity_set.get(entityid=entityid)

    def process_metadata(self):
        metadata = self.load_file()
        if (self.file_id and metadata.file_id and
                metadata.file_id == self.file_id):
            return
        else:
            self.file_id = metadata.file_id

        if not metadata:
            return
        if not metadata.is_federation:
            raise XmlDescriptionError("XML Haven't federation form")

        update_obj(metadata.get_federation(), self)

    def process_metadata_entities(self, request=None):
        entities_from_xml = self._metadata.get_entities()

        for entity in self.entity_set.all():
            """Remove entity relation if does not exist in metadata"""
            if not self._metadata.entity_exist(entity.entityid):
                self.entity_set.remove(entity)
                if request and not entity.federations.exists():
                    messages.warning(request,
                        mark_safe(_("Orphan entity: <a href='%s'>%s</a>" %
                                (entity.get_absolute_url(), entity.entityid))))

        for m_id in entities_from_xml:
            try:
                entity = self.get_entity(entityid=m_id)
            except Entity.DoesNotExist:
                try:
                    entity = Entity.objects.get(entityid=m_id)
                    self.entity_set.add(entity)
                except Entity.DoesNotExist:
                    entity = self.entity_set.create(entityid=m_id)
            entity.process_metadata(self._metadata.get_entity(m_id))

    def get_absolute_url(self):
        return reverse('federation_view', args=[self.slug])

    def can_edit(self, user, delete):
        permission = 'delete_federation' if delete else 'change_federation'
        if user.has_perm('metadataparser.%s' % permission):
            if user in self.editor_users.all():
                return True
        return False


class EntityQuerySet(QuerySet):
    def iterator(self):
        cached_federations = {}
        for entity in super(EntityQuerySet, self).iterator():
            if not entity.file:
                federations = entity.federations.all()
                if federations:
                    federation = federations[0]
                else:
                    raise ValueError("Can't find entity metadata")

                for federation in federations:
                    if not federation.id in cached_federations:
                        cached_federations[federation.id] = federation

                    cached_federation = cached_federations[federation.id]
                    try:
                        entity.load_metadata(federation=cached_federation)
                    except ValueError:
                        # Allow entity in federation but not in federation file
                        continue
                    else:
                        break

            yield entity


class EntityManager(models.Manager):
    def get_queryset(self):
        return EntityQuerySet(self.model, using=self._db)


class EntityType(models.Model):
    name = models.CharField(blank=False, max_length=20, unique=True,
                            verbose_name=_(u'Name'), db_index=True)
    xmlname = models.CharField(blank=False, max_length=20, unique=True,
                            verbose_name=_(u'Name in XML'), db_index=True)

    def __unicode__(self):
        return self.name


class Entity(Base):

    READABLE_PROTOCOLS = {
        'urn:oasis:names:tc:SAML:1.1:protocol': 'SAML 1.1',
        'urn:oasis:names:tc:SAML:2.0:protocol': 'SAML 2.0',
        'urn:mace:shibboleth:1.0': 'Shiboleth 1.0',
    }

    entityid = models.CharField(blank=False, max_length=200, unique=True,
                                verbose_name=_(u'EntityID'), db_index=True)
    federations = models.ManyToManyField(Federation,
                                         verbose_name=_(u'Federations'))

    types = models.ManyToManyField(EntityType, verbose_name=_(u'Type'))

    registration_authority = models.CharField(blank=True, null='True', max_length=200,
                                              verbose_name=_(u'Registration Authority'))
    registration_instant = models.DateTimeField(blank=True, null=True,
                                                verbose_name=_(u'Registration Instant'))
    languages = models.CharField(blank=True, null='True', max_length=200,
                                              verbose_name=_(u'Languages'))
    protocols = models.CharField(blank=True, null='True', max_length=500,
                                              verbose_name=_(u'Protocols'))
    scopes = models.CharField(blank=True, null='True', max_length=500000,
                                              verbose_name=_(u'Attribute Scopes'))
    attributes = models.CharField(blank=True, null='True', max_length=5000,
                                              verbose_name=_(u'Requested Attributes'))
    attributes_optional = models.CharField(blank=True, null='True', max_length=5000,
                                              verbose_name=_(u'Optional Attributes'))

    objects = models.Manager()
    longlist = EntityManager()

    @property
    def organization(self):
        names = self._get_uuinfo('organizationName')
        urls = self._get_uuinfo('organizationUrl')
        displayNames = self._get_uuinfo('organizationDisplayName')

        vals = []
        for lang, name in names.items():
            val = {}
            val['name'] = name
            val['lang'] = lang
            if lang in displayNames.keys():
                val['displayName'] = displayNames[lang]
            if lang in urls.keys():
                val['URL'] = urls[lang]
            vals.append(val)
        return vals

    @property
    def name(self):
        return self._get_uuinfo('displayName')

    @property
    def description(self):
        return self._get_uuinfo('description')

    @property
    def infoUrl(self):
        return self._get_uuinfo('infoUrl')

    @property
    def privacyUrl(self):
        return self._get_uuinfo('privacyUrl')

    def display_protocols(self):
        protocols = []
        for proto in self.protocols.split(' '):
            protocols.append(self.READABLE_PROTOCOLS.get(proto, proto))
        return protocols

    def display_attributes(self):
        attributes = {}
        for attr in self.attributes.split(' '):
            oid = attr.replace('urn:oid:', '')
            if attr in attributemap.MAP['fro']:
                attributes[oid] = attributemap.MAP['fro'][attr]
            else:
                attributes[oid] = attr
        return attributes

    def display_attributes_optional(self):
        attributes = {}
        for attr in self.attributes_optional.split(' '):
            oid = attr.replace('urn:oid:', '')
            if attr in attributemap.MAP['fro']:
                attributes[oid] = attributemap.MAP['fro'][attr]
            else:
                attributes[oid] = attr
        return attributes

    @property
    def contacts(self):
        if not hasattr(self, '_contacts_cached'):
            self._contacts_cached = EntityContact.objects.filter(entity=self)

        contacts = []
        for cur_contact in self._contacts_cached:
            if cur_contact.name and cur_contact.surname:
                contact_name = '%s %s' % (cur_contact.name, cur_contact.surname)
            elif cur_contact.name:
                contact_name = cur_contact.name
            elif cur_contact.surname:
                contact_name = cur_contact.surname
            else:
                contact_name = urlparse(cur_contact.email).path.partition('?')[0]
            c_type = 'undefined'
            if cur_contact.contact_type:
                c_type = cur_contact.contact_type
            contacts.append({ 'name': contact_name, 'email': cur_contact.email, 'type': c_type })
        return contacts

    @property
    def logos(self):
        if not hasattr(self, '_uuinfo_cached'):
            self._uuinfo_cached = EntityInfo.objects.filter(entity=self)

        logos = []
        for cur_logo in self._uuinfo_cached:
            if cur_logo.info_type == 'logos':
                logo = {}
                logo['width'] = cur_logo.width or ''
                logo['height'] = cur_logo.height or ''
                logo['file'] = cur_logo.value
                logo['lang'] = cur_logo.language
                logo['external'] = True
                logos.append(logo)

        return logos

    class Meta:
        verbose_name = _(u'Entity')
        verbose_name_plural = _(u'Entities')

    def __unicode__(self):
        return self.entityid

    def load_metadata(self, federation=None, entity_data=None):
        if not hasattr(self, '_entity_cached'):
            if self.file:
                self._entity_cached = self.load_file().get_entity(self.entityid)
            elif federation:
                self._entity_cached = federation.get_entity_metadata(self.entityid)
            elif entity_data:
                self._entity_cached = entity_data
            else:
                for federation in self.federations.all():
                    try:
                        entity_cached = federation.get_entity_metadata(self.entityid)
                        if entity_cached and hasattr(self, '_entity_cached'):
                            self._entity_cached.update(entity_cached)
                        else:
                            self._entity_cached = entity_cached
                    except ValueError:
                        continue
            if not hasattr(self, '_entity_cached'):
                raise ValueError("Can't find entity metadata")

    def _get_uuinfo(self, info, lang=None):
        if not hasattr(self, '_uuinfo_cached'):
            self._uuinfo_cached = EntityInfo.objects.filter(entity=self)

        val = {}
        for cur_info in self._uuinfo_cached:
            if cur_info.info_type == info:
                 val[cur_info.language] = cur_info.value
        return val

    def _get_property(self, prop):
        try:
            self.load_metadata()
        except ValueError:
            return None
        if hasattr(self, '_entity_cached'):
            return self._entity_cached.get(prop, None)
        else:
            raise ValueError("Not metadata loaded")

    def process_metadata(self, entity_data=None):
        if not entity_data:
            self.load_metadata()

        if self.entityid != entity_data.get('entityid'):
            raise ValueError("EntityID is not the same")

        if entity_data:
            self.registration_authority = entity_data.get('registration_authority', None)
            self.registration_instant = entity_data.get('registration_instant', None)
            self.protocols = ' '.join(entity_data.get('protocols', []))

            entity_infos = []
            old_entity_infos = EntityInfo.objects.filter(entity=self)
            # Add description, displayName, urls elements to EntityInfo table (if not already present)
            for cur_type in ['description', 'displayName', 'infoUrl', 'privacyUrl']:
                for lang, val in entity_data.get(cur_type, {}).items():
                    new_entity_info =  EntityInfo(info_type=cur_type, language=lang, value=val, entity=self)
                    if not new_entity_info in old_entity_infos:
                        entity_infos.append(new_entity_info)

            # Add Logo elements to EntityInfo table (if not already present)
            for val in entity_data.get('logos', []):
                new_entity_info = EntityInfo(info_type='logos', language=val['lang'], value=val['file'], entity=self,
                                             width=val['width'], height=val['height'])
                if not new_entity_info in old_entity_infos:
                    entity_infos.append(new_entity_info)

            # Add Organization information to EntityInfo table (if not already present)
            for lang, data in entity_data.get('organization', {}).items():
                if 'URL' in data:
                    new_entity_info = EntityInfo(info_type='organizationUrl', language=lang, value=data['URL'], entity=self)
                    if not new_entity_info in old_entity_infos:
                        entity_infos.append(new_entity_info)
                if 'name' in data:
                    new_entity_info = EntityInfo(info_type='organizationName', language=lang, value=data['name'], entity=self)
                    if not new_entity_info in old_entity_infos:
                        entity_infos.append(new_entity_info)
                if 'displayName' in data:
                    new_entity_info = EntityInfo(info_type='organizationDisplayName', language=lang, value=data['displayName'], entity=self)
                    if not new_entity_info in old_entity_infos:
                        entity_infos.append(new_entity_info)

            EntityInfo.objects.bulk_create(entity_infos)

            # Add entity contacts if in metadata
            contacts = []
            old_contacts = EntityContact.objects.filter(entity=self)
            for cont in entity_data.get('contacts', []):
                if cont['email']:
                    new_contact = EntityContact(contact_type=cont['type'], name=cont['name'], surname=cont['surname'], email=cont['email'], entity=self)
                    if not new_contact in old_contacts:
                        contacts.append(new_contact)
            EntityContact.objects.bulk_create(contacts)

            self.languages = ' '.join(entity_data.get('languages', []))
            self.scopes = ' '.join(entity_data.get('scopes', []))
            attributes = entity_data.get('attr_requested', {'required': [], 'optional': []})
            self.attributes = ' '.join(attributes['required'])
            self.attributes_optional = ' '.join(attributes['optional'])

            self.save()

        self._entity_cached = entity_data

        xml_types = entity_data.get('entity_types', None)
        if xml_types:
            for etype in xml_types:
                try:
                    entity_type = EntityType.objects.get(xmlname=etype)
                except EntityType.DoesNotExist:
                    entity_type = EntityType.objects.create(xmlname=etype,
                                              name=DESCRIPTOR_TYPES_DISPLAY[etype])
                if entity_type not in self.types.all():
                    self.types.add(entity_type)

    def to_dict(self):
        self.load_metadata()

        entity = self._entity_cached.copy()
        entity["types"] = [(unicode(f)) for f in self.types.all()]
        entity["federations"] = [{u"name": unicode(f), u"url": f.get_absolute_url()}
                                    for f in self.federations.all()]

        if self.registration_authority:
            entity["registration_authority"] = self.registration_authority
        if self.registration_instant:
            entity["registration_instant"] = datetime.strptime(self.registration_instant, '%Y-%m-%dT%H:%M%SZ')

        if "file_id" in entity.keys():
            del entity["file_id"]
        if "entity_types" in entity.keys():
            del entity["entity_types"]

        return entity

    @classmethod
    def get_most_federated_entities(self, maxlength=TOP_LENGTH, cache_expire=None):
        entities = None
        if cache_expire:
            cache = get_cache("default")
            entities = cache.get("most_federated_entities")

        if not entities:
            # Entities with count how many federations belongs to, and sorted by most first
            entities = Entity.objects.all().annotate(
                                 federationslength=Count("federations")).order_by("-federationslength")[:maxlength]

        if cache_expire:
            cache = get_cache("default")
            cache.set("most_federated_entities", entities, cache_expire)

        return entities

    def get_absolute_url(self):
        return reverse('entity_view', args=[quote_plus(self.entityid)])

    def can_edit(self, user, delete):
        permission = 'delete_entity' if delete else 'change_entity'
        if user.has_perm('metadataparser.%s' % permission):
            if user in self.editor_users.all():
                return True

        for federation in self.federations.all():
            if federation.can_edit(user, False):
                return True

        return False

class EntityInfo(models.Model):
    info_type = models.CharField(blank=True, max_length=30,
                                verbose_name=_(u'Info Type'), db_index=True)
    language = models.CharField(blank=True, null=True, max_length=10,
                                verbose_name=_(u'Language'))
    value = models.CharField(blank=False, max_length=100000,
                                verbose_name=_(u'Info Value'))
    width = models.PositiveSmallIntegerField(null=True, default=0,
                                verbose_name=_(u'Width'))
    height = models.PositiveSmallIntegerField(null=True, default=0,
                                verbose_name=_(u'Height'))

    entity = models.ForeignKey(Entity, blank=False,
                                verbose_name=_('Entity'))

    def __unicode__(self):
        return "[%s:%s] %s" % (self.info_type, self.language, self.value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for field in ['info_type', 'language', 'value', 'width', 'height']:
                if self.__dict__[field] != other.__dict__[field]:
                    return False
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

class EntityContact(models.Model):
    contact_type = models.CharField(blank=True, max_length=30,
                                verbose_name=_(u'Contact Type'), db_index=True)
    name = models.CharField(blank=True, null=True, max_length=200,
                                verbose_name=_(u'Name'))
    surname = models.CharField(blank=True, null=True, max_length=200,
                                verbose_name=_(u'Surname'))
    email = models.CharField(blank=False, max_length=500,
                                verbose_name=_(u'Email'))

    entity = models.ForeignKey(Entity, blank=False,
                                verbose_name=_('Entity'))

    def __unicode__(self):
        return "[%s] %s %s <%s>" % (self.contact_type, self.name, self.surname, self.email)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for field in ['contact_type', 'name', 'surname', 'email']:
                if self.__dict__[field] != other.__dict__[field]:
                    return False
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

@receiver(pre_save, sender=Federation, dispatch_uid='federation_pre_save')
def federation_pre_save(sender, instance, **kwargs):
    if instance.file_url:
        instance.fetch_metadata_file()
    if instance.name:
        instance.slug = slugify(unicode(instance))[:200]


@receiver(pre_save, sender=Entity, dispatch_uid='entity_pre_save')
def entity_pre_save(sender, instance, **kwargs):
    if instance.file_url:
        instance.fetch_metadata_file()
        instance.process_metadata()
