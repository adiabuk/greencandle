#pylint: disable=no-member
"""
Functions for sending alerts
"""

import re
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import notify_run
from str2bool import str2bool
from . import config
from .common import AttributeDict, sub_perc, format_usd, get_tv_link, get_trade_link


def send_gmail_alert(action, pair, price):
    """
    Send email alert using gmail
    """
    if not str2bool(config.email.email_active):
        return
    email_to = config.email.email_to
    email_from = config.email.email_from
    email_password = config.email.email_password

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
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def send_push_notif(*args):
    """
    Send push notification via notify.run
    """
    if not str2bool(config.push.push_active):
        return
    host = config.push.push_host
    channel = config.push.push_channel
    host = "unk" if 'HOST' not in os.environ else os.environ['HOST']

    title = "{}_{}".format(host, config.main.name)
    text = title + ' ' + ' '.join(str(item) for item in args)
    notify = notify_run.Notify(channel)

    notify.endpoint = 'https://{0}/{1}'.format(host, channel)
    notify.send(text)

def send_slack_message(channel, message, emoji=None, icon=None):
    """
    Send notification using slack api
    """
    if not icon:
        icon = ":{}:".format(config.main.trade_direction) if emoji else ":robot_face:"

    if not str2bool(config.slack.slack_active):
        return
    payload = {"username": config.main.name,
               "icon_emoji": icon,
               "channel": config.slack[channel],
               "attachments":[
                   {"fields":[
                       {"value": message
                        }]}]}

    webhook = config.slack["url"]
    requests.post(webhook, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

def send_slack_trade(**kwargs):
    """
    Send trade notification in slack
    """
    valid_keys = ["channel", "event", "pair", "action", "price", "perc", "usd_profit"]
    kwargs = AttributeDict(kwargs)
    for key in valid_keys:
        if key not in kwargs:
            kwargs[key] = "N/A"
    try:
        kwargs['price'] = str(kwargs['price']).rstrip("0")
        kwargs['perc'] = "%.4f" % (kwargs['perc'])
        commission = 0.2
        kwargs['net_perc'] = "%.4f" % float(float(kwargs['perc']) - float(commission)) + "%"
        kwargs['net_profit'] = format_usd(sub_perc(float(commission), float(kwargs['usd_profit'])))
        kwargs['usd_profit'] = format_usd(kwargs['usd_profit'])
        kwargs['perc'] = str(kwargs['perc']) + "%"

    except TypeError:
        kwargs['net_perc'] = 'N/A'
        kwargs['net_profit'] = 'N/A'


    if not str2bool(config.slack.slack_active):
        return
    title = config.main.name
    if kwargs.action == 'OPEN':
        color = '#00fc22'
        strat = re.findall(r"-([\s\S]*)$", config.main.name)[0].replace('api-', '')
        close_string = "• Close: {0}\n".format(get_trade_link(kwargs.pair, strat,
                                                              'close', 'close now'))
    elif kwargs.action == 'CLOSE':
        color = '#fc0303' # red
        close_string = ""
    else:
        color = '#ff7f00'
        close_string = ""
    icon = ":{}:".format(config.main.trade_direction)

    block = {
        "username": kwargs.event,
        "icon_emoji": "{}".format(icon),
        "channel": config.slack[kwargs.channel],
        "attachments":[
            {"color":"{}".format(color),
             "icon_emoji": "{}".format(icon),
             "fields":[
                 {"value": ("• Pair: {0}\n"
                            "• Price: {1}\n"
                            "• title: {2}\n"
                            "• Percentage: {3}\n"
                            "• usd_profit: {4}\n"
                            "• Net perc: {5}\n"
                            "• Net usd_profit: {6}\n"
                            "{7}"
                            "\n\n".format(get_tv_link(kwargs.pair),
                                          kwargs.price,
                                          title,
                                          kwargs.perc,
                                          kwargs.usd_profit,
                                          kwargs.net_perc,
                                          kwargs.net_profit,
                                          close_string
                                          )),
                  "short":"false"
                 }]}]}

    webhook = config.slack["url"]
    requests.post(webhook, data=json.dumps(block), headers={'Content-Type': 'application/json'})
