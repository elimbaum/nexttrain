#!/usr/bin/env python3
# Repurposed for Boston

print("next-train lcd - boston version")
print("getting ready...")
print("  importing digital io")

from asyncio import wait_for
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

### DISPLAY SETUP
lcd_rs = digitalio.DigitalInOut(board.D2)
lcd_en = digitalio.DigitalInOut(board.D3)
lcd_d7 = digitalio.DigitalInOut(board.D22)
lcd_d6 = digitalio.DigitalInOut(board.D27)
lcd_d5 = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D4)
lcd_backlight = digitalio.DigitalInOut(board.D10)

lcd_pins = [lcd_rs, lcd_en, lcd_d7, lcd_d6, lcd_d5, lcd_d4, lcd_backlight]

for p in lcd_pins:
    p.switch_to_output()    

lcd_columns = 16
lcd_rows = 2

# backlight is controlled by pfet, invert
def set_backlight(state):
    lcd.backlight = not state

lcd = characterlcd.Character_LCD_Mono(
    lcd_rs, lcd_en,
    lcd_d4, lcd_d5, lcd_d6, lcd_d7,
    lcd_columns, lcd_rows, lcd_backlight)
set_backlight(True)

lcd.message = "nexttrainbox\nchoo choo..."

print("  importing gpio")
from gpiozero import Button

print("  importing api")
import urllib
import urllib.request as url
import certifi
import ssl
import json

import time
import signal
import sys
import math
from collections import defaultdict
from datetime import datetime, timezone

### API SETUP
API_URL = "https://api-v3.mbta.com/predictions?filter[stop]="
API_KEY = open('/home/pi/.mbta_api_key').read().strip()
TOP_KEY = "data"
json = json.JSONDecoder()

ctx = ssl.create_default_context(cafile=certifi.where())

UNION_SQ_GREEN_LINE_STATION = "place-unsqu"
UNION_SQ_BUS_STOP = "2612"
BUS_LINE = "747" # CT2 internal number

# don't debounce microswitches!
button_no = Button(14, pull_up=True)
button_nc = Button(15, pull_up=True)

SLEEP_TIMEOUT = 30 # seconds

def build_message(line_name, data):
    now = datetime.now(tz=timezone.utc)

    available_space = lcd_columns - (len(line_name) + 1)

    arrival_times = []
    for v in data:
        attr = v.get('attributes', {})
        time_str = attr.get('departure_time')
        if time_str == None:
            time_str = attr.get('arrival_time')

        t = datetime.fromisoformat(time_str)
        delta_minutes = str(math.floor((t - now).total_seconds() / 60))
        arrival_times.append(delta_minutes)

    if data:
        arr_str = ', '.join(arrival_times) + ' m'

        while len(arr_str) > available_space:
            arrival_times = arrival_times[:-1]
            arr_str = ', '.join(arrival_times)
    else:
        arr_str = "none :("
    
    return f"{line_name} {arr_str.rjust(available_space)}"

# spdt break-before-make microswitch (arcade button) full sequence
def wait_for_full_press(t=None):
    # we can assume that if the first event times out, there will be no
    # complete press
    if not button_nc.wait_for_release(t):
        return False
    button_no.wait_for_press()
    button_no.wait_for_release()
    button_nc.wait_for_press()
    return True

def get_arrival_times(station, route=None):
    # print("getting new data...")
    request_url = f"{API_URL}{station}"

    if route:
        request_url += f"&filter[route]={route}"

    req = url.Request(request_url, headers={'x-api-key': API_KEY})

    with url.urlopen(req, context=ctx) as conn:
        resp = conn.read().decode()
        parsed = json.decode(resp)[TOP_KEY]
        # print("  new:", len(parsed), "trains ({:.4} sec)".format(time.time() - t))

        return parsed

def shutdown(s, f):
    lcd.clear()
    set_backlight(False)
    print("\nbye")
    sys.exit(0)

# TODO get new data in a thread on a timer

signal.signal(signal.SIGINT, shutdown)

# Check internet
try:
    with url.urlopen('https://8.8.8.8', context=ctx) as conn:
        pass
except urllib.error.URLError as e:
    print(e)
    lcd.clear()
    lcd.message = "no internet"
    wait_for_full_press(SLEEP_TIMEOUT)

print("ready")
while True:
    set_backlight(False)
    lcd.clear()

    # wait to wake up from sleep
    wait_for_full_press()
    set_backlight(True) 
    lcd.message = "Loading..."

    # display loop
    while True:
        lcd.clear()

        try:
            train_times = get_arrival_times(UNION_SQ_GREEN_LINE_STATION)
            bus_times = get_arrival_times(UNION_SQ_BUS_STOP, BUS_LINE)
        except urllib.error.URLError:
            # if there was an error getting the train data
            # this can happen very soon after boot
            lcd.message = "connection error\nplease try again"
            wait_for_full_press(SLEEP_TIMEOUT)
            break

        s = ( build_message("CT2", bus_times) + "\n"
            + build_message("GL ", train_times))

        lcd.message = s

        # short-circuit if we already waited
        if wait_for_full_press(SLEEP_TIMEOUT):
            break
