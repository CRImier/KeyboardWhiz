import select
import string
import smbus
import time
import sys

from copy import copy
from collections import OrderedDict

__version__ = "0.1"

l = list

# TODO: add a yes/no helper function

# TODO: properly add caps-insensitivity to keys_to_press

keys_to_press = ["Esc"] +\
                ["F{}".format(i) for i in range(1, 13)] +\
                ["Print Screen", "Pause", "Insert", "Delete", "`"] +\
                l('1234567890-=') + ["BACKSPACE"] +\
                ['TAB']+ l('QWERTYUIOP[]\\') +\
                ['CAPSLOCK']+l('ASDFGHJKL;\'') +\
                ['Left SHIFT'] + l('ZXCVBNM,./') + ['Right SHIFT'] +\
                ["Left CTRL", "Fn", "Win", "Left ALT", "SPACE"] +\
                ["Right ALT", "Context", "Right CTRL"] +\
                ['UP', 'DOWN', 'LEFT', 'RIGHT'] +\
                ["HOME", "PGUP", "PGDOWN", "END"]

# Additional keys to press if the keyboard has a numpad
numpad_keys_to_press =  ["KP{}".format(i) for i in range(10)] +\
                        ["KPENTER", "KPDOT"]

# User-friendly 
key_translations = {".":"DOT", ",":"COMMA", "/":"SLASH", "'":"APOSTROPHE", "[":"LBRACE", "]":"RBRACE", "=": "EQUAL", "-":"MINUS", "`":"GRAVE", "\\":"BACKSLASH", ";":"SEMICOLON", "Left SHIFT":"LEFTSHIFT", "Right SHIFT":"RIGHTSHIFT", "Left ALT":"LEFTALT", "Right ALT":"RIGHTALT", "Win":"LEFTMETA", "Fn":"FN"}

# Messages

welcome_msg = """Welcome to KeyboardWhiz script v{__version__}! \n This""".format(**globals())

scanning_msg_first = """Let's scan the keyboard quickly!"""



bus = smbus.SMBus(5)
a1 = 0x21
a2 = 0x22
#a1 = 0x25
#a2 = 0x26

# MCP23017 register descriptions
       #i  a   io    pu   read  write, str
eps = ((0, a1, 0x00, 0xc, 0x12, 0x14, "2A"), \
       (1, a1, 0x01, 0xd, 0x13, 0x15, "2B"), \
       (2, a2, 0x00, 0xc, 0x12, 0x14, "1A"), \
       (3, a2, 0x01, 0xd, 0x13, 0x15, "1B") )

# short functions to read/write to MCP23017 registers
def smr(a, p, d):
  bus.write_byte_data(a, p, d)

def gmr(a, p):
  return bus.read_byte_data(a, p)

# mapping that allows us to get from "expander+port+pin" to "connector pin number"
pin_mapping = [ \
   "1A0", "1A1", "1A2", "1A3", "1A7", "1A6", "1A5", "1A4",
   "1B3", "1B2", "1B1", "1B0", "1B4", "1B5", "1B6", "1B7",
   "2A0", "2A1", "2A2", "2A3", "2A7", "2A6", "2A5", "2A4",
   "2B3", "2B2", "2B1", "2B0", "2B4", "2B5", "2B6", "2B7"
]

# input functions

def stdin_has_char():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def stdin_readall():
    s = ''
    while stdin_has_char():
        s += sys.stdin.read(1)
    return s

# expander setup functions

def setup_for_key_scanning():
    for _, a, i, p, r, w, _ in eps:
        smr(a, w, 0x00) # writing 0 to all pin latches
        smr(a, i, 0xff) # setting all pins as inputs
        smr(a, p, 0xff) # enabling all pullups
        print(hex(a), gmr(a, r))

def setup_for_leds():
    for _, a, i, p, _, w, _ in eps:
        smr(a, w, 0xff) # writing ff to all pin latches
        smr(a, i, 0x00) # setting all pins as outputs
        smr(a, p, 0x00) # disabling all pullups

