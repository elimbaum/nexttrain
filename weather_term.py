import requests
import json
from pprint import pprint
from datetime import datetime

city = "new+haven"

r = json.loads(requests.get(f"https://wttr.is/{city}?format=j1").content)

today = r['weather'][0]
tmrw = r['weather'][1]

def get_weather(data, from_hour=None):
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

def prob_to_str(x, elapsed=0):
    blocks = " ▁▂▃▄▅▆▇▉"

    bl = []
    for index, pr in enumerate(x):
        if index < elapsed:
            bl.append("▒")
            continue
        block_height = int(round(pr / 100 * (len(blocks) - 1)))
        bl.append(blocks[block_height])

    return ''.join(bl)

## print today
now = datetime.now()

dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

(l, h, p) = get_weather(today, now.hour)

print("┌" + "─" * 16 + "┐")
print(f"│{now.hour:2}:{now.minute:02}  {prob_to_str(p, now.hour // 3)}%│")
print(f"│{dow[now.weekday()]} {l:>3}°F →{h:>3}°F│")
print("└" + "─" * 16 + "┘")


## print tmrw
(l, h, p) = get_weather(tmrw)

print("┌" + "─" * 16 + "┐")
print(f"│tmrw   {prob_to_str(p)}%│")
print(f"│{dow[(now.weekday() + 1) % 7]} {l:>3}°F →{h:>3}°F│")
print("└" + "─" * 16 + "┘")

## |--------------|
## HH:MM   12345678
## XX°F - XX°F 
## |--------------|
## Tmrw    12345678
## XX°F - XX°F 
# deg symbol: 0xdf ?
# check 0xff - full block. so maybe one leftover
# underline is bottom row - two left over!
# arrow is available
# medium shade ▒

# https://omerk.github.io/lcdchargen/
