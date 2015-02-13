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
import os
from os import path
import requests
import logging
import itertools
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
        error_msg = None
        try:
            log('Refreshing metadata for federation %s ...' %federation, logger, logging.INFO)
            error_msg, data_changed = fetch_metadata_file(federation)
    
            if not error_msg and data_changed:
                log('Updating database ...', logger, logging.INFO)
    
                log('Updating federation ...', logger, logging.DEBUG)
                federation.process_metadata()
    
                log('Updating federation entities ...', logger, logging.DEBUG)
                federation.process_metadata_entities(timestamp = timestamp)
    
                log('Updating federation file ...', logger, logging.DEBUG)
                federation.save(update_fields = ['file'])

        except Exception, errorMessage:
            error_msg = errorMessage

        finally:
            if error_msg:
                log('Sending following error via email: %s' % error_msg, logger, logging.INFO)
                
                mailConfigDict = getattr(settings, "MAIL_CONFIG")
                try:
                    subject = mailConfigDict['refresh_subject'] %federation
                    from_address = mailConfigDict['from_email_address']
                    sendMail(from_address, subject, error_msg)
                except Exception, errorMessage:
                    log('Message could not be posted successfully: %s' %errorMessage, logger, logging.ERROR)
    
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

        if federation.file and federation.file.storage.exists(federation.file):
            federation.file.seek(0)
            original_file_content = federation.file.read()

        if not federation.file.storage.exists(federation.file) or not compare_filecontents(original_file_content, req.content):
            filename = path.basename(parsed_url.path)
            federation.file.save(filename, ContentFile(req.content), save=True)
            data_changed = True
#                 dir_name, file_name = os.path.split(federation.file.name)
#                 purge(os.path.join(dir_name, filename), federation.file)
    
    return (error_msg, data_changed)

def purge(name, the_file):
    
    def del_file(file_name):
        try:
            the_file.storage.delete(file_name)
        except:
            pass
        
    """
    Deletes all old versions of the file except the two most recent ones.
    """
    dir_name, file_name = os.path.split(name)
    file_root, file_ext = os.path.splitext(file_name)
    # If the filename already exists, add an underscore and a number (before
    # the file extension, if one exists) to the filename until the generated
    # filename doesn't exist.
    count = itertools.count(1)
    file_to_delete = None
    while the_file.storage.exists(name):
        if name == the_file.name:
            break
        
        if file_to_delete:
            del_file(file_to_delete)
        
        file_to_delete = name
        
        # file_ext includes the dot.
        name = os.path.join(dir_name, "%s_%s%s" % (file_root, next(count), file_ext))

    return name


def log(message, logger = None, severity = logging.INFO):
    
    if logger:
        logger.log(severity, message)
        
    else:
        print message

if __name__ == '__main__':

    refresh()
