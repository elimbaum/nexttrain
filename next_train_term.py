#!/usr/bin/env python3

import urllib.request as url
import os
import json
import ssl
import certifi
import math
from datetime import datetime, timezone

if 'MBTA_KEY' in os.environ:
	API_KEY = os.environ['MBTA_KEY']
else:
	API_KEY = open("/home/pi/.mbta_api_key").read().strip()

API_URL = "https://api-v3.mbta.com/predictions?filter[stop]="
ctx = ssl.create_default_context(cafile=certifi.where())

TOP_KEY = 'data'

COLOR_PREFIX = "\033[38;5;"
COLOR_RESET = "\033[0m"

colors = {
	'SV' : 15,
	'OR' : 209,
	'BL' : 32,
	'GR' : 28,
	'YL' : 11,
	'RD' : 1
}

DISPLAY_WIDTH = 16

json = json.JSONDecoder()

def train_sorter(train):
	time = train['Min']

	if time.isdigit():
		return int(time)

	if time == "ARR":
		return -1
	
	if time == "BRD":
		return -2
	

def get_arrival_times(station, route=None):
	now = datetime.now(tz=timezone.utc)

	request_url = f"{API_URL}{station}"
	if route:
		request_url = f"{API_URL}{station}&filter[route]={route}"

	req = url.Request(request_url, headers={'x-api-key': API_KEY})

	with url.urlopen(req, context=ctx) as conn:
		resp = conn.read().decode()
		parsed = json.decode(resp)[TOP_KEY]

		output = []

		for v in parsed:
			attr = v['attributes']
			time_str = attr.get('departure_time') or attr.get('arrival_time')

			if time_str == None:
				output.append('?')
			else:
				t = datetime.fromisoformat(time_str)
				delta_minutes = str(max(0, math.floor((t - now).total_seconds() / 60)))
				output.append(delta_minutes)
			
		s = ' '.join(output)[:DISPLAY_WIDTH - 4]
		return s.rjust(DISPLAY_WIDTH - 4)


BUS_STOP = "2612"
GL_STOP  = "place-unsqu"

print(f"{COLOR_PREFIX}{colors['YL']}m" "CT2 ", end='')
print(get_arrival_times(BUS_STOP, 747))

print(f"{COLOR_PREFIX}{colors['GR']}m" "GL  ", end='')
print(get_arrival_times(GL_STOP))