def remaining_today(day, hour):
    start = (hour // 3) * 300
    return [hr for hr in day['hourly'] if int(hr['time']) >= start]

# precip: next 24h, eight 3-hour slots from the current one
def next_24h(days, hour):
    start = (hour // 3) * 300
    slots = []
    for i, day in enumerate(days):
        for hr in day['hourly']:
            if i == 0 and int(hr['time']) < start:
                continue
            slots.append(hr)
            if len(slots) == 8:
                return slots
    return slots

def get_weather(hourly):
    low = min(int(hr['tempF']) for hr in hourly)
    high = max(int(hr['tempF']) for hr in hourly)
    precip = list(map(int, (hr['chanceofrain'] for hr in hourly)))
    return (low, high, precip)

def today_conditions(today, tomorrow, hour):
    (lo, hi, _) = get_weather(remaining_today(today, hour))
    (_, _, precip) = get_weather(next_24h([today, tomorrow], hour))
    return (lo, hi, precip)

def prob_to_str(x, blocks=" ▁▂▃▄▅▆▇▉"):
    bl = []
    for pr in x:
        block_height = int(round(pr / 100 * (len(blocks) - 1)))
        bl.append(blocks[block_height])

    return ''.join(bl)

def main():
    import requests
    import json
    from pprint import pprint
    from datetime import datetime
    import sys

    city = "new+haven" if len(sys.argv) < 2 else sys.argv[1]

    r = json.loads(requests.get(f"https://wttr.is/{city}?format=j1").content)

    today = r['weather'][0]
    tmrw = r['weather'][1]

    ## print today
    now = datetime.now()

    dow = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    (l, h, p) = today_conditions(today, tmrw, now.hour)

    print("┌" + "─" * 16 + "┐")
    print(f"│{now.hour:2}:{now.minute:02} p{prob_to_str(p)}|│")
    print(f"│{dow[now.weekday()]} {l:>3}°F →{h:>3}°F│")
    print("└" + "─" * 16 + "┘")


    ## print tmrw
    (l, h, p) = get_weather(tmrw['hourly'])

    print("┌" + "─" * 16 + "┐")
    print(f"│tmrw  p{prob_to_str(p)}|│")
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

if __name__ == "__main__":
    main()
