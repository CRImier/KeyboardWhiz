import traceback
import select
import string
import time
import json
import sys
import os

from copy import copy
from datetime import datetime
from collections import OrderedDict

import smbus

__version__ = "0.2"

# don't recall what this is for, but prolly used somewhere down there
l = list

# TODO: properly add caps-insensitivity to keys_to_press
# ... wait what?

# globals
bus = None
info = {}

# Key definitions for interactive scanning

keys_to_press = ["Esc"] +\
                ["F{}".format(i) for i in range(1, 13)] +\
                ["Print Screen", "Pause", "Insert", "Delete", "`"] +\
                l('1234567890-=') + ["BACKSPACE"] +\
                ['TAB']+ l('QWERTYUIOP[]\\') +\
                ['CAPSLOCK']+l('ASDFGHJKL;\'') + ["Enter"] +\
                ['Left SHIFT'] + l('ZXCVBNM,./') + ['Right SHIFT'] +\
                ["Left CTRL", "Fn", "Win", "Left ALT", "SPACE"] +\
                ["Right ALT", "Context", "Right CTRL"] +\
                ['Up', 'Down', 'Left', 'Right'] +\
                ["Home", "Page Up", "Page Down", "End"]

intl_keys_to_press = copy(keys_to_press)

# Additional keys to press if the keyboard has a numpad
numpad_keys_to_press =  ["KP{}".format(i) for i in range(10)] +\
                        ["KPDOT", "KPENTER", "KPPLUS", "KPMINUS"] +\
                        ["KPMUL", "KPDIV", "NUMLOCK"]

# User-friendly names
key_translations = {".":"DOT", ",":"COMMA", "/":"SLASH", "'":"APOSTROPHE", "[":"LBRACE", "]":"RBRACE", \
                    "=": "EQUAL", "-":"MINUS", "`":"GRAVE", "\\":"BACKSLASH", ";":"SEMICOLON", "Left SHIFT":"LEFTSHIFT", \
                    "Right SHIFT":"RIGHTSHIFT", "Left ALT":"LEFTALT", "Right ALT":"RIGHTALT", "Win":"LEFTMETA", \
                    "Page Up":"PGUP", "Page Down":"PGDOWN", "#":"HASH", "+":"PLUS", "Å":"ARING", "^":"CARET", \
                    "Ö":"ODIAERESIS", "Ä":"ADIAERESIS","*":"ASTERISK", ">":"LESS"}


def info_normalize():
    for key, value in info.get("raw", {}).items():
        info["raw"][key] = key_translations.get(value, value).upper()
    for key, value in info.get("raw_fn_keys", {}).items():
        info["raw_fn_keys"][key] = key_translations.get(value, value).upper()

# questioning

def get_bool(key, question):
    current_value = {True:'y', False:'n', None:''}[info.get(key, None)]
    new_val = input("{} (y/n) [{}] ".format(question, current_value))
    while new_val:
        value = None
        if new_val.lower().startswith('y'):
            value = True
        elif new_val.lower().startswith('n'):
            value = False
        if value is not None:
            info[key] = value
            return
        else:
            print("Sorry, it's unclear to me. Please enter a [y/n] response.")
            new_val = input("{} y/n [{}]".format(question, current_value))

def get_int(key, question):
    current_value = info.get(key, "")
    new_val = input("{} (number) [{}] ".format(question, current_value))
    while new_val:
        try:
            info[key] = int(new_val)
            return
        except ValueError:
            print("Please enter a number!")
            new_val = input("{} (number) [{}] ".format(question, current_value))

def get_string(key, question):
    current_val = info.get(key, "")
    new_val = input("{} [{}] ".format(question, current_val))
    if new_val:
        info[key] = new_val

