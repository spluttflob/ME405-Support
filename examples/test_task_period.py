"""!
@file test_task_period.py
This file tests the new method @c cotask.Task.set_period(). It allows the user
to change the period at which Task 0 runs and watch the results as the rate at
which printouts appear.

@author JR Ridgely
@date   2022-Feb-07 JRR Original file
@copyright (c) 2022 by JR Ridgely and released under the GNU Public License,
        version 3.0. 
"""

import gc
import pyb
import cotask
import task_share


def task0_fun ():
    """!
    Task which prints junk slowly.
    """
    counter = 0
    while True:
        print (counter)
        counter += 1
        yield 0


def task_luser ():
    """!
    Task which lets the (l)user interact with a running test program.
    """
    vcp = pyb.USB_VCP ()
    task_period = 1000
    while True:
        if vcp.any ():
            vcp.read ()
            task_period += 1000
            task0.set_period (task_period)
            print (f"Period now {task_period}")
        yield 0


# The test code runs the two tasks, letting the user change the rate at which
# the first task runs. 
if __name__ == "__main__":
    
    print ("\033[2JTesting cotask.py task period hacking")
    
    task0 = cotask.Task (task0_fun, name = 'Task 0', priority = 2, 
                         period = 1000, profile = True, trace = False)
    cotask.task_list.append (task0)

    taskL = cotask.Task (task_luser, name = 'Luser', priority = 1, 
                         period = 100, profile = False, trace = False)
    cotask.task_list.append (taskL)

    while True:
        try:
            cotask.task_list.pri_sched ()
        except KeyboardInterrupt:
            break

    # The task printout will be a bit weird because the period shown for Task 0
    # is the period at which it was running when the program exited 
    print ('\n' + str (cotask.task_list))
