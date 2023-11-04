"""!
@file test_cqueue.py
This file contains code to test the classes in the cqueue C module.

This file must be used with a version of MicroPython 
"""
import gc
import cqueue
import utime
import random
from micropython import const

TEST_SIZE = const (2000)


def main(run_number):
    """!
    Run the test.
    @param run_number The number in a sequence of runs of this test
    """
    # Say hello and make sure memory is as cleanly set up as possible
    gc.collect ()
    print ('')
    print (f"Memory before allocation: {gc.mem_free ()}")

    # Create the queues, allocating memory for the data
    inky = cqueue.IntQueue (TEST_SIZE)
    foof = cqueue.FloatQueue (TEST_SIZE)

    # Create lists to hold results of tests
    int_durs = []
    float_durs = []
    none_durs = []

    for index in range (TEST_SIZE):
        dur = 0
        begin = 0

        to_ink = index + 1
        begin = utime.ticks_us ()
        inky.put (to_ink)
        dur = utime.ticks_diff (utime.ticks_us (), begin)
        int_durs.append (dur)

        to_foof = float (index + 1)
        begin = utime.ticks_us ()
        foof.put (to_foof)
        dur = utime.ticks_diff (utime.ticks_us (), begin)
        float_durs.append (dur)

        begin = utime.ticks_us ()
        dur = utime.ticks_diff (utime.ticks_us (), begin)
        none_durs.append (dur)

    count = 0
    while inky.any() and foof.any():
        count += 1
        ink0 = inky.get()
        foof0 = foof.get()
        if ((float (ink0) - foof0) / foof0) > 0.001:
            print (f"Error: {ink0} != {foof0}")

    print (f"Memory after test run #{run_number}: {gc.mem_free ()}")
    print (f"Ints:   Num {len(int_durs)},"
           + f" Avg {sum(int_durs) / len(int_durs):.1f},"
           + f" Max {max (int_durs)}")
    print (f"Floats: Num {len(float_durs)},"
           + f" Avg {sum(float_durs) / len(float_durs):.1f},"
           + f" Max {max (float_durs)}")
    print (f"Nones:  Num {len(none_durs)},"
           + f" Avg {sum(none_durs) / len(none_durs):.1f},"
           + f" Max {max (none_durs)}")


for count in range (100):
    try:
        main(count + 1)
        utime.sleep_ms (200)
    except KeyboardInterrupt:
        break

print ("Test complete.")
