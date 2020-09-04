import smbus
import time

from copy import copy
from collections import OrderedDict

bus = smbus.SMBus(1)
a1 = 0x21
a2 = 0x22

# MCP23017 register descriptions
       #i  a   io    pu   read  write, str
ep = ( (0, a1, 0x00, 0xc, 0x12, 0x14, "2A"), \
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

"""data = {'1A72B4': 'D', '1A72B6': 'S', '1A01A6': 'RTRIANGLE', '1A71B6': 'K', '1A01A3': 'ENTER', \
'1A71B5': 'COLON', '1A21A4': 'RALT', '1B02A4': 'Q', '1B02A2': 'U', '1B02A3': 'R', '1B02A0': 'PGUP', \
'1A31A7': 'SLASH', '1A72A1': 'FN', '1A72A2': 'J', '1A31A4': 'SPACE', '1A61B1': 'F7', \
'1A61B0': 'O', '1A41A5': 'RIGHT', '1A61A7': 'L', '1A51A7': 'WIN', '1A02A4': 'Z', '1B42B7': 'END', \
'1B42B5': 'HOME', '1A02A2': 'M', '1B72B7': 'F11', '2B52B6': 'F1', '1B11B6': 'RBRACE', '2A32B5': '5', \
'2A32B7': '4', '2B42B5': 'F2', '1A11A3': 'F5', '1A11A2': 'LALT', '1A02B4': 'C', '1A02B6': 'X', \
'1A22B7': 'PRINTSCREEN', '1B72B5': 'DELETE', '1B02B6': 'W', '1B02B4': 'E', '1A12A2': 'H', \
'1A11B4': 'UP', '1A11B5': 'QUOTE', '1A11B6': 'F6', '1A41B7': 'DOWN', '1A41B5': 'DOT', \
'1A41B4': 'LEFT', '1B32B5': 'LCTRL', '2B62B7': '2', '2A22B7': '7', '2A22B5': '6', '1A52B7': 'F12', \
'1A12A3': 'G', '1A52B5': 'INSERT', '1A12A4': 'ESC', '1A01B6': 'LTRIANGLE', '1A01B4': 'PAUSE', \
'1A01B3': 'RCTRL', '1A01B2': 'RSHIFT', '1A62B7': '9', '1A62B5': 'F8', '1B62B5': 'EQUAL', \
'1B62B7': '8', '1A72A0': 'PGDN', '1A02A3': 'V', '1B01B5': 'P', '1B01B6': 'I', '1A72A3': 'F', \
'1B52B5': 'MINUS', '1B52B7': '0', '1A72A4': 'A', '1A31B1': 'BACKSPACE', '1B12A3': 'T', \
'1B12A2': 'Y', '1B12A4': 'TAB', '1A32B5': 'F9', '1A32B7': 'F10', '1B11B2': 'LSHIFT', \
'2B42B7': '3', '1B11B5': 'LBRACE', '1B11B4': 'CONTEXT', '2A42B5': 'TILDE', '2A42B7': '1', \
'1A12B4': 'F4', '1A42A3': 'B', '1A42A2': 'N', '1B12B4': 'F3', '1A21B0': 'NUMLK', '1B12B6': 'CAPS'}"""

#small acer PK1306F01U0
#data = {'1A31A7': 'F10', '1A72A0': '5', '1A22A5': 'DOWN', '1A22A4': 'LEFT', '1B22A4': 'LCTRL', '1A22A1': 'PGDN', '1A01A7': 'ESC', '1B72A4': 'SPACE', '1A71B6': '9', '1A71B7': '7', '1B52A4': 'M', '1A71B5': 'PLUS', '1A02A5': 'CAPSLOCK', '1B62A5': 'B', '1A21A7': 'INSERT', '1A02A1': 'F1', '1B62A1': 'J', '2A42A7': 'FN', '2A12A7': 'A', '2A02A5': 'X', '1A12A4': 'F7', '1B72A1': 'G', '2A02A1': 'F', '1B02A1': 'RSHIFT', '1A02A4': 'F6', '1A12A1': 'F4', '1B72A5': 'C', '1B42A4': 'CONTEXT', '1A12A5': '1', '1B52A5': 'COMMA', '1A32A5': 'PRINTSCREEN', '1A32A4': 'PAUSE', '1A11A7': 'F11', '1B21B3': 'IGNORE', '1B52A1': 'L', '2A22A5': 'RALT', '2A22A4': 'LALT', '1A32A1': '2'}

# Large Asus KB MP-10A73SU6886
#data = {'1B22A1': '2', '1B22A2': 'W', '1B22A6': 'Z', '1B22A7': 'ESC', '1A71B6': 'KP8', '1A71B4': 'F9', '1B31B6': 'FN', '2A42A6': 'N', '2A42A7': 'J', '2A02A6': 'LALT', '1B02A5': 'C', '1B02A3': 'RSHIFT', '1B02A0': 'RALT', '1B32A1': '1', '1B32A7': 'A', '1B32A6': 'KP0', '1A61B4': 'T', '1A72A2': 'LEFT', '1A61B6': 'G', '1A61B0': 'V', '1A72A7': 'CONTEXT', '1A52A6': 'DOWN', '1A52A7': 'L', '2A32A6': 'LSHIFT', '1A52A2': 'F11', '1A52A1': '9', '1A62A2': 'R', '1A62A1': '4', '1A62A7': 'F', '1A62A6': 'B', '2A22A4': 'U', '2A22A5': 'KP1', '1A02A7': 'KP6', '1A02A6': 'F8', '1A02A1': 'KP4', '1A02A2': 'KP5', '2A52A7': 'KPSLASH', '2A52A6': 'KPMINUS', '1B41B5': 'WIN', '1A51B0': 'DOT', '1B21B6': 'F2', '1A51B4': 'O', '1B02A4': 'M', '1B21B4': 'F1', '1B21B7': 'S', '1A51B6': 'RSLASH', '1A51B7': 'F10', '1A32A6': 'KPASTERISK', '1B51B7': 'KP7', '1B51B6': 'KP9', '2A12A4': '7', '1A11B4': 'END', '1A11B6': 'PRINTSCREEN', '1A11B7': 'EQUALS', '1A11B0': 'QUOTE', '1B31B4': 'TAB', '1B31B7': 'TILDE', '1A41B0': 'KPENTER', '1A41B7': 'CAPSLOCK', '1A41B6': 'E', '1A41B4': 'F4', '1A12A2': 'RBRACE', '1A12A1': 'BACKSPACE', '1A12A6': 'ENTER', '1A12A7': 'D', '1A01B7': 'DELETE', '1A01B6': 'RIGHT', '1A01B4': 'PAUSE', '1B72A5': 'KP3', '1B72A4': '6', '1B52A7': 'NUMLOCK', '1B52A1': 'HOME', '1B52A2': 'PAGEUP', '1A22A6': 'LCTRL', '1B01B1': 'SLASH', '1B01B2': 'X', '1B01B3': 'Q', '1A61B7': '5', '1B62A4': 'H', '1B62A5': 'KPPLUS', '1A31B6': 'F7', '1A31B7': 'F5', '1A31B4': 'F6', '1A31B0': 'COMMA', '1B12A1': 'P', '1B12A2': 'LBRACE', '1B12A7': 'COMMA', '1B12A6': 'UP', '1B11B7': '0', '1B11B6': 'MINUS', '1B11B4': 'F12', '2A12A5': 'KPDOT', '1A32A7': 'K', '1A32A1': '8', '1A32A2': 'I', '1A42A1': '3', '1A42A2': 'F3', '1A42A7': 'PAGEDOWN', '1A42A6': 'SPACE', '1A21B0': 'RCTRL', '1B42A4': 'Y', '1B42A5': 'KP2'}
data = {'8-21': 'KP0', '8-20': 'A', '1-15': 'EQUALS', '1-14': 'PRINTSCREEN', '1-17': 'BACKSPACE', '9-20': 'ESC', '9-21': 'Z', '1-12': 'END', '3-18': 'I', '1-18': 'RBRACE', '7-18': 'F3', '7-17': '3', '8-17': '1', '7-15': 'CAPSLOCK', '8-15': 'TILDE', '8-12': 'TAB', '7-12': 'F4', '7-11': 'KPENTER', '4-20': 'CONTEXT', '11-9': 'X', '11-8': 'Q', '16-21': 'LALT', '6-20': 'L', '6-21': 'DOWN', '1-11': 'QUOTE', '7-20': 'PAGEDOWN', '7-21': 'SPACE', '4-12': 'F9', '4-14': 'KP8', '5-20': 'F', '5-21': 'B', '4-18': 'LEFT', '17-22': 'KPDOT', '17-23': '7', '23-21': 'N', '23-20': 'J', '2-21': 'LCTRL', '11-16': 'RALT', '11-10': 'SLASH', '11-19': 'RSHIFT', '9-18': 'W', '9-15': 'S', '9-14': 'F2', '9-17': '2', '9-12': 'F1', '22-20': 'KPSLASH', '22-21': 'KPMINUS', '3-21': 'KPASTERISK', '13-20': 'NUMLOCK', '3-12': 'F6', '3-11': 'COMMA', '3-17': '8', '3-15': 'F5', '3-14': 'F7', '0-21': 'F8', '0-20': 'KP6', '12-23': 'Y', '12-22': 'KP2', '5-11': 'V', '5-12': 'T', '5-15': '5', '5-14': 'G', '5-17': '4', '5-18': 'R', '0-17': 'KP4', '0-14': 'RIGHT', '0-15': 'DELETE', '0-12': 'PAUSE', '1-20': 'D', '1-21': 'ENTER', '0-18': 'KP5', '3-20': 'K', '19-21': 'LSHIFT', '10-12': 'F12', '10-17': 'P', '10-14': 'MINUS', '10-15': '0', '10-18': 'LBRACE', '11-22': 'C', '11-23': 'M', '18-23': 'U', '18-22': 'KP1', '14-23': 'H', '14-22': 'KPPLUS', '6-11': 'DOT', '6-12': 'O', '6-14': 'RSLASH', '6-15': 'F10', '6-17': '9', '6-18': 'F11', '13-17': 'HOME', '13-15': 'KP7', '13-14': 'KP9', '8-14': 'FN', '13-18': 'PAGEUP', '7-14': 'E', '10-21': 'UP', '10-20': 'COMMA', '12-13': 'WIN', '2-11': 'RCTRL', '15-22': 'KP3', '15-23': '6'}

#data = {}

new_data = {}
for key, value in data.items():
    if "-" not in key:
        key = "-".join([str(pin_mapping.index(pos)) for pos in sorted([key[:3], key[3:]])])
    new_data[key] = value
if new_data:
    print("Data has been converted to new format!")
    data = new_data
    print(data)

"""for _, a, i, p, _, w, _ in ep:
  smr(a, i, 0xff)
  smr(a, w, 0x00)
  smr(a, p, 0xff) # enabling all pullup

def main_loop():
 while True:
  for y, a, i, _, _, w, s1 in ep: # for each expander port
    for b in range(8): # picking one pin on the expander
      smr(a, i, 1<<b^0xFF) # enabling one pin on the expander
      for z, ax, _, _, rx, _, s2 in ep: # for each expander port (again)
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
                  key = raw_input("Enter key for {}: ".format(id)) # getting key name from user
                  if key: # Key has been input
                    data[id] = key # saving it in the dictionary
                else: # key is already known
                  key = data[id] # shorthand for ease of coding
                  if key != "IGNORE": # IGNOREd keys won't be shown when pressed
                      print("{} already pressed, is {}!".format(id, key)) # print the pressed keys for informational purposes
        #time.sleep(0.01)
      smr(a, i, 0xFF) # after each port bit has been scanned, set all pins to zero (TODO: optimize so that this only gets done after the port is scanned)

def main():
  try:
    main_loop()
  except KeyboardInterrupt:
    print(data)

main()
"""

############################
# Now, processing the resulting changes:
# finding out which pins would be rows and which would be columns
############################

rc_mapping = []
# assemble rows and columns from the data we got
a1 = []; a2 = []
# get ourselves a copy of the data so that we can iterate over it and remove elements one by one
rc_data = copy(data)

# The loop's purpose is to sort columns apart from rows while not confusing them

# get the first pin pair as a "boostrap" pair for the while loop, assign first pin to a1 and second pin to a2
key, value = data.items()[0]
d1, d2 = [int(c) for c in key.split('-')]
a1.append(d1); a2.append(d2)
rc_data.pop(key)
changes_made = True
while changes_made:
    changes_made = False
    for key, value in data.items():
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

rc_mapping = list(set(rc_mapping))
a1 = sorted(a1); a2 = sorted(a2)
print(a1, a2)
if rc_data:
    print("Unsorted pins: ", str(rc_data))

if len(a1) >= len(a2):
    rows = a2; columns = a1
else:
    rows = a1; columns = a2

# pin table
table = OrderedDict([[row, OrderedDict()] for row in rows])
for a1, a2, key in rc_mapping:
    rnum = a1 if a1 in rows else a2
    cnum = a1 if a1 in columns else a2
    table[rnum][cnum] = key