def get_metadata():
    print("Hey! I would appreciate if you helped by entering some info about your keyboard!\n")
    print("Some of this data will determine what the script will do. Other data will make this keyboard easier to find for others.")
    print("Ultimately, all of this data will be used to spot similarities between keyboards made,")
    print("so that we can create something really cool and cheap that works with a wide range of keyboards.\n")
    print("Now, let's begin. Skip any questions by pressing Enter.")
    # questions
    get_string("name", "What is the keyboard model number? There should be a label on the FPC or backside.\nCould be something like %MANUFACTURER% FRU %NUMBER%.")
    if " " in info["name"]:
        get_string("file_name", "Oh, that's good info! Thank you! Any short name that could be used for the datasheet filename?")
    get_string("lang", "Do you know the keyboard language? Maybe there's a language code on the label? I.e. US/UI/INTL/UK/SD/RU etc.")
    get_string("laptop_mfg", "Do you know the manufacturer of the laptop that this keyboard was used with?")
    get_string("laptop", "Do you know what laptop model this keyboard was used with?")
    # let's see if we can provide a manufacturer hint to the user
    if not info.get("keeb_mfg", ""):
        # Darfon heuristic - keyboard code starts with NSK-
        if "NSK-" in info.get("name", "") or info.get("file_name", "").startswith("NSK-"):
            print("This looks like a Darfon-manufactured keyboard!")
    get_string("keeb_mfg", "Any idea on the keyboard manufacturer? Could be someone like \"Chicony\" or \"Darfon\".")
    get_string("pitch", "What is the pin pitch on your FPC? I.e. 1mm/0.8mm/0.5mm/other.")
    get_int("pin_count", "What's the amount of pins on your keyboard's FPC?")
    get_int("fpc_offset", "Did you insert the keyboard into the connector with an offset? If so, enter the amount of pins that are unconnected (i.e. 1")
    get_bool("has_numpad", "Does your keyboard have a numpad?")
    get_bool("has_trackpoint", "Does your keyboard have a trackpoint?")
    get_bool("has_leds", "Does your keyboard have some LEDs embedded into the keys, i.e. CapsLock?")
    get_bool("has_backlight", "Does your keyboard have backlight on a separate FPC?")
    get_bool("has_power_button", "Does your keyboard have a power button?")
    # now processing the metadata
    process_metadata()

def get_basic_metadata():
    print("Let's enter some basic info about your keyboard so that the script knows how to best help you!\n")
    # questions
    get_string("lang", "Do you know the keyboard language? Maybe there's a language code on the label? I.e. US/UI/INTL/UK/SD/RU etc.")
    get_bool("has_numpad", "Does your keyboard have a numpad?")
    get_bool("has_leds", "Does your keyboard have some LEDs embedded into the keys, i.e. CapsLock?")
    get_bool("has_power_button", "Does your keyboard have a power button?")
    get_int("fpc_offset", "Did you insert the keyboard into the connector with an offset? If so, enter the amount of pins that are unconnected (i.e. 1")
    # now processing the metadata
    process_metadata()

def get_help_shorthand():
    return "(n/f/r/x/b/s/p/e/?)"

def help_offer():
    print("Press '?'+Enter on your PC's keyboard (or just Enter alone) to see available commands")

def show_help():
    print("Press 'n'+Enter if the key is Not present on your keyboard.")
    print("Press 'f'+Enter if the key is on a Fn layer.")
    print("Press 'r'+Enter if the key is bRoken on your keyboard and doesn't register.")
    print("Press 'x'+Enter to add an eXtra key. For a key that'd be called KEY_NAME, enter the NAME part.")
    print("Press 'b' to go Back one key in case you pressed one or more keys incorrectly.")
    print("Press 's' to Skip broken key re-scanning. (is a toggle)")
    print("Press 'p' to Print the current key again.")
    print("Press 'e' to End scanning.")
    print("Press '?' or just Enter to show this Help again")

def enter_key_name():
    key = input("Enter key name: ") # getting key name from user
    return key

def remove_key_from_data(key):
    removed = False
    while key in info["raw"].values():
        for k, v in info["raw"].items():
            if v == key:
                info["raw"].pop(k)
                removed = True
                break
    return removed

def remove_key_ui():
    key = enter_key_name()
    key = key_translations.get(key, key).upper()
    result = remove_key_from_data(key)
    print("Key removed!" if result else "Key not found!")

# setting things up from the metadata given

