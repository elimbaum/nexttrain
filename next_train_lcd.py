#!/usr/bin/env python3

print("next-train lcd")
print("getting ready...")
print("  importing digital io")
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
from repo.next_train_term import train_sorter

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
import urllib.request as url
import json

import time
import signal
import sys
from collections import defaultdict

### API SETUP
API_URL = "http://api.wmata.com/StationPrediction.svc/json/GetPrediction/"
API_KEY = open('/home/pi/.wmata_api_key').read().strip()
TOP_KEY = "Trains"
json = json.JSONDecoder()

# station = "K02" # Clarendon
# station = "K01" # Courthouse
# station = "D07" # Potomac Ave
# station "C05" # Rosslyn
station = "E04" # columbia heights

# don't debounce microswitches!
button_no = Button(14, pull_up=True)
button_nc = Button(15, pull_up=True)

SLEEP_TIMEOUT = 60 # seconds
TIME_PER_PAGE =  4 # seconds

def build_train_msg(train):
    line = train['Line']

    # destination codes are almost always 8 chars, but constrain to
    # 9 character just to be safe
    dest = train['Destination'][:9]
    time = train['Min']

    if time.isdigit():
        time += "m"
    
    return "{:2} {:9} {:>3}".format(line, dest, time)

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

def train_sorter(train):
	time = train['Min']

	if time.isdigit():
		return int(time)

	if time == "ARR":
		return -1
	
	if time == "BRD":
		return -2

def get_new_data():
    # print("getting new data...")
    t = time.time()
    with url.urlopen(API_URL + station + "?api_key=" + API_KEY) as conn:
        resp = conn.read().decode()
        parsed = json.decode(resp)[TOP_KEY]
        # print("  new:", len(parsed), "trains ({:.4} sec)".format(time.time() - t))

        return sorted(parsed, key=train_sorter)

def shutdown(s, f):
    lcd.clear()
    set_backlight(False)
    print("\nbye")
    sys.exit(0)

# TODO no passengers/empty/other edge cases (tricky?)
# TODO get new data in a thread on a timer
# TODO validate API key, confirm connectivity?

signal.signal(signal.SIGINT, shutdown)

print("ready")
while True:
    set_backlight(False)
    lcd.clear()

    # wait to wake up from sleep
    wait_for_full_press()
    last_press = time.time()
    set_backlight(True) 
    lcd.message = "Loading..."

    # display loop
    while True:
        lcd.clear()
        trains = get_new_data()

        if len(trains) == 0:
            lcd.message = "No trains :("
            wait_for_full_press(TIME_PER_PAGE)
            break

        # sort by direction. reverse so that westbound trains are first
        trains = sorted(trains, key=train_sorter)

        display_top_line = True
        for t in trains:
            already_waited = False
            # print(t)
            if display_top_line:    
                lcd.clear()
                lcd.message = build_train_msg(t) + "\n"
                display_top_line = False
            else:
                lcd.message += build_train_msg(t)
                display_top_line = True

                # press to advance to next page, or wait a few sec
                if wait_for_full_press(TIME_PER_PAGE):
                    last_press = time.time()
                already_waited = True

            # short-circuit if we already waited
            if not already_waited and wait_for_full_press(TIME_PER_PAGE):
                last_press = time.time()

        if (time.time() - last_press) > SLEEP_TIMEOUT:
            break
