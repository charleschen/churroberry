import json
import os

from flask import Flask
from flask_ask import Ask, statement
from wakeonlan import wol
import requests
import urlparse

app = Flask(__name__)
app.config.update(
    DEBUG=True
)

ask = Ask(app, '/')

device_ip = '192.168.1.200'
mac = 'D8:D4:3C:7A:44:28'

commands_filepath = os.path.join(app.root_path, 'commands.json')
with open(commands_filepath) as commands_file:
    commands = json.loads(commands_file.read())


def command(device_ip, command_name):
    if (command_name == 'power on'):
        wol.send_magic_packet(mac)
        return True

    if "source" in command_name:
        command_name = "input"

    command_data = commands.get(command_name)
    if not command_data:
        return False

    body = """<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body><u:X_SendIRCC xmlns:u="urn:schemas-sony-com:service:IRCC:1"><IRCCCode>%s</IRCCCode></u:X_SendIRCC></s:Body></s:Envelope>""" % command_data["value"]

    url = urlparse.urljoin('http://%s' % device_ip, 'sony/IRCC')
    resp = requests.post(url, data=body, headers={'Content-Type': 'text/xml'})

    if resp.status_code != 200:
        return False

    return True


def result_speech(is_successful, action):
    speech_text = "Success" if is_successful else (
        "Sorry we failed at %s" % action)
    return statement(speech_text).simple_card('Hello', speech_text)


def repeat_command(count, action):
    for i in xrange(count):
        command_completed = command(device_ip, action)
        if not command_completed:
            return False

    return True


@ask.intent('CommandTimesIntent')
def command_times_intent(action, count):
    print 'original action:', action, 'count:', count
    action_words = action.split(" ")[1:]
    count = int(count) if count else 1
    action = " ".join(action_words)
    print "action", action_words, "count", count
    for i in xrange(count):
        command_completed = command(device_ip, action)
        if not command_completed:
            return result_speech(False, action)

    return result_speech(True, action)


@ask.intent('CommandIntent')
def command_intent(action):
    print 'action', action
    command_completed = command(device_ip, action)
    return result_speech(command_completed, action)


@ask.intent('SourceIntent')
def source(count):
    count = int(count)
    action = 'input'
    completed = repeat_command(count, action)
    return result_speech(completed, action)


@ask.intent('VolumeIntent')
def volume(direction, count):
    count = int(count)
    action = 'volume %s' % direction
    print "VolumeIntent", action, count
    completed = repeat_command(count, action)
    return result_speech(completed, action)


if __name__ == '__main__':
    app.run()