def process_metadata(lang=None):
    global keys_to_press

    def replace(l, old, new): # list helper
        index = l.index(old)
        l.pop(index)
        l.insert(index, new)

    # if the keyboard has a numpad, we need to add the stereotypical numpad keys
    # into the keys_to_press list that's used for interactive key mapping
    keys_to_press = copy(intl_keys_to_press)
    if info.get("has_numpad", False) and not all([key in keys_to_press for key in numpad_keys_to_press]):
        for key in numpad_keys_to_press:
            if key not in keys_to_press:
                keys_to_press.append(key)
    # if it's a UK/ND keyboard, we need to move a few keys places
    lang = info.get("lang", "") if lang is None else lang
    if lang == "UK":
        # moving the slash
        keys_to_press.remove('\\')
        slash_index = keys_to_press.index("Z")
        keys_to_press.insert(slash_index, '\\')
        # adding a hash key
        if '#' in keys_to_press: keys_to_press.remove('#')
        hash_index = keys_to_press.index("Enter")
        keys_to_press.insert(hash_index, '#')
    elif lang == "ND" or lang.lower() in ["swedish", "danish"]:
        # number row
        replace(keys_to_press, '-', '+')
        replace(keys_to_press, '=', '`')
        # first row
        replace(keys_to_press, '[', 'Å')
        replace(keys_to_press, ']', '^')
        keys_to_press.remove('\\')
        # second row
        replace(keys_to_press, ';', 'Ö')
        replace(keys_to_press, "'", 'Ä')
        asterisk_index = keys_to_press.index("Enter")
        keys_to_press.insert(asterisk_index, '*')
        # third row
        slash_index = keys_to_press.index("Z")
        keys_to_press.insert(slash_index, '>')
        replace(keys_to_press, "/", '-')
    # TODO: process more language codes

def print_lang_keys(lang):
    # a test function that creates keys-to-press for different languages
    global keys_to_press
    keys_to_press_backup = copy(keys_to_press)
    process_metadata(lang=lang)
    print(", ".join([repr(key) for key in keys_to_press]))
    keys_to_press = copy(keys_to_press_backup)

# Messages

welcome_msg = "Hello and welcome to KeyboardWhiz!"
version_msg = "Script version is v{__version__}".format(**globals())
console_msg = "If you ran the script like designed - at any point, feel free to press Ctrl+C to drop into a Python shell!"

scanning_msg_new = "Let's scan the keyboard quickly!"

def print_broken_keys():
  if info.get("broken_keys", []):
    print("This keyboard file has keys {} marked as broken".format(", ".join(info["broken_keys"])))

# hardware definitions

bus_num = 1

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

# "user input while scanning keys" functions

def stdin_has_char():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def stdin_readall():
    s = ''
    while stdin_has_char():
        s += sys.stdin.read(1)
    return s

# expander setup functions

def test_expander_presence():
    ep_addrs = list(set([a for _, a, i, p, r, w, _ in eps]))
    for ep_addr in ep_addrs:
      try:
        gmr(ep_addr, 0x00) # just reading some register
      except (NameError, IOError):
        print("WARNING: I can't find the expander at {}, bus {}!".format(hex(ep_addr), bus_num))

def setup_for_key_scanning():
    for _, a, i, p, r, w, _ in eps:
        smr(a, w, 0x00) # writing 0 to all pin latches
        smr(a, i, 0xff) # setting all pins as inputs
        smr(a, p, 0xff) # enabling all pullups
        #print(hex(a), gmr(a, r))

def setup_for_leds():
    for _, a, i, p, _, w, _ in eps:
        smr(a, w, 0xff) # writing ff to all pin latches
        smr(a, i, 0x00) # setting all pins as outputs
        smr(a, p, 0x00) # disabling all pullups

# I swear, this is going to be an object at some point! T___T

