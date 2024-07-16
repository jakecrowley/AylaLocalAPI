#!/usr/bin/env python3

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

    parser = argparse.ArgumentParser()
    if IP is None:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, required=True)
    else:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, default=IP)
    parser.add_argument("--port", dest='port', help="Port to run the API server on", type=int, default=10275, required=False)
    args = parser.parse_args()

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
    mqttc.username_pw_set("mqtt", "2fUM2rQP3f4NT17iZq696bRz")

    mqttc.connect('192.168.0.157')

    mqttc.loop_forever()
    # while True:
    #     try:
    #         cmd = input().split('=')
    #         api.devices[0].set_property(cmd[0], int(cmd[1]))
    #     except:
    #         pass