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

if settings.PROFILE:
    from silk.profiling.profiler import silk_profile as profile
else:
    from met.metadataparser.templatetags.decorators import noop_decorator as profile

def refresh(fed_name=None, force_refresh=False, logger=None):
    log('Starting refreshing metadata ...', logger, logging.INFO)

    federations = Federation.objects.all()
    federations.prefetch_related('etypes', 'federations')

    # All entries must have the same time stamp 
    timestamp = timezone.now()
    
    for federation in federations:
        if fed_name and federation.slug != fed_name:
            continue

        error_msg = None
        try:
            log('Refreshing metadata for federation %s ...'  % federation, logger, logging.INFO)
            error_msg, data_changed = fetch_metadata_file(federation, logger)
    
            if not error_msg and (force_refresh or data_changed):
                log('Updating database ...', logger, logging.INFO)
    
                log('Updating federation ...', logger, logging.DEBUG)
                federation.process_metadata()
    
                log('Updating federation entities ...', logger, logging.DEBUG)
                removed, updated = federation.process_metadata_entities(timestamp=timestamp)
                log('Removed %s old entities and updated %s entities.' % (removed, updated), logger, logging.INFO)
    
                log('Updating federation file ...', logger, logging.DEBUG)
                federation.save(update_fields=['file'])

        except Exception, errorMessage:
            error_msg = errorMessage

        finally:
            if error_msg:
                log('Sending following error via email: %s' % error_msg, logger, logging.INFO)
                
                mailConfigDict = getattr(settings, "MAIL_CONFIG")
                try:
                    subject = mailConfigDict['refresh_subject'] %federation
                    from_address = mailConfigDict['from_email_address']
                    sendMail(from_address, subject, '%s' % error_msg)
                except Exception, errorMessage:
                    log('Message could not be posted successfully: %s' % errorMessage, logger, logging.ERROR)
    
    log('Refreshing metadata terminated.', logger, logging.INFO)

def fetch_metadata_file(federation, logger=None):
    file_url = federation.file_url
    if not file_url or file_url == '':
        log('Federation has no URL configured.', logger, logging.INFO)
        return ('', False)

    # Timeouts: 10 seconds for connect call, 120 seconds for total download
    req = requests.get(file_url, timeout=(10, 120))
    if req.ok:
        if 400 <= req.status_code < 500:
            return ('%s Client Error: %s' % (req.status_code, req.reason), False)
        elif 500 <= req.status_code < 600:
            return ('%s Server Error: %s' % (req.status_code, req.reason), False)
    else:
        return ('Getting metadata from %s failed.' % federation.file_url, False)
    
    parsed_url = urlsplit(federation.file_url)

    if federation.file and federation.file.storage.exists(federation.file):
        federation.file.seek(0)
        original_file_content = federation.file.read()

    if not federation.file.storage.exists(federation.file) or not compare_filecontents(original_file_content, req.content):
        filename = path.basename("%s-metadata.xml" % federation.slug)
        federation.file.save(filename, ContentFile(req.content), save=True)
        purge(federation.file, logger)
        return ('', True)
    
    return ('', False)

def purge(the_file, logger=None):
    """
    Deletes all old versions of the federation metadata file.
    """
    dir_name, file_name = os.path.split(the_file.name)
    file_root, file_ext = os.path.splitext(file_name)
    file_root = file_root.split('_', 1)[0]

    for fname in the_file.storage.listdir(dir_name)[1]:
        if fname.startswith(file_root) and fname != file_name:
            try:
                log('Deleting old federation file: %s' % fname, logger, logging.DEBUG)
                the_file.storage.delete(os.path.join(dir_name, fname))
            except:
                log('Error while deleting file %s"' % file_name, logger, logging.ERROR)
                pass

def log(message, logger=None, severity=logging.INFO):
    if logger:
        logger.log(severity, message)
    else:
        print message

