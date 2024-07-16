from AylaCloudAPI import login, getDevices
from textwrap import indent
import argparse
import logging
import jsonpickle

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("email", help="Email for the Ayla API", type=str)
    parser.add_argument("password", help="Password for the Ayla API", type=str)
    args = parser.parse_args()

    access_token = login(args.email, args.password)
    devices = getDevices(access_token)

    with open("config.json", "w") as f:
        f.write(jsonpickle.encode({'auth_token': access_token, 'devices': devices}, indent=4, unpicklable=False))
        logging.info(f"Retrieved {len(devices)} devices.")
