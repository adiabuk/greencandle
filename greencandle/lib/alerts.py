#pylint: disable=no-member
"""
Functions for sending alerts
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import notify_run
from str2bool import str2bool
from . import config
from .timeout import restrict_timeout
from .logger import getLogger, get_decorator

GET_EXCEPTIONS = get_decorator((Exception))

@GET_EXCEPTIONS
def send_gmail_alert(action, pair, price):
    """
    Send email alert using gmail
    """
    if not str2bool(config.email.active):
        return
    logger = getLogger(__name__, config.main.logging_level)
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

def send_push_notif(*args):
    """
    Send push notification via notify.run
    """
    if not str2bool(config.push.active):
        return
    host = config.push.host
    channel = config.push.channel
    title = config.push.title
    text = title + ' ' + ' '.join(str(item) for item in args)
    notify = notify_run.Notify(channel)

    notify.endpoint = 'https://{0}/{1}'.format(host, channel)
    notify.send(text)
