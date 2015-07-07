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

from lxml import etree

from django.core.files.base import ContentFile
from django.conf import settings

from pyff.mdrepo import MDRepository
from pyff.pipes import Plumbing

from met.metadataparser.utils import compare_filecontents, send_mail
from met.metadataparser.models import Federation

if settings.PROFILE:
    from silk.profiling.profiler import silk_profile as profile
else:
    from met.metadataparser.templatetags.decorators import noop_decorator as profile

def _send_message_via_email(error_msg, federation, logger=None):
    mailConfigDict = getattr(settings, "MAIL_CONFIG")
    try:
        subject = mailConfigDict['refresh_subject'] % federation
        from_address = mailConfigDict['from_email_address']
        send_mail(from_address, subject, '%s' % error_msg)
    except Exception, errorMessage:
        log('Message could not be posted successfully: %s' % errorMessage, logger, logging.ERROR)

def _fetch_new_metadata_file(federation):
    try:
        changed = federation.fetch_metadata_file(federation.slug)
        return None, changed
    except Exception, errorMessage:
        return "%s" % errorMessage, False

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
            error_msg, data_changed = _fetch_new_metadata_file(federation)
    
            if not error_msg and (force_refresh or data_changed):
                log('Updating database ...', logger, logging.INFO)
    
                log('Updating federation ...', logger, logging.DEBUG)
                federation.process_metadata()
    
                log('Updating federation entities ...', logger, logging.DEBUG)
                removed, updated = federation.process_metadata_entities(timestamp=timestamp)
                log('Removed %s old entities and updated %s entities.' % (removed, updated), logger, logging.INFO)
    
                log('Updating federation file ...', logger, logging.DEBUG)
                federation.save(update_fields=['file'])

            log('Updating federation statistics ...', logger, logging.DEBUG)
            federation.compute_new_stats(timestamp=timestamp)

        finally:
            if error_msg:
                log('Sending following error via email: %s' % error_msg, logger, logging.INFO)
                _send_message_via_email(error_msg, federation, logger)
    
    log('Refreshing metadata terminated.', logger, logging.INFO)

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

def log(message, logger=None, severity=logging.INFO):
    if logger:
        logger.log(severity, message)
    else:
        print(message)

