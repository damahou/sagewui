# -*- coding: utf-8 -*

#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

"""nodoctest
Sending mail using Twisted

AUTHOR:
    -- Bobby Moretti
"""
from __future__ import absolute_import
from __future__ import print_function

import sys

from twisted.mail import smtp
from twisted.mail import relaymanager
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


def buildMessage(fromaddr, toaddr, subject, body):
    message = MIMEMultipart()
    message['From'] = fromaddr
    message['To'] = toaddr
    message['Subject'] = subject
    textPart = MIMEBase('text', 'plain')
    textPart.set_payload(body)
    message.attach(textPart)
    return message


def sendComplete(result):
    print("Message sent.")


def handleError(error):
    print("Error", error.getErrorMessage(), file=sys.stderr)


def send_mail(fromaddr, toaddr, subject, body, on_success=sendComplete,
              on_failure=handleError):
    try:
        recpt_domain = toaddr.split('@')[1].encode("ascii")
    except (ValueError, IndexError, UnicodeDecodeError):
        raise ValueError("mal-formed destination address")
    message = buildMessage(fromaddr, toaddr, subject, body)
    messageData = message.as_string(unixfrom=False)

    def on_found_record(mx_rec):
        smtp_server = str(mx_rec.name)
        sending = smtp.sendmail(smtp_server, fromaddr, [toaddr], messageData)
        sending.addCallback(on_success).addErrback(on_failure)

    relaymanager.MXCalculator().getMX(recpt_domain).addCallback(
        on_found_record)
