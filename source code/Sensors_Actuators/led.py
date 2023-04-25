from MyMQTT import *
import time
import datetime
import json
import requests
from gpiozero import LED
import Adafruit_DHT
import threading
import urllib.request


class LEDLights:
    def __init__(self, led_info, service_catalog_info):
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
        self.led_info = led_info
        info = json.load(open(self.led_info))
        self.topic = info["servicesDetails"][0]["topic"] # topic dedicated to led
        self.topic_zone = info["servicesDetails"][0]["topic_zone"] # topic common to all zone
        self.clientID = info["Name"]
        self.timer = info["timer"]  # Timer
        self.cycle = info["duty_cycle"]
        self.client = MyMQTT(self.clientID, self.broker, self.port, self)
        self.car_led1 = LED(24)  # Car green light
        self.car_led2 = LED(22)  # Car red light
        self.ped_led1 = LED(23)  # Pedestrian green light
        self.ped_led2 = LED(18)  # Pedestrian red light
        # LED functioning control sensor
        self.led_ctrl = Adafruit_DHT.DHT11  # Temperature & humidity sensor
        self.led_ctrl_pin = 25
        # Thingspeak details
        self.base_url = info["Thingspeak"]["base_url"]
        self.key = info["Thingspeak"]["key"]
        self.url_read = info["Thingspeak"]["url_read"]

    def register(self):
        # Check temperature is under emergency threshold
        humidity, temperature = Adafruit_DHT.read(self.led_ctrl, self.led_ctrl_pin)
        if humidity is not None and temperature is not None:
            print(f'Temperature of the traffic light = {temperature}')
            if temperature > 80:
                # Overheated traffic light: malfunctioning detected
                data = json.load(open(self.led_info))
                data["status"] = "Malfunctioning"
                json.dump(data, open(self.led_info, "w"))
                print("Traffic light overheated, malfunctioning detected.")
            else:
                # Temperature under control: traffic light correctly functioning
                data = json.load(open(self.led_info))
                data["status"] = "OK"
                json.dump(data, open(self.led_info, "w"))
            # Post temperature data on Thingspeak
            self.thingspeak_post(temperature)
            # Send registration request to Resource Catalog
            request_string = 'http://' + self.rc["ip_address"] + ':' + self.rc["ip_port"] + '/registerResource'
            try:
                r = requests.put(request_string, json.dumps(data, indent=4))
                print(f'Response: {r.text}')
            except:
                print("An error occurred during registration")
        else:
            print('LED functioning sensor failure. Check wiring.')

    def start(self):
        self.client.start()
        time.sleep(3)
        self.client.mySubscribe(self.topic)
        self.client.mySubscribe(self.topic_zone)

    def stop(self):
        self.client.unsubscribe()
        time.sleep(3)
        self.client.stop()

    def notify(self, topic, payload):
        payload = json.loads(payload)
        print(f'Message received: {payload}\n Topic: {topic}')
        if topic == self.topic_zone:
            # payload["e"]["v"] == 'car'
            self.car_led1.on()
            self.car_led2.off()
            self.ped_led1.off()
            self.ped_led2.on()
        elif topic == self.topic:
            # payload["e"]["v"] == 'pedestrian'
            self.car_led1.off()
            self.car_led2.on()
            self.ped_led1.on()
            self.ped_led2.off()
        self.led_cycle()

    def led_cycle(self):
        # Start regular functioning cycle
        timer = self.timer
        while timer > 0:
            timer -= self.cycle
            time.sleep(self.cycle)
            if self.car_led1.is_lit:
                self.car_led1.off()
                self.car_led2.on()
                self.ped_led1.on()
                self.ped_led2.off()
            else:
                self.car_led1.on()
                self.car_led2.off()
                self.ped_led1.off()
                self.ped_led2.on()
        # Turn off lights for energy saving
        self.car_led1.off()
        self.car_led2.off()
        self.ped_led1.off()
        self.ped_led2.off()
        print('Lights turned off for energy saving')
        
    def thingspeak_post(self, val):
        URL = self.base_url #This is unchangeble
        KEY = self.key #This is the write key API of your channels

    	#field one corresponds to the first graph, field2 to the second ... 
        HEADER='&field2={}'.format(val)
        
        NEW_URL = URL+KEY+HEADER
        URL_read = self.url_read
        print("Temperature data have been sent to Thingspeak\n" + URL_read)
        data = urllib.request.urlopen(NEW_URL)
        print(data)
        
    def background(self):
        while True:
            self.register()
            time.sleep(10)

    def foreground(self):
        self.start()


if __name__ == '__main__':
    led = LEDLights('led_info.json', 'service_catalog_info.json')

    b = threading.Thread(name='background', target=led.background)
    f = threading.Thread(name='foreground', target=led.foreground)

    b.start()
    f.start()

    while True:
        time.sleep(1)

    # led.stop()
