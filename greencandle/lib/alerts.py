#pylint: disable=no-member
"""
Functions for sending alerts
"""

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from str2bool import str2bool
from greencandle.lib import config
from greencandle.lib.common import (AttributeDict, format_usd, get_tv_link, get_trade_link,
                                    list_to_dict, get_be_services)

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

def send_slack_message(channel, message, emoji=None, icon=None, name=None):
    """
    Send notification using slack api
    """
    if not icon:
        icon = ":{}:".format(config.main.trade_direction) if emoji else ":robot_face:"

    if not str2bool(config.slack.slack_active):
        return
    name = name if name else config.main.name
    payload = {"username": name,
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
    valid_keys = ["channel", "event", "pair", "action", "price", "perc", "usd_profit", "quote",
                  "open_time", "close_time"]
    kwargs = AttributeDict(kwargs)
    for key in valid_keys:
        if key not in kwargs:
            kwargs[key] = "N/A"
    try:
        kwargs['price'] = str(kwargs['price']).rstrip("0")
        kwargs['perc'] = "%.4f" % (kwargs['perc'])
        commission = 0.2
        kwargs['net_perc'] = "%.4f" % float(float(kwargs['perc']) - float(commission)) + "%"
        kwargs['net_profit'] = format_usd(float(kwargs['usd_profit']) - ((float(kwargs.usd_quote)
                                                                          /100) * 0.2))
        kwargs['usd_profit'] = format_usd(kwargs['usd_profit'])
        kwargs['perc'] = str(kwargs['perc']) + "%"
        kwargs['quote'] = "%.4f" % (kwargs['quote'])
        kwargs['usd_quote'] = format_usd(kwargs['usd_quote'])

    except TypeError:
        kwargs['net_perc'] = 'N/A'
        kwargs['net_profit'] = 'N/A'
        kwargs['usd_quote'] = format_usd(kwargs['usd_quote'])

    if not str2bool(config.slack.slack_active):
        return
    if kwargs.action == 'OPEN':
        color = '#00fc22'
        services = list_to_dict(get_be_services(config.main.base_env),
                                reverse=False, str_filter='-be-')
        trade_direction = "{}-{}".format(config.main.name, config.main.trade_direction) if not \
                config.main.name.endswith(config.main.trade_direction) else config.main.name
        try:
            short_name = services[trade_direction]

            link = get_trade_link(kwargs.pair, short_name, 'close', 'close_now',
                                  config.web.nginx_port)
        except KeyError:
            link = "API - no link"
        close_string = "• Close: {0}\n".format(link)
        quote_string = "• Quote in: %.4f\n" % float(kwargs.quote)
        time_string = "• Open_time: %s " % kwargs.open_time
    elif kwargs.action == 'CLOSE':
        color = '#fc0303' # red
        close_string = ""
        quote_string = "• Quote out: %.4f\n" % float(kwargs.quote)
        opent = datetime.strptime(str(kwargs.open_time), "%Y-%m-%d %H:%M:%S")
        closet = datetime.strptime(str(kwargs.close_time), "%Y-%m-%d %H:%M:%S")
        delta = str(closet-opent)
        time_string = "• Open_time: %s\n• Close_time: %s\n• Trade time: %s\n" % (kwargs.open_time,
                                                                                 kwargs.close_time,
                                                                                 delta)
    else:
        color = '#ff7f00'
        close_string = ""
        quote_string = ""
        time_string = ""

    icon = ":{}:".format(config.main.trade_direction)

    block = {
        "username": kwargs.event,
        "icon_emoji": "{}".format(icon),
        "channel": config.slack[kwargs.channel],
        "attachments":[
            {"color":"{}".format(color),
             "icon_emoji": "{}".format(icon),
             "fields":[
                 {"value": ("• Pair: {}\n"
                            "• Price: {}\n"
                            "• name/direction: {}/{}\n"
                            "• Percentage: {}\n"
                            "• usd_profit: {}\n"
                            "{}"
                            "{}"
                            "• USD quote: {}\n"
                            "• Net perc: {}\n"
                            "• Net usd_profit: {}\n"
                            "{}" .format(get_tv_link(kwargs.pair, config.main.interval),
                                         kwargs.price,
                                         config.main.name,
                                         config.main.trade_direction,
                                         kwargs.perc,
                                         kwargs.usd_profit,
                                         close_string,
                                         quote_string,
                                         kwargs.usd_quote,
                                         kwargs.net_perc,
                                         kwargs.net_profit,
                                         time_string
                                         )),
                  "short":"false"
                 }]}]}

    webhook = config.slack["url"]
    requests.post(webhook, data=json.dumps(block), headers={'Content-Type': 'application/json'})
