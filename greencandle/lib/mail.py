#pylint: disable=wrong-import-position
"""
Functions for sending email alerts
"""

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)
from . import config
from .timeout import restrict_timeout
from .logger import getLogger, get_decorator

GET_EXCEPTIONS = get_decorator((Exception))

@GET_EXCEPTIONS
def send_gmail_alert(action, pair, price):
    """
    Send email alert using gmail
    """
    logger = getLogger()
    email_to = config.email.to
    email_from = config.email['from']
    email_password = config.email.password

    fromaddr = email_from
    toaddr = email_to
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    message = "{0} alert generated for {1} at {2}".format(action, pair, price)
    msg['Subject'] = message

    body = message
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_from, email_password)
    text = msg.as_string()
    logger.info("Sending Email")
    with restrict_timeout(3, name="email alert"):
        server.sendmail(fromaddr, toaddr, text)
    server.quit()
