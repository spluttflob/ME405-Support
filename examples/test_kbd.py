""" @file test_kbd.py
    This file contains code to verify that the @c keyboard module works.

    This module must be installed with a command such as
    @code
    pip3 install keyboard
    @endcode
    before use (and maybe use @c sudo or @c su if you're on Unix or Linux).

    On Linux, this program must be run as root because security.  On Windows,
    there is no security.  On MacOS, there's security but I'm not sure if it 
    must be run as root; check @c https://github.com/boppreh/keyboard for more
    information. 

    @author jr
    @date Mon Jan 11 18:52:02 2021
        
"""

import keyboard


pushed_key = None

def on_keypress (thing):
    """ Callback which runs when the user presses a key.
    """
    global pushed_key

    pushed_key = thing.name


if __name__ == "__main__":

    dimes = 0                # Pursue a career in accounting

    keyboard.on_press (on_keypress)  ########## Set callback

    # Run a simple loop which responds to some keys and ignores others.
    # If someone presses control-C, exit this program cleanly
    while True:
        try:
            # If a key has been pressed, check if it's a key we care about
            if pushed_key:
                if pushed_key == "0":
                    print ("This is worth a cent")

                elif pushed_key == '1':
                    print ("Non-wooden nickel detected")

                elif pushed_key == '2':
                    dimes += 1
                    print ("We're up to our {:d}th dime".format (dimes))

                elif pushed_key == 'e':
                    print ("I've seen an 'E'")

                pushed_key = None

        # If Control-C is pressed, this is sensed separately from the keyboard
        # module; it generates an exception, and we break out of the loop
        except KeyboardInterrupt:
            break

    print ("Control-C has been pressed, so it's time to exit.")
    keyboard.unhook_all ()

