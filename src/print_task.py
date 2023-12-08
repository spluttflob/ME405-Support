## @file print_task.py
#  This file contains code for a task which prints things from a queue. It helps
#  to reduce latency in a system having tasks which print because it sends
#  things to be printed out the serial port one character at a time, even when
#  other tasks put whole strings into the queue at once. When run as a
#  low-priority task, this allows higher priority tasks to interrupt the
#  printing between characters, even when all the tasks are being cooperatively
#  scheduled with a priority-based scheduler. 
#
#  Example code:
#  @code
#  # In each module which needs to print something:
#  import print_task
# 
#  # In the main module or wherever tasks are created:
#  print_task = cotask.Task (print_task_function, name = 'Printing', 
#                           priority = 0, profile = True)
#  cotask.task_list.append (print_task)
# 
#  # In a task which needs to print something:
#  print_queue.put ("This is a string")
#  print_queue.put_bytes (bytearray ("A bytearray"))
#  print_queue.put ("A number: {:d}\r\n".format (number))
#  @endcode
# 
#  @copyright This program is copyright (c) 2018-2023 by JR Ridgely and
#             released under the GNU Public License, version 3.0. 
# 
#  It is intended for educational use only, but its use is not limited thereto.
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.

# import pyb
import cotask
import task_share
from micropython import const


## The size of the buffer which will hold characters to be printed when the
#  print task has time to print them. 
PT_BUF_SIZE = const (1000)


## Put a string into the print queue so it can be printed by the printing 
#  task whenever that task gets a chance. If the print queue is full, 
#  characters are lost; this is better than blocking to wait for space in the
#  queue, as we'd block the printing task and space would never open up. When 
#  a character has been put into the queue, the @c go() method of the print 
#  task is called so that the run method will be called as soon as the print 
#  task is run by the task scheduler. 
#  @param a_string A string to be put into the queue
@micropython.native
def put (a_string):
    for a_ch in a_string:
        print_task.go ()
#         if not print_queue.full ():
#             print_queue.put (ord (a_ch))
#             print_task.go ()


## Put bytes from a @c bytearray or @c bytes into the print queue. When 
#  characters have been put into the queue, the @c go() method of the print
#  task is called so that the run method will be called as soon as the print 
#  task is run by the task scheduler. 
#  @param b_arr The bytearray whose contents go into the queue
@micropython.native
def put_bytes (b_arr):

    for byte in b_arr:
        if not print_queue.full ():
            print_queue.put (byte)
            print_task.go ()


## Task function for the task which prints stuff. This function checks for
#  any characters to be printed in the queue; if any characters are found 
#  then one character is printed, after which the print task yields so other 
#  tasks can run. This function must be called periodically; the normal way 
#  is to make it the run function of a low priority task in a cooperatively 
#  multitasked system so that the task scheduler calls this function when 
#  the higher priority tasks don't need to run.
def print_task_function ():

    while True:
        # If there's a character in the queue, print it
        if print_queue.any ():
            print (chr (print_queue.get ()), end = '')

        # If there's another character, tell this task to run again ASAP
        if print_queue.any ():
            print_task.go ()

        yield 0


## This queue holds characters to be printed when the print task gets around
#  to it. It is always created when print_task is imported as a module.
global print_queue
print_queue = task_share.Queue ('B', PT_BUF_SIZE, name = "Print Queue", 
                                thread_protect = False, overwrite = False)


## @cond DO_NOT_DOXY_THIS
# This test code is only run when this file is used as the main file; it isn't
# run when the file is imported as a module
if __name__ == "__main__":
    import utime
    import task_share
    from micropython import const
    from pyb import USB_VCP

    print ("Testing print_task")

    def print_queue_task_fun ():
        """!
        Task which puts things into a share and a queue.
        """
        counter = 0
        while True:
            counter += 1
            put (f"The current value of the first counter: {counter}\r\n")
            yield 0

    def print_direct_task_fun ():
        """!
        Task which prints things directly rather than using a print task.
        """
        counter = 0
        while True:
            counter += 1
            print (f"The current value of the other counter: {counter}\r\n",
                   end='')
            yield 0

    # Create tasks to send things and print things
    task_1 = cotask.Task (print_queue_task_fun, name = "Print to Queue",
                          priority = 2, period = 1000, profile = True)
    task_2 = cotask.Task (print_direct_task_fun, name = "Print Directly",
                          priority = 2, period = 1000, profile = True)
    print_task = cotask.Task (print_task_function, name = "Print Task", 
                              priority = 0, profile = True)
    cotask.task_list.append (task_1)
    cotask.task_list.append (task_2)
    cotask.task_list.append (print_task)

    # Run tasks until someone presses a key, then stop and show diagnostics
    while True:
        try:
            cotask.task_list.pri_sched ()
        except KeyboardInterrupt:
            break

    # Print a table of task data and a table of shared information data
    print ('\n' + str (cotask.task_list))
    print (task_share.show_all ())
    print ('\r\n')

## @endcond
