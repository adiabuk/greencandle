from flask import Flask, request, Response
import boto3
import serial
import subprocess
from configparser import ConfigParser

app = Flask(__name__)

def get_config():
    parser = ConfigParser(allow_no_value=True)
    parser.read("./red-alert.ini")
    x = AttributeDict()
    for section in parser.sections():
        x[section] = AttributeDict(parser._sections[section])
    return x

class AttributeDict(dict):
    """Access dictionary keys like attributes"""
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value
    def __del_attr__(self, attr):
        self.pop(attr, None)

@app.route('/webhook', methods=['POST'])
def respond():
    print(request.json)
    lights()
    play(request.json)
    return Response(status=200)

def lights(port='/dev/ttyACM0', baud=19200):
    ser = serial.Serial(port, baud)
    ser.close()
    ser.open()

def play(data):
    config = get_config()
    polly_client = boto3.Session(
        aws_access_key_id=config.main.access_key,
        aws_secret_access_key=config.main.secret_key,
        region_name='eu-west-1').client('polly')

    pair = '.'.join(list(data['pair']))
    text = 'Red Alert, all hands to battle stations. {} {}'.format(pair, data['text'])
    response = polly_client.synthesize_speech(VoiceId='Emma',
                                              OutputFormat='mp3',
                                              SampleRate='24000',
                                              Engine="neural",
                                              Text = text)
    file = open('speech.mp3', 'wb')
    file.write(response['AudioStream'].read())
    print(text)
    file.close()

    play_mp3('com.mp3')
    play_mp3('speech.mp3')

def play_mp3(path):
    subprocess.Popen(['mpg123', '-q', path]).wait()

def main():
    app.run(debug=True, host='0.0.0.0', port=20000, threaded=True)
if __name__ == "__main__":
    main()