def scan_usual_keys(extra_keys = False):
 """ Interactive key picker """
 # init the GPIO expanders
 setup_for_key_scanning()

 # a few flags and shorthands
 expected_key_index = 0 # index in the list of the expected keys
 next_key_is_fn = False
 key_input_done = False
 skip_broken_keys = False
 if "raw" not in info:
    data = {} # dict that will have initial keyboard data
    info["raw"] = data
 else:
    data = info["raw"]
 time_of_last_press = time.time()

 # helpers
 def prompt_key(fn=False):
    if fn: print("[Fn] ", end='')
    shorthand = get_help_shorthand()
    message = "Press {}: ".format(keys_to_press[expected_key_index]) if not extra_keys else "Press your key: "
    print(shorthand, message, end='');sys.stdout.flush()

 def enter_key_name():
    key = input("Enter key name: ") # getting key name from user
    return key

 def get_last_pressed_key():
    last_pressed_key = keys_to_press[expected_key_index-1]
    return key_translations.get(last_pressed_key, last_pressed_key).upper()

 def go_back():
    nonlocal expected_key_index
    if expected_key_index:
        expected_key_index -= 1

 def advance_expected_key(increment_first=True):
    # on the very first key, when just starting the scanning,
    # we don't want to increment on the first iteration,
    # because that'd make the scanning always skip Esc
    nonlocal expected_key_index
    key_skipped = False # flag for output formatting and return value
    # this function is meaningless in extra key mode
    if extra_keys: return False
    # skip keys that are alreaady present in decoded data
    if increment_first:
        expected_key_index += 1
    if expected_key_index == len(keys_to_press):
        return None
    new_key = keys_to_press[expected_key_index]
    new_key_trans = key_translations.get(new_key, new_key).upper()
    skipped_keys = info.get("skipped_keys", [])
    fn_keys = info.get("raw_fn_keys", {}).values()
    broken_keys = info.get("broken_keys", [])
    while new_key_trans in info["raw"].values() \
      or new_key in skipped_keys \
      or new_key_trans in fn_keys \
      or (skip_broken_keys and new_key in broken_keys):
        expected_key_index += 1
        if not key_skipped:
            print("skipping key", new_key, end='')
            key_skipped = True
        else:
            print(",", new_key, end='')
        sys.stdout.flush()
        if expected_key_index == len(keys_to_press):
            return None
        new_key = keys_to_press[expected_key_index]
        new_key_trans = key_translations.get(new_key, new_key).upper()
    if key_skipped: # reusing this as "a key has been skipped" flag
        print() # newline so that the new prompt is printed well
        return True
    # no key has been skipped
    return False

 def remove_key_from_broken(key):
    # this function is meaningless in extra key mode
    if extra_keys: return False
    while key in info.get("broken_keys", []):
        info["broken_keys"].remove(key)
        print("Key {} no longer marked as broken!".format(key))

 def scan_for_shorts():
  info["shorted_pins"] = []
  for y, a, i, _, _, w, s1 in eps: # for each expander port
    for b in range(8): # picking one pin on the expander
      smr(a, i, 1<<b^0xFF) # setting one pin on the expander as input
      for z, ax, _, _, rx, _, s2 in eps: # for each expander port (again)
        d = gmr(ax, rx) # read the port
        if z == y: # if it's the same port where pin is being enabled,
          d |= 1<<b # ignore the pin that's being enabled
        d = d ^ 0xFF # invert the port, since we're doing 'active low' logic
        if d != 0x00: # we got some pins set on this port!
            for n in range(8): # going through each bit,
              if d & (1 << n): # if any bit is set
                d1 = pin_mapping.index(s1+str(b)) # port and bit which we have set - get the pin number
                d2 = pin_mapping.index(s2+str(n)) # port and bit where we got a response - get the pin number
                d1, d2 = sorted([d1, d2]) # sort the pin numbers - so that connection between 1,2 and 2,1 is interpreted as the same connection
                fpc_offset = info.get("fpc_offset", 0)
                d1 -= fpc_offset
                d2 -= fpc_offset
                id = "{}-{}".format(d1, d2) # string ID for easily storing and looking up keys using a dictionary
                info["shorted_pins"].append(id)
                print("Pins {} and {} appear to be shorted together!".format(d1, d2))
                time.sleep(0.1)
      smr(a, i, 0xFF) # after each port bit has been scanned, set all pins to zero (TODO: optimize so that this only gets done after the port is scanned (TODO: check if this is a valid todo at all))

 # Start of interaction with the user
 if new_file: print(scanning_msg_new)
 print_broken_keys()

 if advance_expected_key(increment_first=False) is None and not extra_keys:
    # an out of keys!
    print(''); return info
 scan_for_shorts()
 help_offer()
 prompt_key()
 # main loop: infinite, breaks on 'return' statements
 while True:
  for y, a, i, _, _, w, s1 in eps: # for each expander port
    for b in range(8): # picking one pin on the expander
      smr(a, i, 1<<b^0xFF) # setting one pin on the expander as input
      for z, ax, _, _, rx, _, s2 in eps: # for each expander port (again)
        d = gmr(ax, rx) # read the port
        if z == y: # if it's the same port where pin is being enabled,
          d |= 1<<b # ignore the pin that's being enabled
        d = d ^ 0xFF # invert the port, since we're doing 'active low' logic
        if d != 0x00: # we got some pins set on this port!
            for n in range(8): # going through each bit,
              if d & (1 << n): # if any bit is set
                d1 = pin_mapping.index(s1+str(b)) # port and bit which we have set - get the pin number
                d2 = pin_mapping.index(s2+str(n)) # port and bit where we got a response - get the pin number
                d1, d2 = sorted([d1, d2]) # sort the pin numbers - so that connection between 1,2 and 2,1 is interpreted as the same connection
                #print(d1, d2)
                fpc_offset = info.get("fpc_offset", 0)
                d1 -= fpc_offset
                d2 -= fpc_offset
                #print(d1, d2)
                id = "{}-{}".format(d1, d2) # string ID for easily storing and looking up keys using a dictionary
                if not extra_keys:
                  key = keys_to_press[expected_key_index] # key we currently expect
                  key_trans = key_translations.get(key, key).upper() # key shown to the user is a bit different
                else:
                  key_trans = key = "your key" # for UI message purposes
                if id in info["shorted_pins"]:
                  # just ignore
                  pass
                elif next_key_is_fn:
                  if not "raw_fn_keys" in info: info["raw_fn_keys"] = {}
                  if extra_keys: key_trans = key = enter_key_name()
                  info["raw_fn_keys"][id] = key_trans
                  if not extra_keys: advance_expected_key()
                  next_key_is_fn = False
                  time_of_last_press = time.time()
                  if expected_key_index == len(keys_to_press) and not extra_keys: # we ran out of keys here
                      print(''); return info # TODO: refactor out and reuse the loop-beginning check somehow?
                  if id not in data:
                      # whoops, this key id is not registered in the non-fn layer yet
                      print('Ok, now please release {} really quickly! =D'.format(key));
                      time.sleep(1.5)
                  else: print('')
                  key_input_done = True
                  prompt_key()
                elif id not in data and info.get("raw_fn_keys", {}).get(id) != key_trans: # key has not yet been saved
                  if extra_keys: key_trans = key = enter_key_name()
                  remove_key_from_broken(key)
                  data[id] = key_trans
                  advance_expected_key()
                  time_of_last_press = time.time()
                  if expected_key_index == len(keys_to_press) and not extra_keys: # we ran out of keys here
                      print(''); return info # TODO: refactor out and reuse the loop-beginning check somehow?
                  print(''); prompt_key()
                elif not key_input_done: # key is already known
                  try:
                    key = data.get(id, info.get("raw_fn_keys", {}).get(id)) # shorthand for ease of coding
                  except KeyError:
                    print("Whoops, key {} determined as known but present in neither regular nor Fn layers?".format(id))
                    print("That is weird, please do let me know about this!")
                  else:
                    last_pressed_key = get_last_pressed_key()
                    time_since_last_press = time.time() - time_of_last_press
                    #print(last_pressed_key)
                    if (time_since_last_press > 1.5) and key != "IGNORE": # IGNOREd keys won't be shown when pressed
                        print("{} already pressed, is {}!".format(id, key)) # print the pressed keys for informational purposes
                    remove_key_from_broken(key)
                key_input_done = False
       # checking stdin
        if stdin_has_char():
            s = stdin_readall().strip()
            # we got some input from the user!
            #print(repr(s))
            if s == 'n': # no such key
                key = keys_to_press[expected_key_index]
                print("Skipping key", key, end='')
                if "skipped_keys" not in info:
                    info["skipped_keys"] = []
                if key_trans not in info["skipped_keys"]: info["skipped_keys"].append(key_trans)
                if advance_expected_key() is None and not extra_keys: # we ran out of keys!
                    print(''); return info
                print(''); prompt_key()
                next_key_is_fn = False
            elif s == 'f': # Fn layer key
                next_key_is_fn = True
                prompt_key(fn=True)
            elif s == 'r': # broken key
                key = keys_to_press[expected_key_index]
                if "broken_keys" not in info:
                    info["broken_keys"] = []
                if key not in info["broken_keys"]: info["broken_keys"].append(key)
                if advance_expected_key() is None and not extra_keys: # we ran out of keys!
                    print(''); return info
                prompt_key()
                next_key_is_fn = False
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
                print(last_pressed_key)
                remove_key_from_data(last_pressed_key)
                go_back()
                prompt_key()
                next_key_is_fn = False
            elif s == 's': # skip broken keys - toggle
                skip_broken_keys = not skip_broken_keys
                if advance_expected_key(increment_first=False) is None and not extra_keys: # we ran out of keys!
                    print(''); return info
            elif s == 'p': # prompt
                print(''); prompt_key()
            elif s == 'e': # exit
                print(''); return info
            elif s in ('?', ''):
                show_help()
            else:
                print("Unrecognized command! Use ? for help.")
        #time.sleep(0.1)
      smr(a, i, 0xFF) # after each port bit has been scanned, set all pins to zero (TODO: optimize so that this only gets done after the port is scanned (TODO: check if this is a valid todo at all))

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

