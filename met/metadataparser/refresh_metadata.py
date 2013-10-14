#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
#########################################################################################

'''
Created on Sep 18, 2013

@author: tamim
'''
from os import path
import requests
import logging
from urlparse import urlsplit
from django.utils import timezone

from django.core.files.base import ContentFile
from django.conf import settings

from met.metadataparser.utils import compare_filecontents, sendMail
from met.metadataparser.models import Federation

def refresh(logger = None):
    
    log('Starting refreshing metadata ...', logger, logging.INFO)

    federations = Federation.objects.all()
    # All entries must have the same time stamp 
    timestamp = timezone.now()
    
    for federation in federations:
        
        log('Refreshing metadata for federation %s ...' %federation, logger, logging.INFO)
        error_msg, data_changed = fetch_metadata_file(federation)

        if error_msg:
            mailConfigDict = getattr(settings, "MAIL_CONFIG")
            try:
                subject = mailConfigDict['refresh_subject'] %federation
                from_address = mailConfigDict['from_email_address']
                sendMail(from_address, subject, error_msg)
            except Exception, errorMessage:
                log('Message could not be posted successfully: %s' %errorMessage, logger, logging.ERROR)

        elif data_changed:
            log('Updating database ...', logger, logging.INFO)

            federation.process_metadata()
            federation.process_metadata_entities(timestamp = timestamp)
            federation.save(update_fields = ['file'])

    log('Refreshing metadata terminated.', logger, logging.INFO)

def fetch_metadata_file(federation):

    req = requests.get(federation.file_url)
    error_msg = ''
    data_changed = False

    if req.ok:
        if 400 <= req.status_code < 500:
            error_msg = '%s Client Error: %s' % (req.status_code, req.reason)

        elif 500 <= req.status_code < 600:
            error_msg = '%s Server Error: %s' % (req.status_code, req.reason)

    else:
        error_msg = 'Getting metadata from %s failed.' % federation.file_url
    
    if not error_msg:
        parsed_url = urlsplit(federation.file_url)

        if federation.file:
            federation.file.seek(0)
            original_file_content = federation.file.read()

            if not compare_filecontents(original_file_content, req.content):
                filename = path.basename(parsed_url.path)
                federation.file.save(filename, ContentFile(req.content), save=False)
                data_changed = True
    
    return (error_msg, data_changed)

def log(message, logger = None, severity = logging.INFO):
    
    if logger:
        logger.log(severity, message)
        
    else:
        print message

if __name__ == '__main__':

    refresh()
