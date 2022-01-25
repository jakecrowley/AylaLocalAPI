import hmac
import hashlib
import math
import random
from Crypto.Cipher import AES

class AylaEncryption:
    def __init__(self, SRnd1, SRnd2, NTime1, NTime2):
        self.SRnd1 = SRnd1
        self.SRnd2 = SRnd2
        self.NTime1 = NTime1
        self.NTime2 = NTime2
        self.LanipKey = "t2o+r4FgnE1o0J/HDQ5aZpVsEkqkyQ=="
        self.__init_aes_cipher()

    def encryptAndSign(self, data):
        sign = bytes.fromhex(hmac.new(self.app_sign_key(), msg = data, digestmod = hashlib.sha256).hexdigest())
        numtopad = math.ceil(len(data) / 16) * 16 - len(data)
        data += b'\x00' * numtopad
        enc = self.__encryptor.encrypt(data)
        return (enc, sign)

    def decryptAndVerify(self, data, sign):
        dec = self.__decryptor.decrypt(data)
        #if self.__aylahmac(self.dev_sign_key(), dec + sign) != sign:
        #    logging.warn("Signature mismatch")
        return dec

    def random_token(n):
        return ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXZY0123456789") for _ in range(n))

    def __init_aes_cipher(self):
        self.__encryptor = AES.new(self.app_crypto_key(), AES.MODE_CBC, self.app_iv_seed())
        self.__decryptor = AES.new(self.app_dec_key(), AES.MODE_CBC, self.app_dec_iv())

    def __aylahmac(self, key, data):
        signature = bytes.fromhex(hmac.new(key, msg = data, digestmod = hashlib.sha256).hexdigest())
        signature1 = bytes.fromhex(hmac.new(key, msg = signature + data, digestmod = hashlib.sha256).hexdigest())
        return signature1

    def app_sign_key(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd1.encode('utf-8') + self.SRnd2.encode('utf-8') + str(self.NTime1).encode('utf-8') + str(self.NTime2).encode('utf-8') + b'0'
        return self.__aylahmac(key, data)

    def app_crypto_key(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd1.encode('utf-8') + self.SRnd2.encode('utf-8') + str(self.NTime1).encode('utf-8') + str(self.NTime2).encode('utf-8') + b'1'
        return self.__aylahmac(key, data)

    def app_iv_seed(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd1.encode('utf-8') + self.SRnd2.encode('utf-8') + str(self.NTime1).encode('utf-8') + str(self.NTime2).encode('utf-8') + b'2'
        return self.__aylahmac(key, data)[:16]

    def dev_sign_key(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd2.encode('utf-8') + self.SRnd1.encode('utf-8') + str(self.NTime2).encode('utf-8') + str(self.NTime1).encode('utf-8') + b'0'
        return self.__aylahmac(key, data)

    def app_dec_key(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd2.encode('utf-8') + self.SRnd1.encode('utf-8') + str(self.NTime2).encode('utf-8') + str(self.NTime1).encode('utf-8') + b'1'
        return self.__aylahmac(key, data)

    def app_dec_iv(self):
        key = self.LanipKey.encode('utf-8')
        data = self.SRnd2.encode('utf-8') + self.SRnd1.encode('utf-8') + str(self.NTime2).encode('utf-8') + str(self.NTime1).encode('utf-8') + b'2'
        return self.__aylahmac(key, data)[:16]
