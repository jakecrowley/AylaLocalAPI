#!/usr/bin/env python3

import jsonpickle
from AylaAPI import AylaAPI, Device
import logging
import requests
import argparse
import time
import socket
import threading
import paho.mqtt.client as mqtt
import json

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        logging.error("Failed to get local IP address, set it manually with --bind.")
        IP = None
    finally:
        s.close()
    return IP

def send_ping_forever(api: AylaAPI, device: Device):
    while True:
        device.ping()
        time.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    IP = get_ip()
    
    try:    
        with open("config.json", "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Config file not found! Run login.py first.")

    parser = argparse.ArgumentParser()
    
    if IP is None:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, required=True)
    else:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, default=IP)
        
    parser.add_argument("--port", dest='port', help="Port to run the API server on", type=int, default=10275, required=False)
    
    mqtt_required = True if "mqtt" not in config else False
    parser.add_argument("--mqtt-ip", dest='mqtt_ip', help="IP of the MQTT server to connect to.", type=str, default=config.get('mqtt', {}).get('ip'), required=mqtt_required)
    parser.add_argument("--mqtt-port", dest='mqtt_port', help="Port of the MQTT server to connect to.", type=int, default=config.get('mqtt', {}).get('port', 1883), required=False)
    parser.add_argument("--mqtt-user", dest='mqtt_user', help="Username for MQTT server authentication.", type=str, default=config.get('mqtt', {}).get('user'), required=mqtt_required)
    parser.add_argument("--mqtt-pass", dest='mqtt_pass', help="Password for MQTT server authentication.", type=str, default=config.get('mqtt', {}).get('pass'), required=mqtt_required)
        
    args = parser.parse_args()
    
    if mqtt_required:
        config["mqtt"] = {
            'ip': args.mqtt_ip,
            'port': args.mqtt_port,
            'user': args.mqtt_user,
            'pass': args.mqtt_pass,
        }
        with open("config.json", "w") as f:
            f.write(jsonpickle.encode(config, indent=4, unpicklable=False))

    api = AylaAPI(args.bind, args.port)

    while api.server is None:
        time.sleep(0.25)

    for device in api.devices:
        threading.Thread(target=send_ping_forever, args=[api, device]).start()
    
    def mqtt_on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
        logging.info(f"Connected to MQTT server with result code {reason_code}")

        for device in api.devices:
            for dp in device.properties:
                property = dp.property
                if property['direction'] != "input" or property['base_type'] != "boolean":
                    continue

                mqtt_config = {
                    "device": {
                        "connections": [["ip", device.lan_ip]],
                        "manufacturer": "APC",
                        "model": "SurgeArrest",
                        "serial_number": device.dsn,
                        "name": device.name,
                    },
                    "name": property["display_name"],
                    "device_class": "outlet",
                    "payload_on": "on",
                    "payload_off": "off",
                    "command_topic": f"homeassistant/switch/{device.dsn}-{property['name']}/set",
                    "state_topic": f"homeassistant/switch/{device.dsn}-{property['name']}/status",
                    "value_template": "{{ value_json.status }}",
                    "unique_id": f"{device.dsn}-{property['name']}",
                }

                client.publish(f"homeassistant/switch/{device.dsn}-{property['name']}/config", payload=json.dumps(mqtt_config), retain=True)

                client.subscribe(f"homeassistant/switch/{device.dsn}-{property['name']}/set")

    def mqtt_on_message(client: mqtt.Client, userdata, msg):
        dev_info = msg.topic.split('/')[2].split('-')
        device = api.get_device_by_sn(dev_info[0])
        device.set_property(dev_info[1], 1 if msg.payload == b'on' else 0)
        client.publish(f"homeassistant/switch/{dev_info[0]}-{dev_info[1]}/status", msg.payload.decode(), retain=True)
        logging.info("MQTT: " + msg.topic + " - " + str(msg.payload))

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    if args.mqtt_user and args.mqtt_pass:
        mqttc.username_pw_set(args.mqtt_user, args.mqtt_pass)

    mqttc.connect(args.mqtt_ip)

    mqttc.loop_forever()
    