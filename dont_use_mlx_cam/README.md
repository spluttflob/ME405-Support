# Melexis MLX90640 Thermal Camera Drivers

This directory contains a simplified MicroPython driver for the MLX90640
thermal infrared camera.

## Quick Start

Using Git or just downloading a `.zip` archive, copy the file `mlx_cam.py`
to your PC.  Copy the folder `mlx90640` containing all its contents 
(`image.py`, `calibration.py`, _etc._) onto your MicroPython board such
as a Nucleo&trade;.  The driver in `mlx_cam.py` will look inside that
folder for camera driver files. 

The file `mlx_cam.py` contains test code which will, by default, capture
a thermal image every 10 seconds (approximately) and display an ASCII art
rendition of the image. 


## Detailed Version

Everybody will TL;DR a long-winded discussion anyway, right? 

...If not, see the documentation for `class MLX_Cam` in the **ME405-Support**
documentation at <https://spluttflob.github.io/ME405-Support/>.
