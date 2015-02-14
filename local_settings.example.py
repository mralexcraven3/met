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
