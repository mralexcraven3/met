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

BASEURL = '/'
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

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

INTERNAL_IPS = ('192.168.122.1',)

SAML_CREATE_UNKNOWN_USER = True

SAML_DJANGO_USER_MAIN_ATTRIBUTE = 'username'

SAML_ATTRIBUTE_MAPPING = {
    'eduPersonPrincipalName': ('username',) ,
    'mail': ('email', ),
    'givenName': ('first_name', ),
    'sn': ('last_name', ),
}


ORGANIZATION_NAME = 'Your organization'

SHIB_LOGOUT_URL = '/Shibboleth.sso/Logout'

SAML2DIR = '/saml2'

SAML_CONFIG = {
  # full path to the xmlsec1 binary programm
  'xmlsec_binary': '/usr/bin/xmlsec1',

  # your entity id, usually your subdomain plus the url to the metadata view
  'entityid': 'https://met-hostname.example.com/saml2/metadata/',

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
                  ('https://met-hostname.example.com/met/saml2/acs/',
                   saml2.BINDING_HTTP_POST),
                  ],
              # url and binding to the single logout service view
              # do not change the binding or service name
              'single_logout_service': [
                  ('https://met-hostname.example.com/met/saml2/ls/',
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
              'https://idp-hostname.example.com/idp/shibboleth': {
                  'single_sign_on_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://idp-hostname.example.com/idp/profile/Shibboleth/SSO',
                      },
                  'single_logout_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://idp-hostname.example.com/idp/profile/Shibboleth/Logout',
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
