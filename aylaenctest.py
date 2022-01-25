from AylaEncryption import AylaEncryption
from base64 import b64encode

config = AylaEncryption("PniuiGHpoOogs8cN", "MShUPfDxO2zPhORF", 151067552164306, 1643061696153873)
print(f"Encryption Paramters\nAppSignKey: {config.app_sign_key().hex()}\nAppCryptoKey: {config.app_crypto_key().hex()}\nAppIvSeed: {config.app_iv_seed().hex()}\nDevSignKey: {config.dev_sign_key().hex()}\nAppDecKey: {config.app_dec_key().hex()}\nAppDecIv: {config.app_dec_iv().hex()}\n")

pt = b'{"seq_no":1,"data":{}}'
(enc, sign) = config.encryptAndSign(pt)
print(f"Plaintext: {pt.decode()}\nEncrypted: {b64encode(enc).decode()}\nSignature: {b64encode(sign).decode()}")
