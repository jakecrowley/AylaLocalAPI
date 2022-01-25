#!/usr/bin/env python3

from AylaAPI import AylaAPI
import logging
import requests
import argparse
import time
import socket

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

if __name__ == "__main__":
    global api
    logging.basicConfig(level=logging.INFO)

    IP = None

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="IP address of the device", type=str)
    if IP is None:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, required=True)
    else:
        parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, default=IP)
    parser.add_argument("--port", dest='port', help="Port to run the API server on", type=int, default=10275, required=False)
    args = parser.parse_args()

    api = AylaAPI(args.bind, args.port)

    while True:
        if api.server is None:
            time.sleep(0.25)
            continue

        try:
            logging.info("Sending ping to {}\n".format(args.ip))
            r = requests.put('http://' + args.ip + '/local_reg.json', json = {"local_reg":{"uri":"/local_lan","notify":0,"ip":args.bind,"port":args.port}})
            if r.status_code != 202:
                logging.info("Request failed with status code {}".format(r.status_code))
        except Exception as e:
            logging.info("Request failed with exception {}".format(str(e)))
        time.sleep(10)