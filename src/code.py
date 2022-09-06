# SPDX-FileCopyrightText: 2022 Joshua Abell 
#
# SPDX-License-Identifier: BSD-3-Clause
# 

"""Little VFR/IFR Map"""

import time
import board
import ssl
import json
import time
import wifi
import socketpool
import adafruit_requests
import neopixel

# Get wifi details and more from a secrets.py file

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets and CheckWX keys are kept in secrets.py, please add them there!")
    print("You can obtain a free CheckWX API Key from https://www.checkwxapi.com/")
    raise

# Load station configuration and other settings

with open("stations.json") as stationData:
    stations = json.load(stationData)

# Initialize Neopixels

num_pixels = len(stations['list'])
pixel_pin = board.IO16
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.1, auto_write=False)

# Light everything up to start

WHITE = (255, 255, 255)
for n in range(num_pixels):
    pixels[n] = WHITE
pixels.show()

categories_to_color = {
    "VFR" : 0x00FF00,    # green
    "MVFR" : 0x0000FF,   #blue
    "IFR" : 0xFF0000,    #red
    "LIFR" : 0xFF00FF,   #magenta
    "UNK" : 0x000000     # Off
}

# Connect to WIFI

print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])
print("Connecting to %s"%secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!"%secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

def updateStation(requests, station):
    hdr = {"X-API-Key": secrets['checkwx_key']}
    url =  "https://api.checkwx.com/metar/" + station + "/decoded"
    print("Fetching text from", url)
    response = requests.get(url, headers=hdr)
    # print(response.text);    
    data = json.loads(response.text)

    # TEST DATA
    #with open("canned.json") as f:
    #    data = json.load(f)

    status = "UNK"
    if (len(data['data']) >= 1)     :
        station  = data['data'][0]['icao']
        status   = data['data'][0]['flight_category']

    print("Station=" + station + " Status=" + status)

    return status

while True:
    for station in stations['list']:
        status = updateStation(requests, station['icao'])
        pixels[station['led']] = categories_to_color[status]
        pixels.show()
    time.sleep(stations['refresh_rate'] * 60.0)