from MyMQTT import *
import time
import json
import requests
import threading


class LedManager:
    def __init__(self, ledmanager_info, service_catalog_info):
        # Retrieve broker info from service catalog
        self.service_catalog_info = json.load(open(service_catalog_info))
        request_string = 'http://' + self.service_catalog_info["ip_address_service"] + ':' + self.service_catalog_info["ip_port_service"] + '/broker'
        r = requests.get(request_string)
        rjson = json.loads(r.text)
        self.broker = rjson["broker"]
        self.port = rjson["broker_port"]
        # Retrieve resource catalog info from service catalog
        request_string = 'http://' + self.service_catalog_info["ip_address_service"] + ':' + self.service_catalog_info["ip_port_service"] + '/one_res_cat'
        r = requests.get(request_string)
        self.rc = json.loads(r.text)
        # Details about sensor
        self.info = ledmanager_info
        info = json.load(open(self.info))
        for s in info["serviceDetails"]:
            if s["serviceType"]=='MQTT':
                self.topicS = s["topicS"] #topic to which it is subscribed
                self.topicP = s["topicP"] #topic on which it publishes
        self.clientID = info["Name"]
        self.client = MyMQTT(self.clientID, self.broker, self.port, self)

    def register(self):
        request_string = 'http://' + self.rc["ip_address"] + ':' + self.rc["ip_port"] + '/registerResource'
        data = json.load(open(self.info))
        try:
            r = requests.put(request_string, json.dumps(data, indent=4))
            print(f'Response: {r.text}')
        except:
            print("An error occurred during registration")

    # Method to START and SUBSCRIBE
    def start(self):
        self.client.start()
        time.sleep(3)  # Timer of 3 second (to deal with asynchronous)
        self.client.mySubscribe(self.topicS)

    # Method to UNSUBSCRIBE and STOP
    def stop(self):
        self.client.unsubscribe()
        time.sleep(3)
        self.client.stop()

    def notify(self, topic, payload):
        messageReceived = json.loads(payload)
        bn = messageReceived["bn"]
        id = bn.split('_')
        sensorType = id[1]
        trafficLightID = id[2]
        obj = 0
        if messageReceived["e"]["n"] == "button":
            obj = "pedestrian"
        elif messageReceived["e"]["n"] == "motion":
            obj = "car"
        if messageReceived["e"]["v"]:
            if sensorType == "p":
                specific_topic = self.topicP + '/' + trafficLightID
                self.publish(specific_topic, obj)
            elif sensorType == "c":
                self.publish(self.topicP, obj)

    def publish(self, topicP, obj):
        msg = {
            "bn": self.clientID,
            "e": {
                "n": "led",
                "u": "detection",
                "t": time.time(),
                "v": obj
            }
        }
        self.client.myPublish(topicP, msg)
        print("published\n" + json.dumps(msg) + '\nOn topic: ' + f'{topicP}')

    def background(self):
        while True:
            self.register()
            time.sleep(10)

    def foreground(self):
        self.start()


if __name__ == '__main__':
    ledMan = LedManager('ledmanagerA_info.json', 'service_catalog_info.json')

    b = threading.Thread(name='background', target=ledMan.background)
    f = threading.Thread(name='foreground', target=ledMan.foreground)

    b.start()
    f.start()

    while True:
        time.sleep(3)

    # ledMan.stop()
