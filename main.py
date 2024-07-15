#!/usr/bin/env python3

from AylaAPI import AylaAPI, Device
import logging
import requests
import argparse
import time
import socket
import threading

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
    ip = device.lan_ip

    while True:
        logging.info("Sending ping to {}\n".format(ip))
        api.devices[0].ping()
        time.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    IP = get_ip()

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="IP address of the device", type=str)
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
    
    while True:
        try:
            cmd = input().split('=')
            api.devices[0].set_property(cmd[0], int(cmd[1]))
        except:
            pass