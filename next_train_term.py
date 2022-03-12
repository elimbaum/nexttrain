#!/usr/bin/env python3

import urllib.request as url

import json

API_KEY = open("/home/pi/.wmata_api_key").read().strip()
API_URL = "http://api.wmata.com/StationPrediction.svc/json/GetPrediction/"

# station = "K02" # Clarendon
# station = "C05" # Rosslyn
station = "E04" # columbia heights
# station = "All"

TOP_KEY = "Trains"

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

json = json.JSONDecoder()

with url.urlopen(f"{API_URL}{station}?api_key={API_KEY}") as conn:
	resp = conn.read().decode()
	parsed = json.decode(resp)[TOP_KEY]

	last_group = None

	# Group is which track the train is on
	for train in sorted(parsed, key=lambda c:c['Group']):
		line = train['Line']
		dest = train['Destination']
		time = train['Min']
		grp = train['Group']

		# linebreak between tracks
		if last_group != None and last_group != grp:
			print()

		last_group = grp

		# No passengers
		if line not in iter(colors):
			continue

		if time.isdigit():
			time += "m"
		
		print(f"{COLOR_PREFIX}{colors[line]}m", end='')
		print(f"{line} {dest:10} {time:>4} {COLOR_RESET}")
