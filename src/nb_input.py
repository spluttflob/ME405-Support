"""!
@file nb_input.py
This file contains a class which can be used to read input through a serial
port in a non-blocking way. This module has been tested only on an STM32 using
pyb.USB_VCP, but it should work on other CPU types using a UART object as the
source of characters. 

@author JR Ridgely
@date   2022-Feb-13 JRR Original file
@copyright (c) 2022 by JR Ridgely and released under the GNU Public License,
           version 3. 

It is intended for educational use only, but its use is not limited thereto.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


class NB_Input:
    """!
    This class implements a task which reads user input one character at a time
    and puts characters together into lines of text. The result is code that
    can be used similarly to the Python @c input() function but doesn't block
    other tasks while waiting for the lazy bum user to type something. Lines
    of text which have been received are put into a list; the lines can then be
    read from the list as they become available. 

    @section input_task_usage Usage Example
    The class in this module is designed to be run within a task which is run
    by the scheduler in @c cotask.py.  See the example file @c basic_tasks.py
    and the test code at the bottom of this file for examples of such tasks.
    ```.py
    from pyb import USB_VCP
    from nb_input import NB_Input
    # ...
    serial_stream = USB_VCP ()
    nb_in = NB_Input (serial_stream, echo=True)
    # ...
    def blinky_task ():
        '''!  Task which demonstrates non-blocking input. This task should run
        often (say, 50ms) for human input and faster for computer input '''
        while True:
            if nb_in.any ():
                print ("\r\nInput:", nb_in.get ())
            yield 0
    # ...
    # Create a task and run the task scheduler as usual for @c cotask.py
    ```
    @subsection input_task_thonny Feature
    When running this code with Thonny, one often sees warnings such as
    @c WARNING:root:Unexpected&nbsp;echo, indicating that the text which Thonny
    saw from the microcontroller in response to user input isn't what Thonny
    expected to see. These warnings may be ignored. 
    """
    _ser_dev: stream   # Serial device from which input comes
    _echo: bool        # Whether to echo characters back to the user
    _line: str         # The line currently being received
    _list: list        # A list of previously received lines of input


    def __init__ (self, serial_device: stream, echo=True):
        """!
        Create a non-blocking input object. There should be at most one of
        these for each serial port.
        @param serial_device The UART or similar serial port through which
               characters will be received
        @param echo If true, characters will be printed back as they're typed
        """
        self._ser_dev = serial_device
        self._echo = echo
        self._line = ""
        self._list = []


    def any (self):
        """!
        Check whether there are any lines of input and return the oldest if so.
        @returns @c True if there are any lines of user input available
        """
        self.check ()
        return len (self._list) > 0


    def get (self):
        """!
        Get one line of characters which have been received through the serial
        device. This method pops a line of text from the queue, so each line of
        text can only be gotten once.
        @returns One line of input, or @c None if no lines are available
        """
        if len (self._list) > 0:
            return self._list.pop (0)


    def check (self):
        """!
        This method is run within a task function to watch for characters
        coming through a serial port. As characters are received, it assembles
        them into a line and makes a reference to the line available when the
        user has pressed Enter.
        @return A string containing a line of text, or @c None if no line has
                been received since the last line was returned
        """
        if self._ser_dev.any ():
            a_char = (self._ser_dev.read (1))[0]
            if a_char == 13:                      # This is '\r'; line complete
                self._list.append (self._line[:]) # Force a copy, not reference
                self._line = ""                   # Clear the original line
            elif a_char == 10:                    # This is '\n'; ignore it
                pass
            elif a_char == 8 and len (self._line) > 0:   # Backspace, non-empty
                self._line = self._line[:-1]
                if self._echo:
                    print (chr (a_char), end='')
            else:                                 # Any old regular character
                self._line += chr (a_char)
                if self._echo:
                    print (chr (a_char), end='')
        return None


## @cond DONT_DOXY_THIS
# Test the input task by running it with another task that blinks a blinky LED
# on a Nucleo-L476RG while simultaneously getting input and displaying it
if __name__ == "__main__":
    from pyb import LED, USB_VCP           # Tested on a Nucleo L476RG
    import cotask

    nb_in = NB_Input (USB_VCP (), echo=True)

    def blinky_task ():
        """!  Task which blinks an LED to show that it's running and prints
        things from the input task. """
        led = LED (1)                      # The green LED on a Nucleo-64
        while True:
            led.toggle ()
            if nb_in.any ():
                print ("\r\nInput:", nb_in.get ())
            yield 0

    def input_task ():
        """!  Task which runs the non-blocking input object quickly to ensure
        that keypresses are handled not long after they've occurred. """
        while True:
            nb_in.check ()
            yield 0

    print ("\033[2JTesting Non-Blocking Input Class")
    in_task = cotask.Task (input_task, name = 'Input Task', priority = 1, 
                           period = 50, profile = True, trace = False)
    led_task = cotask.Task (blinky_task, name = 'Test Task', priority = 2, 
                            period = 500, profile = True, trace = False)
    cotask.task_list.append (in_task)
    cotask.task_list.append (led_task)

    while True:
        try:
            cotask.task_list.pri_sched ()
        except KeyboardInterrupt:
            break

    print ('\n' + str (cotask.task_list))
    ## @endcond

