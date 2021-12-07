""" @file vend_kb.py
    This file contains an example of using the @c keyboard module to read PC
    keys without blocking the rest of a program.
"""

import keyboard 

last_key = ''

def kb_cb(key):
    """ Callback function which is called when a key has been pressed.
    """
    global last_key
    last_key = key.name

# Tell the keyboard module to respond to these particular keys only
keyboard.on_release_key("c", callback=kb_cb)
keyboard.on_release_key("p", callback=kb_cb)

# Run this loop forever, or at least until someone presses control-C
while True:
    if last_key == 'c':
        last_key = ''
        print("You want a Cuke?")
    elif last_key == 'p':
        last_key = ''
        print("You want a Popsy?")

    # Other code could run here; it won't be blocked by waiting for keys

