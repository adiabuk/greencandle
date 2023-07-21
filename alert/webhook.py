#!/usr/bin/env python
#pylint: disable=protected-access,no-else-return,consider-using-with

"""
API module for listening for JSON POST requests and playing audio alerts and activating alert lights
"""

from pathlib import Path
from configparser import ConfigParser
from datetime import datetime, time
import subprocess
import boto3
from flask import Flask, request, Response
import serial
import setproctitle

APP = Flask(__name__)

def get_config():
    """
    Get alerts config
    """
    parser = ConfigParser(allow_no_value=True)
    parser.read("/etc/alert.ini")
    attr_dict = AttributeDict()
    for section in parser.sections():
        attr_dict[section] = AttributeDict(parser._sections[section])
    return attr_dict

class AttributeDict(dict):
    """Access dictionary keys like attributes"""
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value
    def __del_attr__(self, attr):
        self.pop(attr, None)

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Activate lights and pass json to audio function for parsing
    """
    lights()
    print(request.json)
    if Path('/var/local/alert_drain').is_file():
        print("Skipping audio alert")
    else:
        print("playing audio")
        play(request.json)
    return Response(status=200)

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def lights(port='/dev/ttyACM0', baud=19200):
    """
    Open serial port to activate lights program
    """
    ser = serial.Serial(port, baud)
    ser.close()
    ser.open()

def play(data):
    """
    Play audio beep and spoken text from Amazon Polly
    """
    config = get_config()
    polly_client = boto3.Session(
        aws_access_key_id=config.main.access_key,
        aws_secret_access_key=config.main.secret_key,
        region_name='eu-west-1').client('polly')

    pair = '.'.join(list(data['pair']))
    text = f"Red Alert, all hands to battle stations. {pair} {data['text']}"
    response = polly_client.synthesize_speech(VoiceId='Emma',
                                              OutputFormat='mp3',
                                              SampleRate='24000',
                                              Engine="neural",
                                              Text=text)
    with open ('speech.mp3', 'wb') as file:
        file.write(response['AudioStream'].read())
    play_mp3('250ms-silence.mp3')
    play_mp3('com.mp3')
    play_mp3('speech.mp3')

def in_between(now, start, end):
    """
    Check if time is beteen start and end time (nighttime hours)
    """
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end

def get_time():
    """
    Return day/night string depending on time of day
    """
    return "night" if in_between(datetime.now().time(), time(20), time(9)) else "day"

def play_mp3(path):
    """
    Play beep and downloaded synthesized audio
    Use 5% volume for out-of-hours alerts, otherwise 10% volume
    """
    volume = '-g100'
    subprocess.Popen(['mpg123', volume, '-q', path]).wait()

def main():
    """
    Main function
    start Flask APP on port 20000
    """
    setproctitle.setproctitle("alert")
    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=False)
if __name__ == "__main__":
    main()
