#pylint: disable=no-member,too-many-locals
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
    message = f"{action} alert generated for {pair} at {price}"
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
    if not config.slack[channel]:
        return
    if not str2bool(config.slack.slack_active):
        return
    if not icon:
        icon = f":{config.main.trade_direction}:" if emoji else ":robot_face:"

    name = name if name else config.main.name
    payload = {"username": name,
               "icon_emoji": icon,
               "channel": config.slack[channel],
               "attachments":[
                   {"fields":[
                       {"value": message
                        }]}]}

    webhook = config.slack["url"]
    requests.post(webhook, data=json.dumps(payload), timeout=20,
                  headers={'Content-Type': 'application/json'})

def send_slack_trade(**kwargs):
    """
    Send trade notification in slack
    """
    valid_keys = ["channel", "event", "pair", "action", "price", "perc", "usd_profit", "quote",
                  "open_time", "close_time", "drawup", "drawdown"]
    kwargs = AttributeDict(kwargs)
    for key in valid_keys:
        if key not in kwargs:
            kwargs[key] = "N/A"

    net_perc = f"{kwargs.net_perc:.4f}%" if kwargs['net_perc'] else "N/A"
    net_profit = format_usd(kwargs.usd_net_profit) if kwargs['usd_net_profit'] else "N/A"

    kwargs['price'] = str(kwargs['price']).rstrip("0")
    kwargs['perc'] = f"{float(kwargs['perc']):.4f}" if kwargs['perc'] else None
    kwargs['net_perc'] = net_perc
    kwargs['net_profit'] = net_profit
    kwargs['usd_profit'] = format_usd(kwargs['usd_profit'])
    kwargs['perc'] = str(kwargs['perc']) + "%"
    kwargs['quote'] = f"{float(kwargs['quote']):.4f}"
    kwargs['usd_quote'] = format_usd(kwargs['usd_quote'])

    if not str2bool(config.slack.slack_active):
        return
    if not config.slack[kwargs.channel]:
        return

    if kwargs.action == 'OPEN':
        color = '#00fc22'
        services = list_to_dict(get_be_services(config.main.base_env),
                                reverse=False, str_filter='-be-')
        trade_direction = f"{config.main.name}-{config.main.trade_direction}" if not \
                config.main.name.endswith(config.main.trade_direction) else config.main.name
        try:
            short_name = services[trade_direction]

            link = get_trade_link(kwargs.pair, short_name, 'close', 'close_now',
                                  config.web.nginx_port)
        except KeyError:
            link = "API - no link"
        close_string = f"• Close: {link}\n"
        quote_string = f"• Quote in: {float(kwargs.quote):.4f}\n"
        time_string = f"• Open_time: {kwargs.open_time} "
    elif kwargs.action == 'CLOSE':
        color = '#fc0303' # red
        close_string = ""
        quote_string = f"• Quote out: {float(kwargs.quote):.4f}\n"
        opent = datetime.strptime(str(kwargs.open_time), "%Y-%m-%d %H:%M:%S")
        closet = datetime.strptime(str(kwargs.close_time), "%Y-%m-%d %H:%M:%S")
        delta = str(closet-opent)
        time_string = (f"• Open_time: {kwargs.open_time}\n• Close_time: {kwargs.close_time}\n"
                       f"• Trade time: {delta}\n")
    else:
        color = '#ff7f00'
        close_string = ""
        quote_string = ""
        time_string = ""

    icon = f":{config.main.trade_direction}:"

    block = {
        "username": kwargs.event,
        "icon_emoji": icon,
        "channel": config.slack[kwargs.channel],
        "attachments":[
            {"color":f"{color}",
             "icon_emoji": icon,
             "fields":[
                 {"value": (f'• Pair: {get_tv_link(kwargs.pair, config.main.interval)}\n'
                            f'• Price: {kwargs.price}\n'
                            f'• name/direction: {config.main.name}/{config.main.trade_direction}\n'
                            f'• Percentage: {kwargs.perc}\n'
                            f'• usd_profit: {kwargs.usd_profit}\n'
                            f'{close_string}'
                            f'{quote_string}'
                            f'• USD quote: {kwargs.usd_quote}\n'
                            f'• Net perc: {kwargs.net_perc}\n'
                            f'• Net usd_profit: {kwargs.net_profit}\n'
                            f'• du/dd: {kwargs.drawup}/{kwargs.drawdown}\n'
                            f'{time_string}'),
                  "short":"false"
                 }]}]}

    webhook = config.slack["url"]
    requests.post(webhook, data=json.dumps(block), headers={'Content-Type': 'application/json'},
                  timeout=20)
