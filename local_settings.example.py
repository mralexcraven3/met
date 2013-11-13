#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
#########################################################################################

import os
BASEDIR = os.path.abspath(os.path.dirname(__file__))


DEBUG = True
#DEBUG = True
TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'met',                      # Or path to database file if using sqlite3.
        'USER': 'met',                      # Not used with sqlite3.
        'PASSWORD': 'met',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

INTERNAL_IPS = ('192.168.122.1',)

MEDIA_ROOT = os.path.join(os.environ.get('HOME', '/home/met'), 'media')
STATIC_ROOT = os.path.join(os.environ.get('HOME', '/home/met'), 'static')


TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(BASEDIR, 'templates'),
)


SAML_ATTRIBUTE_MAPPING = {
    'eppn': ('username', 'email'),
    'mail': ('username', 'email', ),
    'cn': ('first_name', ),
    'sn': ('last_name', ),
}


ORGANIZATION_NAME = 'Your organization'

SHIB_LOGOUT_URL = '/Shibboleth.sso/Logout'

MAIL_CONFIG = {
  # Email server name
  'email_server': 'mailserver.daasi.de',
  # Email server port number
  'email_server_port': '25',
  # Addressee email address
  'to_email_address': ['tamim.ziai@daasi.de'],
  # own email address
  'from_email_address': 'met@refeds.org',
  # Subject for metadata refresh error
  'refresh_subject': 'Metadata failure for federation %s',
  # Subject for comments
  'comment_subject': 'Comment for entity \'%s\'',
  # Subject for I'd like ...
  'proposal_subject': 'Proposal for gathering the entity %s in a federation',
  # Body for I'd like ...
  'proposal_body': 'I\'d like the entity %s to be gathered in the following federation(s):%s\n\nComment:\n%s',
}

STATS = {
    # Features that have to be saved in the database
    'features': {
        'sp': 'SPSSODescriptor',
        'idp': 'IDPSSODescriptor',
        'sp_saml1': 'urn:oasis:names:tc:SAML:1.1:protocol',
        'sp_saml2': 'urn:oasis:names:tc:SAML:2.0:protocol',
        'sp_shib1': 'urn:mace:shibboleth:1.0',
        'idp_saml1': 'urn:oasis:names:tc:SAML:1.1:protocol',
        'idp_saml2': 'urn:oasis:names:tc:SAML:2.0:protocol',
        'idp_shib1': 'urn:mace:shibboleth:1.0',
    },
    
    # Protocols
    'protocols': ['saml1', 'saml2', 'shib1'],

    # Feature names
    'feature_names': {
        'sp': 'SP',
        'idp': 'IDP',
        'sp_saml1': 'SP SAML 1.1',
        'sp_saml2': 'SP SAML 2.0',
        'sp_shib1': 'SP Shibboleth 1.0',
        'idp_saml1': 'IDP SAML 1.1',
        'idp_saml2': 'IDP SAML 2.0',
        'idp_shib1': 'IDP Shibboleth 1.0',
    },

    # Statistics that can be shown (values are keys for 'features')
    'statistics': {
        'entity_by_type': {'terms': ['sp', 'idp'], 'title': 'Services', 'x_title': 'Time', 'y_title': 'Count'},
        'entity_by_protocol': {'terms': ['sp_saml1', 'sp_saml2', 'sp_shib1', 'idp_saml1', 'idp_saml2', 'idp_shib1'], 'title': 'Protocols', 'x_title': 'Time', 'y_title': 'Count'},
    },
    
    # Time format in the x axis
    'time_format': '%m/%d/%Y %H:%M',
}