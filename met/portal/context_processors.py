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