def scan_usual_keys(info):
 # Interactive key picker
 setup_for_key_scanning()
 expected_key_index = 0 # index in the list of the expected keys
 if "raw" not in info:
    data = {} # dict that will have initial keyboard data
    info["raw"] = data
 else:
    data = info["raw"]
 time_of_last_press = time.time()

 # helpers
 def prompt_key():
    print("Enter key for {}: ".format(keys_to_press[expected_key_index]), end='');sys.stdout.flush()
 def get_last_pressed_key():
    last_pressed_key = keys_to_press[expected_key_index-1]
    return key_translations.get(last_pressed_key, last_pressed_key)
 def remove_key_from_data(key):
    nonlocal expected_key_index
    for k, v in data.items():
        if v == key:
            data.pop(k)
            if expected_key_index:
                expected_key_index -= 1
            return
 prompt_key()
 # main loop: infinite, breaks on 'return' statements
 while True:
  if expected_key_index == len(keys_to_press):
    # we reached the end of our key list, don't need to do anything
    print(''); return info
  for y, a, i, _, _, w, s1 in eps: # for each expander port
    for b in range(8): # picking one pin on the expander
      smr(a, i, 1<<b^0xFF) # setting one pin on the expander as input
      for z, ax, _, _, rx, _, s2 in eps: # for each expander port (again)
        d = gmr(ax, rx) # read the port
        if z == y: # if it's the same port where pin is being enabled,
          d |= 1<<b # ignore the pin that's being enabled
        d = d ^ 0xFF # invert the port
        if d != 0x00: # we got some pins set on this port!
            for n in range(8): # going through each bit,
              if d & (1 << n): # if any bit is set
                d1 = pin_mapping.index(s1+str(b)) # port and bit which we have set - get the pin number
                d2 = pin_mapping.index(s2+str(n)) # port and bit where we got a response - get the pin number
                d1, d2 = sorted([d1, d2]) # sort the pin numbers - so that connection between 1,2 and 2,1 is interpreted as the same connection
                id = "{}-{}".format(d1, d2) # string ID for easily storing and looking up keys using a dictionary
                if id not in data: # key has not yet been saved
                  key = keys_to_press[expected_key_index]
                  #key = raw_input("Enter key for {}: ".format(id)) # getting key name from user
                  #if key: # Key has been input
                    #data[id] = key # saving it in the dictionary
                  data[id] = key_translations.get(key, key) # saving it in the dictionary
                  expected_key_index += 1
                  time_of_last_press = time.time()
                  if expected_key_index == len(keys_to_press): # we ran out of keys here
                      print(''); return info # TODO: refactor out and reuse the loop-beginning check somehow?
                  print(''); prompt_key()
                else: # key is already known
                  key = data[id] # shorthand for ease of coding
                  last_pressed_key = get_last_pressed_key()
                  time_since_last_press = time.time() - time_of_last_press
                  #print(last_pressed_key)
                  if (key != last_pressed_key or time_since_last_press > 1.5) and key != "IGNORE": # IGNOREd keys won't be shown when pressed
                      print("{} already pressed, is {}!".format(id, key)) # print the pressed keys for informational purposes
        # checking stdin
        if stdin_has_char():
            s = stdin_readall().strip()
            # we got some input from the user!
            print(repr(s))
            if s == 'n': # no such key
                print("Skipping key", keys_to_press[expected_key_index], end='')
                expected_key_index += 1
                if expected_key_index == len(keys_to_press):
                    print(''); return info
                print(''); prompt_key()
            elif s == 'x': # extra key
                key_name = input("Enter your key name! ").upper()
                if key_name:
                    #key_name = "KEY_"+key_name if not key_name.startswith("KEY_") else key_name
                    print("Now press the key name in question")
                    keys_to_press.insert(expected_key_index, key_name)
                print(''); prompt_key()
            elif s == 'b': # backspace
                # removing the last key that was pressed, going to the last key
                last_pressed_key = get_last_pressed_key()
                remove_key_from_data(last_pressed_key)
                prompt_key()
        #time.sleep(0.1)
      smr(a, i, 0xFF) # after each port bit has been scanned, set all pins to zero (TODO: optimize so that this only gets done after the port is scanned (TODO: check if this is a valid todo at all))

info = {}
#info = {'raw': {'6-16': 'ESC', '17-18': 'F1', '14-18': 'F2', '13-18': 'F3', '6-18': 'F4', '14-15': 'F5', '13-15': 'F6', '6-15': 'F7', '15-17': 'F8', '14-27': 'F9', '13-27': 'F10', '6-27': 'F11', '17-27': 'F12', '17-26': 'PRINTSCREEN', '6-29': 'EJECT', '17-29': 'DELETE', '14-16': 'GRAVE', '8-16': '1', '8-15': '2', '8-18': '3', '8-19': '4', '14-19': '5', '14-21': '6', '8-21': '7', '8-22': '8', '8-27': '9', '8-28': '0', '14-28': 'MINUS', '17-28': 'EQUAL', '7-16': 'Q', '7-15': 'W', '7-18': 'E', '7-19': 'R', '13-19': 'T', '13-21': 'Y', '7-21': 'U', '7-22': 'I', '7-27': 'O', '7-28': 'P', '13-28': 'LBRACE', '13-22': 'RBRACE', '14-22': 'BACKSLASH', '10-16': 'A', '10-15': 'S', '10-18': 'D', '10-19': 'F', '6-19': 'G', '6-21': 'H', '10-21': 'J', '10-22': 'K', '10-27': 'L', '10-28': 'SEMICOLON', '6-28': 'APOSTROPHE', '11-16': 'Z', '11-15': 'X', '11-18': 'C', '11-19': 'V', '17-19': 'B', '17-21': 'N', '11-21': 'M', '11-22': 'COMMA', '11-27': 'DOT', '11-28': 'SLASH'}}

pbin = lambda v: "0b"+bin(v)[2:].zfill(8)

