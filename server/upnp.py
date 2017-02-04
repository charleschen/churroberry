import re
import time

from simpletr64.devicetr64 import ET
import simpletr64
import requests
import urlparse

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convert(name):
    s1 = first_cap_re.sub(r'\1 \2', name)
    return all_cap_re.sub(r'\1 \2', s1).lower()


def search_device(manufactor, load_scpd=False):
    # something wrong with discover, can't consistently give back device
    tries = 4
    while(tries > 0):
        for r in simpletr64.Discover.discover():
            device = simpletr64.DeviceTR64.createFromURL(r.location)
            try:
                device.loadDeviceDefinitions(r.location)
            except ValueError:
                pass

            print device.deviceInformations
            if manufactor in device.deviceInformations.get('manufacturer').lower():
                tries = 0
                break

        tries -= 1

    if load_scpd:
        for k in device.deviceServiceDefinitions.keys():
            device.loadSCPD(k)

    return device


def get_codes(device_ip):
    url = urlparse.urljoin('http://%s' % device_ip, 'sony/system')
    data = {
        "method": "getRemoteControllerInfo",
        "params": [],
        "id": 10,
        "version": "1.0"
    }
    resp = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
    if resp.status_code != 200:
        raise Exception('ruh oh')

    commands = {}
    for command_data in resp.json()['result'][1]:
        commands[convert(command_data['name'])] = command_data
    return commands
