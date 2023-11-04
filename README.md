# README

This repository holds code used in the ME405 course at Cal Poly. 

The documentation pages are at <https://spluttflob.github.io/ME405-Support/>.

### Scheduler Files

* These files are used to implement cooperative multitasking in MicroPython.
  The `cotask.py` and `task_share.py` modules are central to this structure. 


### Other Lab Support Files

* `src/nb_input.py` contains a class which implements non-blocking input from
  a serial port on a microcontroller running MicroPython.

* `examples/what_you_said.py` helps to test serial communications between a
  microcontroller running MicroPython and a PC running a regular Python 
  program.

* `examples/test_kbd.py` demonstrates one way to use the `keyboard` module to
   allow Python to read individual key presses **on a PC,** not on a
   microcontroller. 

* `examples/vend_kb.py` demonstrates another method to do non-blocking reads on
   a PC.

* `custom_micropython` has some support to help those who wish to compile their
  own ME405 style custom MicroPython firmware.

  
### Firmware Files

* The file `firmware.bin` contains a custom version of MicroPython for use only
  on an STM32L476RG Nucleo. It supports extra UARTs, DAC, and the use of the 
  USB-OTG connector on the Shoe of Brian (see the github-pages documents) to
  connect the `/flash` directory as a USB drive. CAN is not supported, as the 
  pins needed are used by the USB-OTG connector. 
  
  This firmware file also contains **MicroPython-ulab,** the NumPy/SciPy partial 
  workalike library found at <https://github.com/v923z/micropython-ulab>, and
  `cqueue`, a module hosted in this repository which contains fast and efficient 
  queues to transfer data between tasks.

  
### Homework Support Files

Most homework support is maintained by the course instructors. 
If any additional files are needed, they may be kept here. 