def light_leds(inverted=True):
  # non-inverted version untested
  found_leds = {}
  # setting all ports to proper initial values to avoid false LED detections in case the "inverted" value changes between function runs
  for _, a, _, _, _, w, _ in eps:
    smr(a, w, 0xFF if inverted else 0)
  #found_leds = {'wifi_white': [2, 3, 1], 'wifi_orange': [2, 3, 2], 'mute': [2, 3, 7], 'caps': [2, 3, 7]}
  found_leds = {'wifi_white': [2, 3, 2], 'wifi_orange': [2, 3, 1], 'mute': [2, 3, 3], 'caps': [2, 3, 6]}
  for y, a, i, _, _, w, s1 in eps: # for each expander port
    break
    for b in range(8): # picking one pin on the expander
      pin_enable_mask = (1<<b ^ 0xFF) if inverted else 1<<b
      smr(a, w, pin_enable_mask) # enabling one pin on the expander
      for z, ax, _, _, rx, _, s2 in eps: # for each expander port (again)
        d = gmr(ax, rx) # read the port
        if y == z:
            if inverted:
                d |= pin_enable_mask ^ 0xFF
            else:
                d &= pin_enable_mask ^ 0xFF
        print(y, z, pbin(pin_enable_mask), b, pbin(d))
      time.sleep(1)
      if stdin_has_char():
        ch = stdin_readall()
        # pause
        led_name = input("Enter your LED name! ")
        if led_name:
            found_leds[led_name] = [y, z, b]
    smr(a, w, 0xFF if inverted else 0) # setting the port to all-high after we're done with it
  print(found_leds)
  # now looking for common pins
  reg_values = [0xFF if inverted else 0 for ep in eps]
  for led_name, led_desc in found_leds.items():
    y, z, b = led_desc
    if inverted:
        reg_values[y] &= 1<<b ^ 0xFF
    else:
        reg_values[y] |= 1<<b
    print([bin(r) for r in reg_values])
  

def main():
  try:
    scan_usual_keys(info)
  except KeyboardInterrupt:
    pass #print(info)

def process_raw_data(info):
    get_rc_mapping(info)
    get_table(info)
    print(info["table"])
    print("Pin table:", info["table"])

def get_rc_mapping(info):
    ############################
    # Now, processing the resulting changes:
    # finding out which pins would be rows and which would be columns
    ############################

    rc_mapping = []
    # assemble rows and columns from the data we got
    a1 = []; a2 = []
    # get ourselves a copy of the data so that we can iterate over it and remove elements one by one
    rc_data = copy(info["raw"])

    # The loop's purpose is to sort columns apart from rows while not confusing them

    # get the first pin pair as a "boostrap" pair for the while loop, assign first pin to a1 and second pin to a2
    key, value = list(info["raw"].items())[0]
    d1, d2 = [int(c) for c in key.split('-')]
    a1.append(d1); a2.append(d2)
    #rc_data.pop(key)
    changes_made = True
    while changes_made:
        changes_made = False
        for key, value in info["raw"].items():
            d1, d2 = [int(c) for c in key.split('-')]
            if all([x not in a1+a2 for x in [d1, d2]]):
                # neither of the pins are in the rows+columns we're assembling, ignoring them for now
                # since, we need to match rows to columns in order to have everything work
                pass
            elif all([x in a1+a2 for x in [d1, d2]]):
                # both pins are already in the rows+columns we're assembling, no need to add them anywhere
                # other than remove the key from rc_data
                rc_mapping.append((d1, d2, value))
                rc_data.pop(key, None)
            else:
                # only one of the pins has not yet been added, perfect!
                if d1 in a1:
                    a2.append(d2)
                elif d1 in a2:
                    a1.append(d2)
                elif d2 in a1:
                    a2.append(d1)
                elif d2 in a2:
                    a1.append(d1)
                rc_mapping.append((d1, d2, value))
                rc_data.pop(key)
                changes_made = True
        # we've run out of keys we can map to existing rows&columns and there's still keys left over
        # i.e. a Power key could have two pins - GND and BTN
        if not changes_made and rc_data:
            pass

    info["rc_mapping"] = list(set(rc_mapping))
    info["a1"] = a1
    info["a2"] = a2
    info["unsorted"] = rc_data
    if rc_data:
        print("Unsorted pins: ", str(rc_data))
    return info

def get_table(info):
    a1 = sorted(info["a1"]); a2 = sorted(info["a2"])

    if len(a1) >= len(a2):
        rows = a2; columns = a1
    else:
        rows = a1; columns = a2

    info["rows"] = rows
    info["columns"] = columns

    print("Rows:", rows)
    print("Columns:", columns)

    # pin table
    table = dict([[row, {}] for row in rows])
    for a1, a2, key in info["rc_mapping"]:
        #print(a1, a2, key)
        rnum = a1 if a1 in rows else a2
        cnum = a1 if a1 in columns else a2
        table[rnum][cnum] = key
    info["table"] = table

main()
print(info)
process_raw_data(info)
print(info)

"""
setup_for_leds()
light_leds()
"""
