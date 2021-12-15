# File: board_info.py - Source for a Doxygen page about how to build a Shoe of Brian

## @page shoe_info The Shoe of Brian
#      This page describes the "shoe" circuit board at the bottom of an ME405 board stack. 
#
#  @section get_sob Obtaining a Shoe Board
#      The Shoe is an open source project hosted at OSHPark.com under the following link:
#
#      https://oshpark.com/shared_projects/e6X6OnYK
#
#      A board can be ordered directly from OSHPark or you can download the @c .brd file, 
#      make a set of Gerber files, and have another vendor fabricate the boards. 
#
#  @section parts_sob Parts
#      The following parts are needed for basic function of the board.  Note that the 
#      0805 package is a surface-mount part in 0805 size.  The resistors and ferrite bead
#      are generic and do not need close tolerances, and substitution is fine. All the
#      parts are available from multiple vendors and the given part numbers are given for
#      convenience only. The priciest parts are the screw terminal blocks, and shopping
#      around for a better price on these can pay off; price shopping for the 
#      resistors would be pretty silly, though.  The vendor information was current
#      as of early 2018 and may have changed by the time you read this.  
#      | Quantity | Part   | Value   | Package | Vendor Part Number |
#      |:-------:|:--------|:--------|:--------|:------------|
#      |    2    | Resistor | 560 ohm |  0805  | DigiKey 311-560CRCT-ND |
#      |         |          |         |        | Mouser 667-ERJ-6GEYJ561V |
#      |    2    | Resistor | 4.7 K   | 0805   | Mouser 667-ERJ-6GEYJ472V |
#      |    2    | 2x19 Header, female | - | - | Mouser 517-929975-01-19-RK |
#      |         |                     |   |   | DigiKey 929975E-01-19-ND‎ |
#      |    1    | Ferrite bead | 30-100 ohm at 1MHz | 0805 | DigiKey MH2029-300YCT-ND |
#      |    2    | Screw terminal block | 10 pos. | 2.54mm spacing | AdaFruit 2142 |
#      |         |                      |         |                | Mouser 651-1725737 |
#      |    1    | Screw terminal block | 5 pos. | 2.54mm spacing | AdaFruit 2139 |
#      |         |                      |         |                | Mouser 651-1725685 |
#      |    1    | Mini USB B connector | - | - | Mouser 710-65100516121 |
#
#      The following additional parts may be optionally added to use board features such
#      as the Micro SD card socket and IMU.  @b Warning: The IMU is in a really small
#      package without pins and is very hard to solder without going blind.  @b Also: The
#      Micro SD card socket footrint on this board is an older Molex design which can be 
#      hard to match, as the part for which this version of the board was designed has
#      been (rudely) discontinued.  
#      | Quantity | Part   | Value   | Package |
#      |:-------:|:--------|:--------|:--------|
#      |    1    | Micro SD connector | - | - |
#      |    2    | Resistor | 560 ohm |  0805  |
#      |    1    | 9-Axis IMU | LSM9DS1 | LGA24-8X4 |
#      |    1    | Capacitor | 0.1 uF | 0805 |
#      |    1    | Capacitor | 0.01 uF | 0805 |
#      |    1    | Capacitor | 22 uF | 1206 |
#      |    4    | Resistors | varies | 0805 |
#      |    1    | Diode   | >1A Schottky | varies |
#
#      The set of four resistors can be used to set the IMU's I<sup>2</sup>C bus address
#      and can usually be left off; any value between about 560 ohms and 10K should work
#      if these are needed.  The diode can be any old surface mounted Schottky which 
#      can fit on the pads and handle around an amp or more.  The capacitors are all
#      generic decoupling capacitors. 
# 
#  @section build_sob Building the Board
#      The Shoe of Brian is mostly pretty easy to solder, though there are four surface
#      mount components to test one's skills, visual acuity, and patience.  It is
#      recommended to solder the USB connector first, then the resistors and ferrite
#      bead next to it.  The USB connector needs to be soldered carefully, in particular
#      making sure that the mounting feet are well attached to the pads; if they are not,
#      bending a USB cable may tear the connector from the board.  Then if you're 
#      sufficiently experienced with SMD soldering or just crazy, add the
#      IMU and its capacitors.  If using the Micro-SD card connector, add that next, and
#      lastly solder the 2x19 headers and screw terminals.  The specified screw terminals
#      have to be squished together a bit so that they can all fit, so place all three
#      terminal blocks in the board first, then solder all three; @e do @e not solder one
#      screw terminal block before adding another, or you probably won't be able to get 
#      the second or third terminal block to fit into the board. 
#
#  @section prog_sob Flashing
#      The following procedure is used to flash MicroPython onto the Nucleo:
#
#      * Obtain an up-to-date copy of the compiled MicroPython binary file
#        from this repository's main folder.
#      * Unplug the Nucleo from USB
#      * Move the jumper near the reset switch on the Nucleo from E5V to U5V 
#      * Plug in the Nucleo's (not the shoe's) USB connector to the PC
#      * Drag the firmware*.bin file into the NODE_L476xx directory
#      * Wait for the red-green blinking to stop, then restart, then stop again
#      * Wait another 10 seconds or so
#      * Unplug USB from the Nucleo
#      * Move the jumper near the reset switch on the Nucleo from U5V to E5V 
#      * Plug the USB cable into the Shoe and MicroPython should be there
#
#  @section feat_sob Features
#      @subsection mag_sob IMU Axes
#      A quirk of the LSM9DS1 IMU is that the X axis for the magnetometer is @e not in
#      the same direction as the X axis of the accelerometer and rate gyro.  Software
#      should take this into account. 
#
#      @subsection pry_sob Disassembly
#      The 2x19 pin headers grip the Nucleo<sup>TM</sup> headers very firmly and are
#      difficult to remove.  If the boards must be separated, prying them very slowly
#      apart with a large flat screwdriver usually works.  The screwdriver can be
#      placed atop the screw terminal blocks to pry one end of the board upward and 
#      used in the gap between the top of the 2x19 headers and the Nucleo board on the
#      other end.  @b Always keep the boards nearly parallel to one another, prying each
#      end up by 1-2 mm and going to the other end, back and forth several times. 
#
#      @subsection mount_sob Mounting
#      The mounting holes are sized for small #4-40 screws and are close to traces and 
#      components; use mounting screws with small diameter heads, and insulating washers
#      on both sides of the board may be a good idea. 
#
#  @section name_sob What's With the Name?
#      It's a Shoe because the other circuit boards stand upon it.  Because the board 
#      is designed for (Micro)Python, its name is of course a Python reference:
#
#      https://www.youtube.com/watch?v=Ym-k5viJ7tA
#
#
