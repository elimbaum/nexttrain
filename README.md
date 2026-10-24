# nexttrain
rpi box that tells me when the next metro is coming

- `next_train_term.py`: prototype that displays train info in the terminal
- `next_train_lcd.py`: raspi 16x2 character lcd version

Added to `/etc/rc.local` - run in the background. using `python3 -u` to not buffer the log file, in case there are transient errors i want to check on

disabled gui in `raspi-config`. should save some cpu/mem.

`requirements.txt` is way too much - just copied user env over to sudo env. but fine for now.

## circuit notes
- PFET to turn on backlight. this maximizes the brightness when on but does mean it's active low - i.e. when program not running, backlight on.
    - default pull up maybe? added `gpio=10=op,pu` to `/boot/config.txt`. didn't seem to do anything.
- trimpot for contrast
- should move schematic/board into here eventually.
- first solder-up didn't work because i mounted the transistor, and the raspi pin headers, backwards.

## todo maybe
- improved logging if errors
- press and hold for debug? inet connectivity, etc.

## first case print notes
- button is tight but that's fine. Not really room to screw in the collar.
- need a bit more vertical room for the rpi. should be LOOSE to slide in.
- display
    - vertical: is 26mm, needs to be 26.5
    - horizontal: is 71mm, needs to be 71.4
- adjust USB

## Wifi
After moving, needed to update the wifi! and forgot how... This did it:

Create `wpa_supplicant.conf`:

```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
  ssid="WIFI NAME"
  scan_ssid=1
  psk="WIFI PASSWORD"
  key_mgmt=WPA-PSK
}
```

and copy to the SD card `boot` partition.

## Updates for MBTA

- API information is [here](https://api-v3.mbta.com/).

To get predictions for Union Square,

```sh
curl -H "x-api-key: $MBTA_KEY" 'https://api-v3.mbta.com/predictions?filter%5Bstop%5D=place-unsqu' | jq
```

And my bus stop in the morning:
```sh
curl -H "x-api-key: $MBTA_KEY" 'https://api-v3.mbta.com/predictions?filter%5Bstop%5D=2612&filter%5Broute%5D=747' | jq
```

(`747` is CT2, and my bus stop is [#2612](https://www.mbta.com/stops/2612))

This `jq` query string will return the arrival times:
```sh
jq -r '.data .[].attributes.arrival_time
```