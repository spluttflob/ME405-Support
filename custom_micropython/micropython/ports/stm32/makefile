# Makefile for ME405 version of MicroPython with extras.
# This lowercase-m makefile overrides the uppercase-M
# Makefile, sets some parameters, then calls Makefile

BOARD = NUCLEO_L476RG

# Where to find the additional C modules used in ME405.
# These are in a directory "modules" which is in the same
# place as the topmost micropython source directory
USER_C_MODULES = ../../../modules

# The ulab module wants to be clearly told it is needed
CFLAGS_EXTRA = -DMODULE_ULAB_ENABLED=1

# Now include the regular Micropython Makefile
include Makefile
