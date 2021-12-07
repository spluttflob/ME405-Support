## @file print_task.py
#  This file contains code for a task which prints things from a queue. It
#  helps to reduce latency in a system having tasks which print because it
#  sends things to be printed out the serial port one character at a time,
#  even when other tasks put whole strings into the queue at once. When run
#  as a low-priority task, this allows higher priority tasks to interrupt
#  the printing between characters, even when all the tasks are being 
#  cooperatively scheduled with a priority-based scheduler. 
#
#    Example code:
#    @code
#    # In each module which needs to print something:
#    import print_task
#
#    # In the main module or wherever tasks are created:
#    shares.print_task = print_task.PrintTask (name = 'Printing', 
#        buf_size = 100, thread_protect = True, priority = 0)
#    cotask.task_list.append (shares.print_task)
#
#    # In a task which needs to print something:
#    shares.print_task.put ('This is a string')
#    shares.print_task.put_bytes (bytearray ('A bytearray'))
#    @endcode
#
#  @copyright This program is copyrighted by JR Ridgely and released under the
#  GNU Public License, version 3.0. 

import pyb
import cotask
import task_share

## The size of the buffer which will hold characters to be printed when the
#  print task has time to print them. 
BUF_SIZE = const (100)

## A flag which is passed to the queue constructor to control whether the 
#  queue will protect puts and gets from being corrupted by interrupts. 
THREAD_PROTECT = True

## A flag which controls if the printing task is to be profiled
PROFILE = True


#@micropython.native
def put (a_string):
    """ Put a string into the print queue so it can be printed by the 
    printing task whenever that task gets a chance. If the print queue is
    full, characters are lost; this is better than blocking to wait for
    space in the queue, as we'd block the printing task and space would
    never open up. When a character has been put into the queue, the @c go()
    method of the print task is called so that the run method will be called
    as soon as the print task is run by the task scheduler. 
    @param a_string A string to be put into the queue """

    for a_ch in a_string:
        if not print_queue.full ():
            print_queue.put (ord (a_ch))
            print_task.go ()


#@micropython.native
def put_bytes (b_arr):
    """ Put bytes from a @c bytearray or @c bytes into the print queue. When 
    characters have been put into the queue, the @c go() method of the print
    task is called so that the run method will be called as soon as the print 
    task is run by the task scheduler. 
    @param b_arr The bytearray whose contents go into the queue """

    for byte in b_arr:
        if not print_queue.full ():
            print_queue.put (byte)
            print_task.go ()


def run ():
    """ Run function for the task which prints stuff. This function checks for
    any characters to be printed in the queue; if any characters are found 
    then one character is printed, after which the print task yields so other 
    tasks can run. This functino must be called periodically; the normal way 
    is to make it the run function of a low priority task in a cooperatively 
    multitasked system so that the task scheduler calls this function when 
    the higher priority tasks don't need to run. 
    """

    while True:
        # If there's a character in the queue, print it
        if print_queue.any ():
            print (chr (print_queue.get ()), end = '')

        # If there's another character, tell this task to run again ASAP
        if print_queue.any ():
            print_task.go ()

        yield (0)


## This queue holds characters to be printed when the print task gets around
#  to it.
global print_queue
print_queue = task_share.Queue ('B', BUF_SIZE, name = "Print_Queue", 
                        thread_protect = THREAD_PROTECT, overwrite = False)

## This is the task which schedules printing. 
global print_task
print_task = cotask.Task (run, name = 'Printing', priority = 0, 
                          profile = PROFILE)

# This line tells the task scheduler to add this task to the system task list
cotask.task_list.append (print_task)
