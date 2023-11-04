# Building the ME405 Custom MicroPython
**Most Recent Update:** November 2023 for MicroPython version 
1.22.0-preview.

These instructions should help you set up an environment to build MicroPython for
the ME405 board set, which includes:

* An IHM04A1 motor driver board on top

* An STM32L476RG Nucleo in the middle

* A Shoe of Brian custom board on the bottom

It should be possible to do this on any of the common operating systems. 
The author uses Linux Mint. 

It is assumed that you have installed an ARM Cortex&trade; compiler on
your computer, you are familiar with using the command line, you have
a Unix&trade;/Linux-like environment on your computer (such as LSW) if
you're running Windows&trade;, and you have and can use the `make`
utility to build programs. 


## Building Stock MicroPython
You should first set up a build environment for regular MicroPython, 
then test it and make sure it compiles MicroPython successfully. 
Also verify that you can flash a MicroPython binary onto your Nucleo&trade;
or other board. 

Make sure to set up the MicroPython subdirectory in its own folder on
your computer, as you may want to add other modules in that directory,
next to the MicroPython source code directory tree. 
Instructions for downloading and setting up MicroPython source code 
are found at:  
<https://docs.micropython.org/en/latest/develop/gettingstarted.html>

When following all the instructions carefully (which you _gotta_ do), 
be sure to pay extra attention to the section "Building the STM32 port."

## Custom MicroPython Files
You need to add some custom files, and custom modified versions of 
stock files, in the MicroPython source tree.  Custom versions of these
files are arranged in directories under this one which match the
arrangement of directories in the stock MicroPython source tree.
Custom files whose names match those of existing files should overwrite
the stock files, and files which don't exist in the stock version may
just be placed in the correct directories. 

#### Highlights
The most important customized things are in the files shown in the tree 
below. 

**`mpconfigboard.h`** Selects which pins are used for which peripherals.
The most important section controls the UART which is used for the REPL:

```c
#define MICROPY_HW_UART1_TX         (pin_B6)
#define MICROPY_HW_UART1_RX         (pin_B7)
#define MICROPY_HW_UART1_CTS        (pin_B4)
```

**`makefile`** This file contains a custom setup so that one can compile
MicroPython for the desired target, using the desired extra modules, 
by just typing `make` at a Linux/Unix command prompt.  After applying
custom settings, this file calls the stock `Makefile` which need not
be modified.  Notice that in a Mac&trade; or Unix&trade; or Linux environment,
the two files `makefile` and `Makefile` are seen as two _different_
files. 


## Extra Packages
For ME405, we add two extra packages.  First, a directory called `modules`
is created in the same directory where the base `micropython` directory lives 
(this is _not_ the `user_mods` directory inside the MicroPython source tree).

* **ulab** is a partial NumPy workalike which allows fast, convenient
  manipulation of data. It is found on GitHub&trade; at  
  <https://github.com/v923z/micropython-ulab>  
  We install it by cloning the GitHub repository inside the `modules` 
  directory.

* **cqueue** is a set of custom classes which implement fast queues to carry
  data from tasks to other tasks.  These are hosted on GitHub&trade; at  
  <https://github.com/spluttflob/ME405-Support/tree/main/custom_micropython/modules/cqueue>  
  ...in other words, pretty much right here.

## The MicroPython Source Tree
A partial listing of the source tree, highlighting the files of most 
interest to compiling the ME405 code, is shown below.  Since there are
_lots_ of files in the tree, the contents of directories in which we do
not need to make modifications are not shown, and bunches of directories
containing ports in which we're not necessarily interested are replaced
with ellipses (`...`).

```c
modules
├── cqueue
│   ├── cqueue.c
│   ├── micropython.cmake
│   └── micropython.mk
└── ulab
    └── ...
micropython
├── docs
├── drivers
├── examples
├── extmod
├── lib
├── LICENSE
├── logo
├── mpy-cross
├── ports
│   ├── bare-arm
│   ├── cc3200
│   ├── embed
│   ├── esp32
│   ├── ...
│   ├── rp2
│   ├── samd
│   ├── stm32
│   │   ├── boards
│   │   │   ├── ...
│   │   │   ├── NUCLEO_L476RG
│   │   │   │   ├── board.json
│   │   │   │   ├── mpconfigboard.h
│   │   │   │   ├── mpconfigboard.mk
│   │   │   │   ├── pins.csv
│   │   │   │   └── stm32l4xx_hal_conf.h
│   │   │   ├── NUCLEO_L4A6ZG
│   │   │   ├── NUCLEO_WB55
│   │   │   ├── ...
│   │   │   └── VCC_GND_H743VI
│   │   ├── makefile
│   │   ├── Makefile
│   │   └── README.md
│   ├── unix
│   ├── webassembly
│   ├── windows
└── zephyr
├── py
├── shared
├── tests
├── tools
└── user_mods
    ├── ME405
    └── ulab

```