def scan(**kwargs):
  process_metadata()
  scan_usual_keys(**kwargs)

def process_raw_data():
    get_rc_mapping()
    get_table()

def get_rc_mapping():
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

def get_table():
    a1 = sorted(info["a1"]); a2 = sorted(info["a2"])

    if len(a1) >= len(a2):
        rows = a2; columns = a1
    else:
        rows = a1; columns = a2

    info["rows"] = rows
    info["columns"] = columns

    print(len(rows), "rows:", rows)
    print(len(columns), "columns:", columns)

    # pin table
    table = dict([[row, {}] for row in rows])
    for a1, a2, key in info["rc_mapping"]:
        #print(a1, a2, key)
        rnum = a1 if a1 in rows else a2
        cnum = a1 if a1 in columns else a2
        try:
            table[rnum][cnum] = key
        except KeyError:
            t = "rows" if a1 in rows else "columns"
            print("Key {} placement weirdness: both {} and {} are {}! Skipping".format(key, a1, a2, t))
    info["table"] = table

# Loading the file or creating a new one

def save_file():
    with open(filename, 'w') as f:
        json.dump(info, f)

save = save_data = save_file

def load_file(filename):
    global info
    with open(filename, 'r') as f:
        info = json.load(f)
    info_normalize()

# Main UI stuff starts here

