#!/usr/bin/env python
#pylint: disable=protected-access,no-else-return,consider-using-with

"""
API module for listening for JSON POST requests and playing audio alerts and activating alert lights
"""

from pathlib import Path
from datetime import datetime, time
import subprocess
from flask import Flask, request, Response
import setproctitle
from alertlibs import create_polly_voice, create_google_voice, lights

APP = Flask(__name__)

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
    if Path('/var/local/drain/alert_drain').is_file():
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

def play(data):
    """
    Play audio beep and spoken text from Amazon Polly or Google
    """
    pair = '.'.join(list(data['pair']))
    text = f"{pair}, {data['text']}"

    if Path('/var/local/google').is_file():
        create_google_voice(text, '/srv/output/speech.mp3')
        red = 'google'
    else:
        create_polly_voice(text, '/srv/output/speech.mp3')
        red = 'polly'

    play_mp3('/srv/output/250ms-silence.mp3')
    play_mp3('/srv/output/com.mp3')
    play_mp3(f'/srv/output/{red}_redalert.mp3')
    play_mp3('/srv/output/speech.mp3')

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
    subprocess.Popen(['mpg123', volume, '-q', path], user="dockeraudio").wait()

def main():
    """
    Main function
    start Flask APP on port 20000
    """
    setproctitle.setproctitle("alert")
    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=False)
if __name__ == "__main__":
    main()
