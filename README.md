# Ayla Local API Reverse Engineering

This is a WIP reverse engineering of the Ayla IoT local API that I am planning on eventually implementing into a Home Assistant integration.  The implementation initiates a connection with the device using the local api key exchange algorithm and can retrieve status updates, and it can also send commands to turn on/off the outlets/usb ports.

Currently, it is required to use the app to initially setup the device, and the Ayla API to retrieve the local key for the device. 

This has been tested in a limited capacity with only an APC (Schneider Electric) Smart Surge Protector, as that is the only Ayla device that I have. 

## Todo
- Home Assistant Integration (mqtt?)
- Implement WiFi setup?