"""!
@file nb_input_task.py
This file contains a task function which reads user input in a non-blocking way
and makes that input available to other tasks.

**FEATURE:** This stuff only runs on STM32s because it uses pyb.USB_VCP.

@author JR Ridgely
@date   2022-Feb-12 JRR Original file
@copyright (c) 2022 by JR Ridgely and released under the GNU Public License,
           version 3. 
"""

from pyb import USB_VCP


## A string when input has been received by the user, or @c None if no complete
#  line of input has been received. 
input_string = None


def input_task (echo=True):
    """!
    Watch for characters coming through a serial port, assemble them into a
    line, and make a reference to the line available when the user has pressed
    Enter.
    @param echo If true, characters will be printed back as they're typed

    @section input_task_usage Usage Example
    Importing this module defines a task function @c input_task() which you
    must make into a task using a @c cotask.Task object and put into the task
    list. See the example file @c basic_tasks.py to run the cotask scheduler,
    or examine the test code at the bottom of @c nb_input_task.py for another
    simpler example. 
    ```.py
    import nb_input_task
    ...
    global input_string
    ...
    while True:                                 # As usual for a task
        ...
        if input_string is not None:            # If a line of data is
                do_something (input_string)     # available, use it and
                input_string = None             # reset the input
        ...
        yield state
    ...
    in_task = cotask.Task (input_task, name = 'Task_1', priority = 1, 
                           period = 50, profile = True, trace = False)
    cotask.task_list.append (in_task)
    ...
    # And run the task scheduler as usual
    ```
    @subsection input_task_thonny Feature
    When running this code with Thonny, one often sees warnings such as
    @c WARNING:root:Unexpected&nbsp;echo, indicating that the text which Thonny
    saw from the microcontroller in response to user input isn't what Thonny
    expected to see. These warnings should be ignored. 
    """
    global input_string

    line = ""
    vcp = USB_VCP ()

    while True:
        if vcp.any ():
            a_char = (vcp.read (1))[0]
            if a_char == 13:               # This is '\r'; we have a line
                input_string = line[:]     # Force a copy, not just a reference
                line = ""                  # Clear the original line
            elif a_char == 10:             # This is '\n'; ignore it
                pass
            elif a_char == 8 and len (line) > 0:   # Backspace, non-empty line
                line = line[:-1]
                print (chr (a_char), end='')
            else:
                line += chr (a_char)
                if echo:
                    print (chr (a_char), end='')

        yield 0


## @cond DONT_DOXY_THIS
# Test the input task by running it with another task that blinks a blinky LED
# on a Nucleo-L476RG while simultaneously getting input and displaying it
if __name__ == "__main__":

    import cotask
    from pyb import LED

    def blinky_task ():
        """!
        Task which blinks and LED to show that it's running and prints things 
        from the input task.
        """
        global input_string

        led = LED (1)                      # The green LED on a Nucleo-64
        while True:
            led.toggle ()

            if input_string is not None:
                print ("\r\nInput:", input_string)
                input_string = None

            yield (0)


    print ("\033[2JTesting Non-Blocking Input Task")
    _task1 = cotask.Task (input_task, name = 'Input Task', priority = 1, 
                          period = 50, profile = True, trace = False)
    _task2 = cotask.Task (blinky_task, name = 'Test Task', priority = 2, 
                          period = 50, profile = True, trace = False)
    cotask.task_list.append (_task1)
    cotask.task_list.append (_task2)

    while True:
        try:
            cotask.task_list.pri_sched ()
        except KeyboardInterrupt:
            break

    print ('\n' + str (cotask.task_list))
    ## @endcond
