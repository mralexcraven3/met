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

import hashlib, smtplib
from email.mime.text import MIMEText
from django.conf import settings

def compare_filecontents(a, b):
    if a is None:
        return b is None
    if b is None:
        return a is None

    md5_a = hashlib.md5(a).hexdigest()
    md5_b = hashlib.md5(b).hexdigest()
    return md5_a == md5_b

def _connect_to_smtp(server, port=25, login_type=None, username=None, password=None):
    smtpSend = smtplib.SMTP(server, port)
    smtpSend.ehlo()

    if smtpSend.has_extn('STARTTLS'):
        smtpSend.starttls()
        smtpSend.ehlo()

    if username and password:
        try:
            if login_type:
                smtpSend.esmtp_features['auth'] = login_type
            smtpSend.login(username, password)
        except Exception, errorMessage:
            print('Error occurred while trying to login to the email server with user %s: %s' % (username, errorMessage))
            raise

    return smtpSend

def send_mail(from_email_address, subject, message):
    mailConfigDict = getattr(settings, "MAIL_CONFIG")
    server = mailConfigDict['email_server']
    smtpSend = None

    if server is None:
        return
    
    smtpSend = _connect_to_smtp(server, mailConfigDict['email_server_port'], mailConfigDict['login_type'], mailConfigDict['username'], mailConfigDict['password'])
        
    try:
        message = MIMEText(message.encode("utf-8"), "plain", _charset = "UTF-8")
        message['From'] = from_email_address
        message['To'] = ",".join(mailConfigDict['to_email_address'])
        message['Subject'] = subject
            
        smtpSend.sendmail(
            from_email_address, 
            mailConfigDict['to_email_address'],
            message.as_string()
        )
    except Exception, errorMessage:
        print('Error occurred while trying to send an email to %s: %s' % (mailConfigDict['to_email_address'], errorMessage))
        raise
    finally:
        if smtpSend:
            smtpSend.quit()
