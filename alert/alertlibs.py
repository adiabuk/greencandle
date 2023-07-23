"""
Functions and classes for audio and visual alert
"""

from configparser import ConfigParser
import boto3
import serial
from gtts import gTTS

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

def create_google_voice(text, filename):
    """
    Create synthesized voice using Google and save as mp3
    """
    language = 'en'
    myobj = gTTS(text=text, lang=language, slow=False)
    myobj.save(filename)

def lights(port='/dev/ttyACM0', baud=19200):
    """
    Open serial port to activate lights program
    """
    ser = serial.Serial(port, baud)
    ser.close()
    ser.open()


def create_polly_voice(text, filename):
    """
    Create synthesized voice using Amazon polly and save as mp3
    """
    config = get_config()
    polly_client = boto3.Session(
        aws_access_key_id=config.main.access_key,
        aws_secret_access_key=config.main.secret_key,
        region_name='eu-west-1').client('polly')
    response = polly_client.synthesize_speech(VoiceId='Emma',
                                              OutputFormat='mp3',
                                              SampleRate='24000',
                                              Engine="neural",
                                              Text=text)
    with open (filename, 'wb') as file:
        file.write(response['AudioStream'].read())
