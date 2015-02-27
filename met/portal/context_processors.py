from django.conf import settings
#from saml2.config import Config

def portal_settings(request):
    """ Include some settings value in context """

    copy_attrs = ('LOGIN_URL',
                  'LOGOUT_URL',
                  'ORGANIZATION_NAME',
                  'SAML_DESCRIPTION',
                  'SAML_ENTITYID',
                  'DJANGO_FEDERATIONS',
                  'DJANGO_ADDITIONAL_IDPS')

    custom_settings = {}

    for key in copy_attrs:
        custom_settings[key] = getattr(settings, key, '')

    # Read metadata from saml local files (could be used to add IdPs to discojuice)
    #conf = Config()
    #conf.load(getattr(settings, 'SAML_CONFIG', True))
    #print "%s" % conf.metadata

    return {'portal_settings': custom_settings}
