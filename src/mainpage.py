## @file mainpage.py
#  @author JR Ridgely
#  @mainpage
#
#  @section ss_intro Introduction
#  The ME405 Python code library contains a set of routines which implement a
#  simple cooperative scheduler that runs in MicroPython. This library is 
#  used for teaching the development of mechatronic systems, including 
#  modestly complex real-time software for use in embedded systems. Its use is
#  not recommended in production systems because the code has not been
#  thoroughly tested to ensure reliability. As of this writing, the same 
#  warning should be made for MicroPython, on which this software is based; as
#  a new product, MicroPython still has bugs and features which significantly
#  affect reliability. It is expected that the reliability of both ME405 code
#  and MicroPython will improve rapidly in the next few years, and users of
#  this code are encouraged to contribute to the development of both. 
#
#  @section ss_hardware Hardware
#  The ME405 course runs MicroPython on Nucleo-64<sup>TM</sup> boards from 
#  ST Microelectronics, taking advantage of the boards' high value for 
#  the money (we're a state supported school teaching some of the best of
#  the 99%). We usually employ a simple custom board called the Shoe of Brian 
#  which sits below the Nucleo and houses a USB OTG "On-The-Go" connector. 
#  The USB OTG connector allows mounting some of the microcontroller's flash 
#  memory as a USB file system, making for convenient programming. We prefer 
#  to leave the Nucleo's ST-Link 2.1 programmer attached so that the board 
#  can be programmed in C++ for high-performance applications if needed in 
#  other mechatronics and Senior project courses. The ME405 software was 
#  deleloped using a Nucleo-L476RG board; this version works much better for
#  our purposes than the -F401 and -F411 versions because of the much larger
#  available flash memory. The processors with 512MB flash cannot easily
#  accommodate MicroPython itself plus a substantial group of Python programs
#  such as the ME405 software suite, unless provided with SD cards, which add
#  to the expense and complexity of the system. 
#
#  @subsection ss_build Build Your Own
#  If you are interested in building your own ME405 circuit, please refer
#  to the following page: 
#  @subpage shoe_info
#
#  If you'd rather not build your own board, note that 
#  many STM32 Discovery<sup>TM</sup> boards are supplied with built-in USB
#  OTG connectors, allowing similarly convenient programming without having to
#  build custom circuitry. The original MicroPython PyBoard has both USB OTG
#  and Micro-SD card connectors and makes an excellent platform for this 
#  software, though minor modifications may be needed to accommodate the 
#  slightly different processor and pinouts. 
#
#  @subsection prepshoe Preparing Nucleo-64s for ME405
#  As shipped, 64-pin Nucleo<sup>TM</sup> boards get power from the USB
#  connector on the ST-Link programmer attached to those boards. In order to
#  be powered from the Shoe of Brian boards underneath and reliably operate
#  their USB-OTG file systems, Nucleo-64 boards need their JP5 jumpers moved
#  from the as-delivered connection of pins 1 to 2 to the other side of the
#  header block, pins 2 to 3.  See ST's user manual UM1724, the user manual
#  for Nucleo-64 boards for more details and schematics.  @e Strangeness: 
#  One batch of STM32L476RG boards has worked without moving this jumper, but
#  another batch requires the jumper to be moved to operate correctly. 
#
#  @section ss_modules Components
#  * The basic functionality of cooperatively (mostly) multitasking real-time
#    software is provided in @c cotask.py.
#  * Communication of information between tasks, including thread-safe 
#    transfer of data between interrupt service routines and cooperatively
#    scheduled "regular" tasks, is supported by code in @c task_share.py.
#  * A number of device drivers are provided, while others are left as an
#    exercise for the student. 
#
#  @section sqref Quick Reference
#  This section contains some quick hints about how to use various functions
#  of the Nucleo<sup>TM</sup> boards with MicroPython as they are set up for
#  ME405. 
#
#  @subsection sstiming Timing
#  MicroPython has two time related libraries, @c time and @c utime, which 
#  provide the same functionality. The use of @c utime is recommended to
#  avoid confusion with the standard Python library called @c time, which has
#  different functionality.
#
#  Reference:
#  https://docs.micropython.org/en/latest/pyboard/library/utime.html
#  @code
#  import utime
#  utime.sleep (0.5)       # Sleep for 0.5 sec, blocking tasks (bad)
#  utime.sleep_us (10)     # Sleep for only 10 us, which is usually OK
#
#  # The following measures how long a function takes to run in microseconds
#  start_time = utime.ticks_us ()
#  run_my_function ()
#  duration = utime.ticks_diff (utime.ticks_us, start_time)
#  @endcode
#
#  @subsection sspins GPIO Pins
#  Reference: 
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.Pin.html
#  @code
#  # Set up a pin as an output and control it
#  pinC0 = pyb.Pin (pyb.Pin.board.PC0, pyb.Pin.OUT_PP)
#  pinC0.high ()
#  pinC0.low ()
#
#  # Set up another pin as an input and read it
#  pinC1 = pyb.Pin (pyb.Pin.board.PC1, pyb.Pin.IN)
#  if pinC1.value ():
#      print ("Pin C1 is high. Is that legal now?")
#  @endcode
#
#  @subsection ssextint External Interrupts
#  Reference: 
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.ExtInt.html
#  @code
#  isr_count = 0
#  def count_isr (which_pin):        # Create an interrupt service routine
#      global isr_count
#      isr_count += 1
#
#  extint = pyb.ExtInt (pyb.Pin.board.PC0,   # Which pin
#               pyb.ExtInt.IRQ_RISING,       # Interrupt on rising edge
#               pyb.Pin.PULL_UP,             # Activate pullup resistor
#               count_isr)                   # Interrupt service routine
#
#  # After some events have happened on the pin...
#  print (isr_count)
#  @endcode
#
#  @subsection sstimers Timers and Timer Interrupts
#  The frequency given in the @c freq parameter of the @c pyb.Timer constructor
#  is the frequency at which the timer overflows and restarts counting at zero.
#  When using timer interrupts, this is the frequency at which interrupts 
#  occur.  Only certain pins can be used with timers. Look for pins associated 
#  with the channels of timers in the STM32 data sheet.
#
#  Reference:
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.Timer.html
#  @code
#  timmy = pyb.Timer (1, freq = 1000)             # Timer 1 running at 1000 Hz
#  timmy.counter ()                               # Get timer value
#  timer.freq (100)                               # Change rollover rate
#
#  # Define a function that toggles the pin and set it as the interrupt
#  # service routine. Uses pinC0 from above
#  def toggler (which_timer):
#      if pinC0.value ():
#          pinC0.low ()
#      else:
#          pinC0.high ()
#
#  timmy.callback (toggler)
#  @endcode
#
#  @subsection sspwm Pulse Width Modulation
#  Only certain pins can be used for PWM. Look for pins associated with the
#  channels of timers in the STM32 data sheet.
#
#  Reference: 
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.Timer.html
#  @code
#  pinA1 = pyb.Pin (pyb.Pin.board.PA1, pyb.Pin.OUT_PP)
#  tim2 = pyb.Timer (2, freq=1000)
#  ch2 = tim2.channel (2, pyb.Timer.PWM, pin=pinA1)
#  ch2.pulse_width_percent (30)
#  @endcode
#
#  @subsection ssadc Analog to Digital Conversion (ADC or A/D)
#  It is very important to apply only voltages in the range from 0 to 3.3V to
#  each A/D pin. Excessive or negative voltages can destroy things. Not all
#  pins can be used as A/D pins; see the STM32 datasheet pin alternate 
#  function table to find out which ones will work (or just try some in the
#  REPL and see which don't give you a @c ValueError ).
#
#  Reference:
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.ADC.html
#  @code
#  adcpin = pyb.ADC (pyb.Pin.board.PA4)
#  volts = adcpin.read ()
#  @endcode
#
#  @subsection ssdac Digital to Analog Conversion (DAC or D/A)
#  Some STM32 chips have digial to analog converters, and others don't. 
#  Digital to analog conversion is not officially supported on ME405 boards,
#  but you can look for class @c pyb.DAC and if it's there, search for
#  MicroPython documentation on how to use it.
#
#  @subsection ssi2c I&sup2;C
#  The following example is for hardware I&sup2;C on the STM32.
#
#  Reference: 
#  https://docs.micropython.org/en/latest/pyboard/library/pyb.I2C.html
#  @code
#  i2c1 = pyb.I2C (1, pyb.I2C.CONTROLLER, baudrate = 100000)
#  i2c1.scan ()                             # Check for devices on the bus
#  i2c1.mem_write ('\x07', 0x2A, 0x05)      # Send a 7 to sensor at 0x2A, register 0x05
#  buffy = bytearray(2)                     # To store 
#  i2c1.mem_read (buffy, 0x2A, 0x07)        # Read 2 bytes from register 0x07 into buffy
#  rsp = i2c1.mem_read (2, 0x2A, 0x07)      # Or read and return 2 bytes from register 0x07
#  @endcode
#
#  @subsection flashprob Flash Memory Problems
#  It is possible that the flash memory on a Nucleo may become corrupted. 
#  This problem seems to manifest itself by read or write errors with source
#  files on the PYBFLASH drive, or by Thonny complaining about its backend. 
#  A solution may be attempted by reformatting
#  the processor's internal flash drive (unless you are using a MicroSD card,
#  in which case just take that out and reformat it in a PC).  The following
#  procedures should reformat the flash, but your mileage may vary.  
#  There are @b no @b guarantees this will work and not harm your system. 
#  Before you run these commands, make sure to back up any files on the 
#  MicroPython board if you can read them. 
#
#  @b Recommended @b Procedure - as of 2024, anyway
#
#  Hold the blue button down and briefly push the black reset button
#  **while continuing to hold the blue button.** 
#  The green LED will blink once, then twice, then three times; after the
#  three flashes, release the blue button and wait a few seconds while the
#  green light does more blinky things -- and then wait another 10 seconds
#  after it stops.  Your @c PYBFLASH drive should now be freshly formatted. 
#  Unplug the board from your PC to power it
#  off, wait a few seconds, then plug it back in. All files except @c boot.py,
#  @c main.py, @c pybcdc.inf, and @c README.txt should be gone. 
#  If your old files are still there, try ejecting (or unmounting, or 
#  "removing" depending on what your OS calls it) the PYBFLASH drive on the PC, 
#  then unplugging the MicroPython board, waiting several seconds, and plugging 
#  it in again.
#
#  Reference: 
#  https://docs.micropython.org/en/latest/pyboard/pyboard/tutorial/reset.html
#
#  @b Alternative @b Procedure - MicroPython 1.13 from 2021 and later (maybe)
#
#  Make sure you're at the REPL prompt and run the following lines:
#  @code
#  import os, pyb
#  os.umount ('/flash')
#  os.VfsFat.mkfs (pyb.Flash (start=0))
#  os.mount (pyb.Flash (start=0), '/flash')
#  os.chdir ('/flash')
#  @endcode
#  The flash drive may lose its name @b PYBFLASH and get a random numerical
#  name, but it will have been newly set up and should work well again. 
#
#  @copyright 
#  The ME405 software suite is copyright 2016-2024 by JR Ridgely and released
#  under the GNU Public License, version 3. It intended for educational use 
#  only, but its use is not limited thereto. 
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

