#!/usr/bin/env python3
# Repurposed for New Haven


print("next-train lcd - new haven version (weather)")
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
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight
)
set_backlight(True)

print("  creating custom chars")

# checkerboard
lcd.create_char(0, [0b01010, 0b10101] * 3 + [0b01010, 0])

# bar graph
for i in range(1, 7 + 1):
    n0 = 8 - i
    lcd.create_char(i, [0] * n0 + [0b11111] * i)

lcd.message = "nextweatherbox\nchoo choo..."

print("  importing gpio")
from gpiozero import Button

print("  importing api")
import urllib
import urllib.request as url
import json

import time
import signal
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import calendar

### API SETUP
API_URL = "https://wttr.is/"
CITY = "new+haven"

# don't debounce microswitches!
button_no = Button(14, pull_up=True)
button_nc = Button(15, pull_up=True)

SLEEP_TIMEOUT = 30  # seconds

def parse_struct(data, from_hour=None):
    hourly = data['hourly']
    forecast_hourly = hourly
    if from_hour is not None:
        start_time = (from_hour // 3) * 300
        forecast_hourly = [hr for hr in hourly if int(hr['time']) >= start_time]

    if forecast_hourly:
        low = min(int(hr['tempF']) for hr in forecast_hourly)
        high = max(int(hr['tempF']) for hr in forecast_hourly)
    else:
        low = int(data['mintempF'])
        high = int(data['maxtempF'])

    precip = list(map(int, (hr['chanceofrain'] for hr in hourly)))

    return (low, high, precip)

def pr_to_str(x, hour=0):
    blocks = " \x01\x02\x03\x04\x05\x06\x07\xff"

    if hour is None:
        hour = 0

    elapsed = hour // 3

    bl = []
    for index, pr in enumerate(x):
        if index < elapsed:
            # Checkerboard
            bl.append("\x00")
            continue
        block_height = int(round(pr / 100 * (len(blocks) - 1)))
        bl.append(blocks[block_height])

    return ''.join(bl)


def build_message(header, timestamp, wx, progress=False):
    deg = "\xdf"
    arrow = "\x7e"

    extra = timestamp.hour if progress else None

    (lo, hi, precip) = parse_struct(wx, extra)

    dow = calendar.day_abbr[timestamp.weekday()].lower()

    return "\n".join([
        f"{header:5} r{pr_to_str(precip, extra)}%",
        f"{dow} {lo:>3}{deg}F {arrow}{hi:>3}{deg}F"
    ])

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


def get_weather(city):
    # print("getting new data...")
    request_url = f"{API_URL}{city}?format=j1"

    req = url.Request(request_url)

    with url.urlopen(req) as conn:
        resp = conn.read().decode()
        parsed = json.loads(resp)['weather']

        return parsed


def shutdown(s, f):
    lcd.clear()
    lcd.message = "zzz..."
    set_backlight(False)
    print("\nbye")
    print(f)
    sys.exit(0)


# TODO get new data in a thread on a timer

signal.signal(signal.SIGINT, shutdown)

time.sleep(1)

# Check internet
try:
    print("  dns check")
    with url.urlopen("https://8.8.8.8") as conn:
        pass
except urllib.error.URLError as e:
    print(e)
    lcd.clear()
    lcd.message = "no internet!"
    wait_for_full_press(SLEEP_TIMEOUT)

print("ready")
while True:
    set_backlight(False)
    lcd.clear()

    # wait to wake up from sleep
    wait_for_full_press()
    set_backlight(True)

    lcd.clear()
    lcd.message = "Loading..."
    try:
        weather = get_weather(CITY)
        today_wx, tmrw_wx = weather[0], weather[1]
    except urllib.error.URLError:
        # if there was an error getting the train data
        # this can happen very soon after boot
        lcd.clear()
        lcd.message = "connection error\nplease try again"
        wait_for_full_press(SLEEP_TIMEOUT)
        continue

    lcd.clear()

    now_t = datetime.now()
    time_str = f"{now_t.hour:2}:{now_t.minute:02}"

    tmrw_t = now_t + timedelta(1)

    s1 = build_message(time_str, now_t, today_wx, progress=True)
    s2 = build_message("tmrw", tmrw_t, tmrw_wx)

    # switch between pages
    while True:
        lcd.message = s1

        # on timeout, sleep. on press, next page
        if not wait_for_full_press(SLEEP_TIMEOUT):
            break

        lcd.message = s2

        # on press, reload
        if not wait_for_full_press(SLEEP_TIMEOUT):
            break

