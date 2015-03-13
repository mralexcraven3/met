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
Created on Sep 19, 2013

@author: tamim
'''
import sys, os
import logging.config
from optparse import OptionParser

current_directory = os.path.join(os.path.dirname(__file__), '..')
activate_this = os.path.join(current_directory, '..', 'met-venv/bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.append(current_directory)
sys.path.append(os.path.join(current_directory, 'met'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'met.settings'

import django
from met.metadataparser.refresh_metadata import refresh

django.setup()

class RefreshMetaData:
    def process(self, options):
        fed_name = options.fed_name
        force_refresh = options.force_refresh
        
        logger = None
        if options.log:
            logging.config.fileConfig(options.log)
            logger = logging.getLogger("Refresh")
    
        refresh(fed_name, force_refresh, logger)


def commandlineCall(argv, ConvertClass=RefreshMetaData):
    optParser = OptionParser()
    optParser.set_usage("refresh [--federation <fed_name>] [--log  <file>] [--force-refresh]")
    
    optParser.add_option(
        "-l",
        "--log",
        type="string",
        dest="log",
        help="The logger configuration file",
        default=None,
        metavar="LOG")

    optParser.add_option(
        "-f",
        "--federation",
        type="string",
        dest="fed_name",
        help="The federation to be updated (None for anyone)",
        default=None,
        metavar="FED")

    optParser.add_option(
        "-r",
        "--force-refresh",
        action="store_true",
        dest="force_refresh",
        help="Force refresh of metadata information (even if file has not changed)",
        metavar="REF")

    (options, args) = optParser.parse_args()
    
    errorMessage = ""
    
    if options.log and not os.path.exists(options.log):
        errorMessage = "File '%s' does not exist." % options.log
    
    if errorMessage:
        print errorMessage
        print optParser.get_usage()
        exit (1)
    
    objConvert = ConvertClass()
    objConvert.process(options)


if __name__ == '__main__':
    commandlineCall(sys.argv)
