import sys, os
import logging.config

current_directory = os.path.join(os.path.dirname(__file__), '..')
activate_this = os.path.join(current_directory, '..', 'met-venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(current_directory)
sys.path.append(os.path.join(current_directory, 'met'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'met.settings'

import django
django.setup()

from django.conf import settings
from met.metadataparser.utils import sendMail

mailConfigDict = getattr(settings, "MAIL_CONFIG")

m_subj = 'Email test'
m_message = 'Body of the test email'

sendMail(mailConfigDict['from_email_address'], m_subj, m_message)
