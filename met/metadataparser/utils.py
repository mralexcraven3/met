#################################################################
# MET v2 Metadate Explorer Tool
#
# This Software is Open Source. See License: https://github.com/TERENA/met/blob/master/LICENSE.md
# Copyright (c) 2012, TERENA All rights reserved.
#
# This Software is based on MET v1 developed for TERENA by Yaco Sistemas, http://www.yaco.es/
# MET v2 was developed for TERENA by Tamim Ziai, DAASI International GmbH, http://www.daasi.de
#########################################################################################

import hashlib, smtplib
from email.mime.text import MIMEText
from django.conf import settings

def compare_filecontents(a, b):
    md5_a = hashlib.md5(a).hexdigest()
    md5_b = hashlib.md5(b).hexdigest()
    return (md5_a == md5_b)

def sendMail(from_email_address, subject, message):
    mailConfigDict = getattr(settings, "MAIL_CONFIG")
    smtpSend = None

    if mailConfigDict['email_server'] is None:
        return
    
    try:
        if mailConfigDict['email_server_port']:
            smtpSend = smtplib.SMTP(mailConfigDict['email_server'], int(mailConfigDict['email_server_port']))
        else:
            smtpSend = smtplib.SMTP(mailConfigDict['email_server'])

        smtpSend.ehlo()

        if smtpSend.has_extn('STARTTLS'):
            smtpSend.starttls()
            smtpSend.ehlo()

        if mailConfigDict['username'] and mailConfigDict['password']:
            try:
                if mailConfigDict['login_type']:
                    smtpSend.esmtp_features['auth'] = mailConfigDict['login_type']
                smtpSend.login(mailConfigDict['username'], mailConfigDict['password'])
            except Exception, errorMessage:
                print('Error occurred while trying to login to the email server with user %s: %s' % (mailConfigDict['username'], errorMessage))
                raise
        
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
    
    except Exception, errorMessage:
        print('Error occurred while trying to connect to the email server %s with port %s: %s' % (mailConfigDict['email_server'], mailConfigDict['email_server_port'], errorMessage))
        raise
    
    finally:
        try:
            if smtpSend:
                smtpSend.quit()
        except Exception, errorMessage:
            print('Error occurred while trying to quit email: %s' % (errorMessage))
