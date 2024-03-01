# Simplified Melexis MLX90640 Thermal Camera Driver

This directory contains a simplified MicroPython driver for the MLX90640
thermal infrared camera which only gets **raw images**, not calibrated ones.
This saves time and memory and is usable for a mechatronics class exercise.

## Quick Start

Using Git or just downloading a `.zip` archive, copy the file `mlx_cam.py`
from this `mlx_raw` directory to your PC. 

* If you have an old (2023 or earlier) ME405 MicroPython, copy the folder 
  `mlx90640` containing all its contents (`image.py`, `calibration.py`, _etc._) 
  onto your MicroPython board such as a Nucleo&trade;.  The driver in 
  `mlx_cam.py` will look inside that folder for camera driver files. 

* If you have a newer ME405 MicroPython, no need -- the MLX90640 drivers are
  already installed on your board.
  
The file `mlx_cam.py` contains test code which will, by default, capture
a thermal image every 10 seconds (approximately) and display an ASCII art
rendition of the image.  There are several modes in which the image may
be displayed:

* ASCII art, the default, usable for testing but not a great quality image.

* CSV (comma separated variable) format, usable by spreadsheets to make a
  quick "heat map."

* Grayscale blocks, using ANSI terminal color commands to control the
  shade of gray of each block. This type of image can only be viewed on a
  serial port terminal program which recognizes these color commands. 
  PuTTY <https://putty.org> works, while Thonny and Screen (on a Mac) 
  don't.


## Detailed Version

Everybody will TL;DR a long-winded discussion anyway, right? 

...If not, see the documentation for `class MLX_Cam` in the **ME405-Support**
documentation at <https://spluttflob.github.io/ME405-Support/>.
