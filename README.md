# KeyboardWhiz code repository

This is the code for making KeyboardWhiz do its magic.
For PCB files, [refer here](https://github.com/CRimier/MyKiCad/tree/master/Reverse-engineering/keyboard_whiz)

## Features already available

- Interactive key scanning - highly flexible, user-friendly, and fast
- Forgiveness when it comes to mistakes, non-present/broken keys and extra keys
- Fn layer initial support
- Keyboard metadata input
- Copious amounts of hand-holding (the non-lewd kind)
- Short-circuited pin detection
- UK keyboard layout extra support
- User-friendly menu
- Ability to drop into a Python shell where called for
- Ability to work without the KeyboardWhiz hardware connected

## Features soon to be enabled/added

Ping me if you'd like to see any of these sooner - i.e. open an issue on GH or email me,
and I'll see if I can find a bit of time to help you with it.

- Color the main.py output
- LED scanning support
- Fn layer data parsing
- Convenient support for SD (scandinavian) keyboard extra keys
- Saving the keyboard data more often
- Renaming the JSON file from a menu
- Better datasheet generation - actually containing all the info
- Support for inserting the keyboard FPC into the connector with an offset
- Media key support - can be done through extra key addition now, but isn't as convenient
- Small HTTP server script so you can easily get the JSON and PDF files off your RPi. For now, feel free to use `python3 -m http.server`.
- Key verification after decoding (pressing keys and verifying these are the right keys). Can kinda be done in extra key scanning mode already.

## Features on the roadmap

- Keyboard controller using the KeyboardWhiz hardware - using `evdev`
- Keyboard tester script
- Audio feedback while scanning
- Easy submission to an online database

## Sharing your keyboard data with me

I would be exceptionally grateful if you could help me with this.

After you've entered some info about your keyboard (menu entry 5) and decoded it,
please, just email the data to crimier `att` protonmail `dot` com. I will connect some infrastructure
to this script into the future that would let you upload data with a single command-line script,
but the backend is not yet there, sadly. Working on it!

I only need the JSON file - PDF can always be generated from the JSON.

## Prerequisites

- `sudo apt install python3-smbus` for the main script
- `sudo apt install python3-reportlab` for PDF generation

## Downloading this code

I recommend you use `git` - run `git clone https://github.com/CRImier/KeyboardWhiz`.
Then, `cd KeyboardWhiz/`.

## Running the main script 

Run it with `sudo python3 -i main.py`. `sudo` might not be needed if you're running on a Raspberry Pi -
it's for I2C device access, which Raspbian probably already has proper permissions set up for.

By default, each time you run the script like `sudo python3 -i main.py`, it will assume you're working with a new keyboard,
and it will create a new JSON file in `keebs/`. It creates files like `keebs/keeb_YYMMDD_HHMMSS.json`,
where `YYMMDD_HHMMSS` is a timestamp.

To work with an already created file for a keyboard, run `sudo python3 -i main.py keebs/keeb_YYMMDD_HHMMSS.json` insteada.
For ease of use, you can input `sudo python3 -i main.py keebs/keeb_` and then press Tab one or two times - it will show you
all the keyboard JSON file names available, so that you don't have to copy-paste and can see which files you have.

If you used `sudo` for creation of the file (aka running the script for the first time),
you should also use `sudo` for i.e. editing the metadata, but if you didn't create the file with
`sudo`, you shouldn't need `sudo` to edit it, either.

You can scan some of the keys, then save your results and exit - then, later on, open the file and scan the remainder of the keys.
The script is flexible like that - you can edit keyboard data and/or scan new keys at any given point.
If you mark some of the keys as broken and then later manage to fix them, the script
will notice that and un-mark them as broken.

Keyboards are saved into `keebs/` folder, with the default filename generated as `keeb_YYMMDD_HHMMSS.json` -
as in, a timestamp. Feel free to rename the JSON file at any point.

You might need to enable the I2C device with `raspi-config`, and on x86 platforms, you might need to `sudo modprobe i2c-dev`.
To determine the bus that the KeyboardWhiz is attached to, see which device numbers you have in `/dev/i2c`, as in, run `ls /dev/i2c-*`.
For each bus number there, run `sudo i2cdetect -y %BUS_NUM%, substituting the bus number into `%BUS_NUM%`, for instance,
`sudo i2cdetect -y 1` and forth. One of these buses should have `21` and `22` - that'll be the bus you have the KeyboardWhiz
connected to.

Then, adjust the `bus_num = 1` line in the script as needed - `1` works for Raspberry Pi, my laptop with a HDMI-I2C adapter needs 5,
yours might differ.

To find the line you need to adjust for changing the bus number, do `nano main.py`, then press Ctrl+W, input `bus_num =` and press Enter,
it'll get you straight to the line in question. Change the number, press Ctrl+S to save the file, then Ctrl+X to exit.

## Generating PDFs

PDFs currently only contain pinout tables. They'll be more self-sufficient in the future, and once I'll improve
the PDF generation script, you'll be able to generate a new PDF from the JSON file alone, without re-connecting the keyboard.
However, having a pinout table is of huge help already.

To generate a PDF of the keyboard pinout, run `python3 generate_pdf.py keebs/keeb_YYMMDD_HHMMSS.json`,
where `YYMMDD_HHMMSS` is a timestamp. For ease of use,
you can input `python generate_pdf.py keebs/keeb_` and then press Tab one or two times - it will show you
all the keyboard JSON file names available, so that you don't have to copy-paste and can see which files you have.

The datasheet will be saved in `datasheets/datasheet_NAME.pdf`; the exact filename will be printed after the PDF generation script runs.

## Updating this code

Do `git pull`. If you've changed the bus number in your script, do `git checkout main.py`, then `git pull`, then change
the bus number again.
