#!/usr/bin/env python3

from AylaAPI import AylaAPIHttpServer
import logging
import requests
import argparse
import threading
import time

httpd = None

def start_server(ip, port):
    global httpd


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="IP address of the device", type=str)
    parser.add_argument("--bind", dest='bind', help="IP to run the API server on", type=str, default='')
    parser.add_argument("--port", dest='port', help="Port to run the API server on", type=int, default=10275, required=False)
    args = parser.parse_args()

    while True:
        if httpd is None:
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