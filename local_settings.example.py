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
import saml2
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

SAML2DIR = os.path.join(BASEDIR, 'saml2')
SHIB_LOGOUT_URL = '/Shibboleth.sso/Logout'


SAML_CONFIG = {
  # full path to the xmlsec1 binary programm
  'xmlsec_binary': '/usr/bin/xmlsec1',

  # your entity id, usually your subdomain plus the url to the metadata view
  'entityid': 'http://met.example.com/saml2/metadata/',

  # directory with attribute mapping
  'attribute_map_dir': os.path.join(SAML2DIR, 'attribute-maps'),

  # this block states what services we provide
  'service': {
      # we are just a lonely SP
      'sp': {
          'name': 'Metadata Explorer Tool',
          'endpoints': {
              # url and binding to the assetion consumer service view
              # do not change the binding or service name
              'assertion_consumer_service': [
                  ('http://met.example.com/saml2/acs/',
                   saml2.BINDING_HTTP_POST),
                  ],
              # url and binding to the single logout service view
              # do not change the binding or service name
              'single_logout_service': [
                  ('http://met.example.com/saml2/ls/',
                   saml2.BINDING_HTTP_REDIRECT),
                  ],
              },
          # # This is commented to be compatible with simplesamlphp
          # # attributes that this project need to identify a user
          #'required_attributes': ['mail'],
          #
          # # attributes that may be useful to have but not required
          #'optional_attributes': ['eduPersonAffiliation'],

          # in this section the list of IdPs we talk to are defined
          'idp': {
              # we do not need a WAYF service since there is
              # only an IdP defined here. This IdP should be
              # present in our metadata

              # the keys of this dictionary are entity ids
              'https://idp.example.com/simplesaml/saml2/idp/metadata.php': {
                  'single_sign_on_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://idp.example.com/simplesaml/saml2/idp/SSOService.php',
                      },
                  'single_logout_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://idp.example.com/simplesaml/saml2/idp/SingleLogoutService.php',
                      },
                  },
              },
          },
      },

 # where the remote metadata is stored
  'metadata': {
      'local': [os.path.join(SAML2DIR, 'remote_metadata.xml')],
      },

  # set to 1 to output debugging information
  'debug': 1,

  # certificate
  'key_file': os.path.join(SAML2DIR, 'certs/server.key'),  # private part
  'cert_file': os.path.join(SAML2DIR, 'certs/server.crt'),  # public part

  # own metadata settings
  'contact_person': [
      {'given_name': 'Sysadmin',
       'sur_name': '',
       'company': 'Example CO',
       'email_address': 'sysadmin@example.com',
       'contact_type': 'technical'},
      {'given_name': 'Admin',
       'sur_name': 'CEO',
       'company': 'Example CO',
       'email_address': 'admin@example.com',
       'contact_type': 'administrative'},
      ],
  # you can set multilanguage information here
  'organization': {
      'name': [('Example CO', 'es'), ('Example CO', 'en')],
      'display_name': [('Example', 'es'), ('Example', 'en')],
      'url': [('http://www.example.com', 'es'), ('http://www.example.com', 'en')],
      },
  }

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