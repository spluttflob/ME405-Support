"""!
@file what_you_said.py
This file contains a simple demonstration of how a MicroPython board can
interact with a person using a PC, or with a Python program running on a PC,
through a USB-Serial interface.

This file is to be run on a MicroPython board. If you're using it to test a
PC python program, you'll probably want to save this file as main.py and copy
it to the MicroPython board, then restart the board with a Ctrl-D, so that this
program keeps running regardless of whether Thonny or PuTTY is active.

Once this program is running on the MicroPython board, you can start Python on 
the PC (either running in a REPL or running a program you've written) to send
some strings to the MicroPython board, stop the PC Python program, switch to a 
terminal program such as PuTTY, and see what the PC Python program sent to the
microcontroller. 

Example commands running on the PC include the following, shown as if you type
them at the REPL:

    >>> import serial
    >>> serpt = serial.Serial ("COM42", 115200)    # or "/dev/tty<something>"
    >>> serpt.write (b"Something\r\n")             # "\r\n" is carriage return
    >>> serpt.close ()                             # Close serial port
    >>> exit ()                                    # Exit PC Python REPL

@author    JR Ridgely
@date      2022-Jan-28
@copyright (c) 2022 by JR Ridgely. Released under a CC-BY-NC-SA 3.0 license.
           Anyone may use it freely but must also share it freely and must
           acknowledge where it came from.
"""


def main ():
    """!
    @brief   Function which receives text from a user and saves it in a list.
    @details The user might be a person or a program; this function is a really
             bad Turing tester because it doesn't know or care with whom or
             what it is interacting.
    """
    print ("Please send me strings, each followed by a newline b'\\n'.")

    sent_to_me = []               # Store what was sent in a list of strings

    while True:
        try:
            # Whoever's at the other end of the serial line should send a
            # string. If it's a program, we could leave the parameter to
            # input() blank so extraneous (not useful data) text isn't sent
            # to the PC program
            a_string = input ("Well? ")
            sent_to_me.append (a_string)

            # Show the current list of numbers
            print (sent_to_me)

        except KeyboardInterrupt:
            break

    print ()
    print ("The final list of strings:")
    print (sent_to_me)


if __name__ == "__main__":
    main ()
