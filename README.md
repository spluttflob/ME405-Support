# README

This repository holds code used in the ME405 course at Cal Poly. 


### Scheduler Files

These files are used to implement cooperative multitasking in MicroPython.
The `cotask.py` and `task_share.py` modules are central to this structure. 


### Other Lab Support Files

* `test_kbd.py` demonstrates one way to use the `keyboard` module to
   allow Python to read individual key presses **on a PC,** not on a
   microcontroller. 

* `vend_kb.py` demonstrates another method to do non-blocking reads on
   a PC.

* To read keys without blocking a microcontroller running MicroPython,
  you may use the `USB_VCP` class (an example will be posted here if
  needed). 

### Homework Support Files

Most homework support is maintained by the lecture instructor. 
If any additional files are needed, they may be kept here. 
