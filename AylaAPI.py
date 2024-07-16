from http.server import BaseHTTPRequestHandler, HTTPServer
from AylaEncryption import AylaEncryption
from base64 import b64encode, b64decode
import logging
import json
import time
import threading
import requests

api = None

class AylaAPIHttpServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if(self.path == "/local_lan/commands.json"):
            host_ip = self.client_address[0]
            device = api.get_device_by_ip(host_ip)

            if device == None:
                logging.error("Device with IP " + host_ip + " not found")
                self.send_response(500)
                self.end_headers()
                return

            dataPendJsonStr = json.dumps(device.data_pending).replace(" ", "")
            data = b'{"seq_no":' + str(device.seq_no).encode('utf-8') + b',"data":' + dataPendJsonStr.encode('utf-8') + b'}'
            device.seq_no += 1
            
            (enc, sign) = device.crypt_config.encryptAndSign(data)

            resp = f'{{"enc":"{b64encode(enc).decode()}","sign":"{b64encode(sign).decode()}"}}'

            self._set_response()
            self.wfile.write(resp.encode('utf-8'))
            device.data_pending = {}

            logging.info(f"GET request\nHost: {host_ip}\nPath: {self.path}\nPlaintext Response: {data}\nEncrypted Response: {resp}\n")

        else:
            self.send_response(400)
            self.end_headers()

    def do_POST(self):
        if(self.path == "/local_lan/key_exchange.json"):
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            body_json = json.loads(post_data.decode('utf-8'))

            device = api.get_device_by_key_id(body_json["key_exchange"]["key_id"])

            if device == None:
                logging.error("Device with key_id " + body_json["key_exchange"]["key_id"] + " not found")
                self.send_response(500)
                self.end_headers()
                return    

            config = AylaEncryption(
                body_json["key_exchange"]["random_1"], 
                AylaEncryption.random_token(16), 
                body_json["key_exchange"]["time_1"], 
                int(time.time() * 1000000),
                device.Lanip["lanip"]["lanip_key"]
                )

            device.crypt_config = config

            resp = f'{{"random_2": "{config.SRnd2}", "time_2": {config.NTime2}}}'

            self._set_response()
            self.wfile.write(resp.encode('utf-8'))

            logging.info(f"POST request\nHost: {device.lan_ip}\nPath: {self.path}\nBody: {post_data.decode('utf-8')}\nResponse: {resp}\n")
            logging.info(f"Encryption Paramters\nAppSignKey: {config.app_sign_key().hex()}\nAppCryptoKey: {config.app_crypto_key().hex()}\nAppIvSeed: {config.app_iv_seed().hex()}\nDevSignKey: {config.dev_sign_key().hex()}\n")

        elif(self.path.startswith("/local_lan/property/datapoint.json")):
            host_ip = self.client_address[0]
            content_length = int(self.headers['Content-Length']) 
            post_data = self.rfile.read(content_length) 
            body_json = json.loads(post_data.decode('utf-8'))

            device = api.get_device_by_ip(host_ip)

            if device == None:
                logging.error("Device with IP " + host_ip + " not found")
                self.send_response(500)
                self.end_headers()
                return

            enc = b64decode(body_json["enc"])
            sign = b64decode(body_json["sign"])
            dec = device.crypt_config.decryptAndVerify(enc, sign)

            self._set_response()
            self.wfile.write(post_data)
            logging.info(f"POST request\nHost: {host_ip}\nPath: {self.path}\nBody: {post_data.decode('utf-8')}\nDecrypted Body: {dec.decode('utf-8')}\n")
        
        # temporary endpoint to set setting values on the device
        # elif(self.path == "/set_device_property"):
        #     content_length = int(self.headers['Content-Length'])
        #     post_data = self.rfile.read(content_length)
        #     body_json = json.loads(post_data.decode('utf-8'))
        #     logging.info(f"POST request\nPath: {self.path}\nBody: {post_data.decode('utf-8')}\n")

        #     device = api.get_device_by_ip(body_json["device_ip"])

        #     if device == None:
        #         logging.error("Device with IP " + body_json["device_ip"] + " not found")
        #         self.send_response(500)
        #         self.end_headers()
        #         return

        #     device.set_property(body_json["property_name"], body_json["value"])
        #     device.notify()

        #     self._set_response()
        #     self.wfile.write('{"success": true}'.encode('utf-8'))
        # else:
        #     self.send_response(400)
        #     self.end_headers()

class DeviceProperty:
    def __init__(self, property):
        self.property = property

    def set_value(self, value):
        self.property["value"] = value
    
    def toJSON(self):
        return {"property": {"base_type":self.property["base_type"],"value":self.property["value"],"metadata":None,"name":self.property["name"]}}

class Device:
    def __init__(self, name, dsn, lan_ip, key, lan_enabled, properties, Lanip):
        self.name = name
        self.dsn = dsn
        self.lan_ip = lan_ip
        self.key = key
        self.lan_enabled = lan_enabled
        self.Lanip = Lanip

        self.crypt_config: AylaEncryption = None
        self.seq_no = 1
        self.data_pending = {}

        self.properties = []
        for prop in properties:
            self.properties.append(DeviceProperty(prop["property"]))

    def ping(self, notify=0):
        try:
            logging.info("Sending {} to {}\n".format("notify" if notify == 1 else "ping", api.devices[0].lan_ip))
            r = requests.post('http://' + api.devices[0].lan_ip + '/local_reg.json', json = {"local_reg":{"uri":"/local_lan","notify":notify,"ip":api.ip,"port":api.port}})
            if r.status_code != 202:
                logging.info("Request failed with status code {}".format(r.status_code))
        except Exception as e:
            logging.info("Request failed with exception {}".format(str(e)))

    def get_writeable_property_names(self):
        names = []
        for dp in self.properties:
            if dp.property["read_only"] == False:
                names.append(dp.property["name"])
        return names

    def get_property(self, name) -> DeviceProperty:
        for dp in self.properties:
            if(dp.property["name"] == name):
                return dp
        return None

    def set_property(self, name, value):
        prop = self.get_property(name)
        prop.set_value(value)
        if "properties" not in self.data_pending:
            self.data_pending["properties"] = []
        self.data_pending["properties"].append(prop.toJSON())
        self.ping(notify=1)

class AylaAPI:
    server: HTTPServer
    devices: list[Device]

    def __init__(self, ip, port):
        global api

        self.ip = ip
        self.port = port
        self.server = None
        self.devices = []

        with open("./config.json", "r") as file:
            devices_list = json.loads(file.read())["devices"]

        for device in devices_list:
            self.devices.append(Device(**device))
        
        api = self

        threading.Thread(target=self.start).start()
    
    def get_device_by_sn(self, dsn) -> Device:
        for device in self.devices:
            if(device.dsn == dsn):
                return device
        return None

    def get_device_by_ip(self, ip) -> Device:
        for device in self.devices:
            if(device.lan_ip == ip):
                return device
        return None
    
    def get_device_by_key_id(self, key_id) -> Device:
        for device in self.devices:
            if(device.Lanip["lanip"]["lanip_key_id"] == key_id):
                return device
        return None

    def start(self):
        self.server = HTTPServer((self.ip, self.port), AylaAPIHttpServer)
        logging.info(f"Starting server on {self.ip}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        logging.info("Stopping server")
        self.server.shutdown()
        self.server.server_close()