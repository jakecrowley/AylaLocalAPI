from http.server import BaseHTTPRequestHandler, HTTPServer
from AylaEncryption import AylaEncryption
from base64 import b64encode, b64decode
import logging
import json
import time
import threading

config = None
seq_no = 1

class AylaAPIHttpServer(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        global config
        global seq_no

        if(self.path == "/local_lan/commands.json"):
            data = b'{"seq_no":' + str(seq_no).encode('utf-8') + b',"data":{}}'
            seq_no += 1
            
            (enc, sign) = config.encryptAndSign(data)

            resp = f'{{"enc":"{b64encode(enc).decode()}","sign":"{b64encode(sign).decode()}"}}'

            self._set_response()
            self.wfile.write(resp.encode('utf-8'))

            logging.info(f"GET request\nPath: {self.path}\nPlaintext Response: {data}\nEncrypted Response: {resp}\n")

        else:
            self.send_response(400)
            self.end_headers()

    def do_POST(self):
        global config 

        if(self.path == "/local_lan/key_exchange.json"):
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            body_json = json.loads(post_data.decode('utf-8'))

            config = AylaEncryption(
                body_json["key_exchange"]["random_1"], 
                AylaEncryption.random_token(16), 
                body_json["key_exchange"]["time_1"], 
                int(time.time() * 1000000))

            resp = f'{{"random_2": "{config.SRnd2}", "time_2": {config.NTime2}}}'

            self._set_response()
            self.wfile.write(resp.encode('utf-8'))

            logging.info(f"POST request\nPath: {self.path}\nBody: {post_data.decode('utf-8')}\nResponse: {resp}\n")
            logging.info(f"Encryption Paramters\nAppSignKey: {config.app_sign_key().hex()}\nAppCryptoKey: {config.app_crypto_key().hex()}\nAppIvSeed: {config.app_iv_seed().hex()}\nDevSignKey: {config.dev_sign_key().hex()}\n")

        elif(self.path.startswith("/local_lan/property/datapoint.json")):
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            body_json = json.loads(post_data.decode('utf-8'))

            enc = b64decode(body_json["enc"])
            sign = b64decode(body_json["sign"])
            dec = config.decryptAndVerify(enc, sign)

            self._set_response()
            self.wfile.write(post_data)
            logging.info(f"POST request\nPath: {self.path}\nBody: {post_data.decode('utf-8')}\nDecrypted Body: {dec.decode('utf-8')}\n")
        else:
            self.send_response(400)
            self.end_headers()

class AylaAPI:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = None
        threading.Thread(target=self.start).start()

    def start(self):
        self.server = HTTPServer((self.ip, self.port), AylaAPIHttpServer)
        logging.info(f"Starting server on {self.ip}:{self.port}")
        self.server.serve_forever()

    def stop(self):
        logging.info("Stopping server")
        self.server.shutdown()
        self.server.server_close()