def print_filename():
    print("Current file is", filename)

def exit():
    if not last_action_was_save:
        r = input("Save before exiting? (Y/n) ")
        if not r or r.lower().startswith('y'):
            save()
    print_filename()
    sys.exit(0)

    # name, callback, do_not_print
menu_entries = [
    ["Input basic data about the keyboard", get_basic_metadata, False],
    ["Scan keys", scan, False],
    ["Remove keys", remove_key_ui, False],
    ["Add keys", lambda: scan(extra_keys=True), False],
    #["Scan LEDs", scan_leds],
    ["Process data", process_raw_data, True],
    ["Input more data about the keyboard", get_metadata, False],
    ["Save", save, True],
    ["Exit", exit, True],
    #["Generate PDF", generate_pdf]
]

# for removing redundant 'wanna save' on exit if you've just saved the data
last_action_was_save = False

def main_menu():
    global last_action_was_save
    do_not_print = False
    def get_entry_num():
        while True:
            try:
                num = input("> ")
                num = int(num)
            except KeyboardInterrupt:
                return None
            except ValueError:
                pass
            else:
                if num in range(len(menu_entries)):
                    return num
    while True:
        if not do_not_print:
            for i, entry in enumerate(menu_entries):
                print("{}: {}".format(i, entry[0]))
        num = get_entry_num()
        if num is None: # ctrlc menu exit
            return
        try:
            menu_entries[num][1]()
        except KeyboardInterrupt:
            pass
        except SystemExit:
            return
        except:
            traceback.print_exc()
        finally:
            do_not_print = menu_entries[num][2]
            if not do_not_print:
                print("-"*20)
            last_action_was_save = menu_entries[num][1] == save

def main():
    print(welcome_msg)
    print(version_msg)
    print(console_msg)

    # first run

    if new_file:
        # Let's scan this keyboard quickly!
        print_filename()
        try:
            get_basic_metadata()
            scan()
        except KeyboardInterrupt:
            pass
        except:
            traceback.print_exc()

    main_menu()

if __name__ == "__main__":

    try:
        bus = smbus.SMBus(bus_num)
    except (PermissionError, IOError, FileNotFoundError):
        print("WARNING: I can't open bus {}!".format(bus_num))
        #traceback.print_exc()
    else:
        test_expander_presence()

    # Creating the directory if it doesn't exist
    try:
        os.mkdir('keebs/')
    except FileExistsError:
        pass

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        try:
            load_file(filename)
        except:
            print("Creating new file: {}".format(filename))
            info = {}
            new_file = True
        else:
            print("Loaded {}".format(filename))
            new_file = False
    else:
        ts = datetime.strftime(datetime.now(), "%y%m%d_%H%M%S")
        filename = "keebs/keeb_{}.json".format(ts)
        info = {}
        new_file = True

    main()

"""
setup_for_leds()
light_leds()
"""
