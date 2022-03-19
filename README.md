# nexttrain
rpi box that tells me when the next metro is coming

- `next_train_term.py`: prototype that displays train info in the terminal
- `next_train_lcd.py`: raspi 16x2 character lcd version

Added to `/etc/rc.local` - run in the background. using `python3 -u` to not buffer the log file, in case there are transient errors i want to check on.

`requirements.txt` is way too much - just copied user env over to sudo env. but fine for now.

## circuit notes
- PFET to turn on backlight. this maximizes the brightness when on but does mean it's active low - i.e. when program not running, backlight on.
    - default pull up maybe? added `gpio=10=op,pu` to `/boot/config.txt`
- trimpot for contrast
- should move schematic/board into here eventually.
- first solder-up didn't work because i mounted the transistor, and the raspi pin headers, backwards.

## todo maybe
- improved logging if errors
- press and hold for debug? inet connectivity, etc.