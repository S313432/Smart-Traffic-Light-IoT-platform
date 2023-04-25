from MyMQTT import *
import time
import datetime
import json
import requests
from gpiozero import MotionSensor
import signal
import threading

import urllib.request
import requests
import threading
import json

import random


class PresenceSensor:
    def __init__(self, presence_info, service_catalog_info):
        # Retrieve broker info from service catalog
        self.service_catalog_info = json.load(open(service_catalog_info))
        request_string = 'http://' + self.service_catalog_info["ip_address_service"] + ':' \
                         + self.service_catalog_info["ip_port_service"] + '/broker'
        r = requests.get(request_string)
        rjson = json.loads(r.text)
        self.broker = rjson["broker"]
        self.port = rjson["broker_port"]
        # Retrieve resource catalog info from service catalog
        request_string = 'http://' + self.service_catalog_info["ip_address_service"] + ':' \
                         + self.service_catalog_info["ip_port_service"] + '/one_res_cat'
        r = requests.get(request_string)
        self.rc = json.loads(r.text)
        # Details about sensor
        self.presence_info = presence_info
        info = json.load(open(self.presence_info))
        self.topic = info["servicesDetails"][0]["topic"]
        self.clientID = info["ID"]
        self.client = MyMQTT(self.clientID, self.broker, self.port, None)
        self.pir = MotionSensor(27)
        # Thingspeak details
        self.base_url = info["Thingspeak"]["base_url"]
        self.key = info["Thingspeak"]["key"]
        self.url_read = info["Thingspeak"]["url_read"]

    def register(self):
        request_string = 'http://' + self.rc["ip_address"] + ':' + self.rc["ip_port"] + '/registerResource'
        data = json.load(open(self.presence_info))
        try:
            r = requests.put(request_string, json.dumps(data, indent=4))
            print(f'Response: {r.text}')
        except:
            print("An error occurred during registration")

    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def motion_callback(self):
        msg = {
            "bn": self.clientID,
            "e": {
                "n": "motion",
                "u": "Boolean",
                "t": time.time(),
                "v": True
            }
        }
        self.client.myPublish(self.topic, msg)
        self.thingspeak_post()
        print("published\n" + json.dumps(msg))

    def thingspeak_post(self):
        val = 1 # Value 1 for cars
        URl = self.base_url  #This is unchangeble
        KEY = self.key  #This is the write key API of your channels

    	#field one corresponds to the first graph, field2 to the second ... 
        HEADER = '&field1={}'.format(val)
        
        NEW_URL = URl+KEY+HEADER
        URL_read = self.url_read
        print('A car has been detected. Thingspeak link: \n' + URL_read)
        data = urllib.request.urlopen(NEW_URL)
        print(data)
        
    def background(self):
        while True:
            self.register()
            time.sleep(10)

    def foreground(self):
        self.start()

if __name__ == '__main__':
    pres = PresenceSensor('presence_info.json', 'service_catalog_info.json')

    b = threading.Thread(name='background', target=pres.background)
    f = threading.Thread(name='foreground', target=pres.foreground)

    b.start()
    f.start()

    try:
        pres.pir.when_motion = pres.motion_callback

        #pause()

    finally:
        pres.stop()
