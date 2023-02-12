"""!
@file mma845x.py
This file contains a @b partly @b written MicroPython driver for the MMA8451 
and MMA8452 accelerometers. It is intended to be used as a starting point for
an exercise in a mechatronics course. 

@author JR Ridgely
@copyright GPL Version 3.0
"""

import micropython


## The register address of the STATUS register in the MMA845x
STATUS_REG = micropython.const (0x00)

## The register address of the OUT_X_MSB register in the MMA845x
OUT_X_MSB = micropython.const (0x01)

## The register address of the OUT_X_LSB register in the MMA845x
OUT_X_LSB = micropython.const (0x02)

## The register address of the OUT_Y_MSB register in the MMA845x
OUT_Y_MSB = micropython.const (0x03)

## The register address of the OUT_Y_LSB register in the MMA845x
OUT_Y_LSB = micropython.const (0x04)

## The register address of the OUT_Z_MSB register in the MMA845x
OUT_Z_MSB = micropython.const (0x05)

## The register address of the OUT_Z_LSB register in the MMA845x
OUT_Z_LSB = micropython.const (0x06)

## The register address of the WHO_AM_I register in the MMA845x
WHO_AM_I = micropython.const (0x0D)

## The register address of the DATA_CFG_REG register in the MMA845x which is
#  used to set the measurement range to +/-2g, +/-4g, or +/-8g
XYZ_DATA_CFG = micropython.const (0x0E)

## The register address of the CTRL_REG1 register in the MMA845x
CTRL_REG1 = micropython.const (0x2A)

## The register address of the CTRL_REG2 register in the MMA845x
CTRL_REG2 = micropython.const (0x2B)

## The register address of the CTRL_REG3 register in the MMA845x
CTRL_REG3 = micropython.const (0x2C)

## The register address of the CTRL_REG4 register in the MMA845x
CTRL_REG4 = micropython.const (0x2D)

## The register address of the CTRL_REG5 register in the MMA845x
CTRL_REG5 = micropython.const (0x2E)

## Constant which sets acceleration measurement range to +/-2g
RANGE_2g = micropython.const (0)

## Constant which sets acceleration measurement range to +/-2g
RANGE_4g = micropython.const (1)

## Constant which sets acceleration measurement range to +/-2g
RANGE_8g = micropython.const (2)


class MMA845x:
    """! This class implements a simple driver for MMA8451 and MMA8452
    accelerometers. These inexpensive phone accelerometers talk to the CPU 
    over I<sup>2</sup>C. Only basic functionality is supported: 
    * The device can be switched from standby mode to active mode and back
    * Readings from all three axes can be taken in A/D bits or in g's
    * The range can be set to +/-2g, +/-4g, or +/-8g

    There are many other functions supported by the accelerometers which could 
    be added by someone with too much time on her or his hands :P 
    
    An example of how to use this driver:
    @code
    mma = mma845x.MMA845x (pyb.I2C (1, pyb.I2C.MASTER, baudrate = 100000), 29)
    mma.active ()
    mma.get_accels ()
    @endcode 
    The example code works for an MMA8452 on a SparkFun<sup>TM</sup> breakout
    board. """

    def __init__ (self, i2c, address, accel_range = 0):
        """! Initialize an MMA845x driver on the given I<sup>2</sup>C bus. The 
        I<sup>2</sup>C bus object must have already been initialized, as we're
        going to use it to get the accelerometer's WHO_AM_I code right away. 
        @param i2c An I<sup>2</sup>C bus already set up in MicroPython
        @param address The address of the accelerometer on the I<sup>2</sup>C
            bus 
        @param accel_range The range of accelerations to measure; it must be
            either @c RANGE_2g, @c RANGE_4g, or @c RANGE_8g (default: 2g)
        """

        ## The I2C driver which was created by the code which called this
        self.i2c = i2c

        ## The I2C address at which the accelerometer is located
        self.addr = address

        # Request the WHO_AM_I device ID byte from the accelerometer
        self._dev_id = ord (i2c.mem_read (1, address, WHO_AM_I))

        # The WHO_AM_I codes from MMA8451Q's and MMA8452Q's are recognized
        if self._dev_id == 0x1A or self._dev_id == 0x2A:
            self._works = True
        else:
            self._works = False
            raise ValueError ('Unknown accelerometer device ID ' 
                + str (self._dev_id) + ' at I2C address ' + address)

        # Ensure the accelerometer is in standby mode so we can configure it
        self.standby ()

        # Set the acceleration range to the given one if it's legal
        # self.set_range (accel_range)


    def active (self):
        """! Put the MMA845x into active mode so that it takes data. In active
        mode, the accelerometer's settings can't be messed with. Active mode
        is set by setting the @c ACTIVE bit in register @c CTRL_REG1 to one.
        """

        if self._works:
            reg1 = ord (self.i2c.mem_read (1, self.addr, CTRL_REG1))
            reg1 |= 0x01
            self.i2c.mem_write (chr (reg1), self.addr, CTRL_REG1)


    def standby (self):
        """! Put the MMA845x into standby mode so its settings can be changed.
        No data will be taken in standby mode, so before measurements are to
        be made, one must call @c active(). """

        if self._works:
            reg1 = ord (self._i2c.mem_read (1, self._addr, CTRL_REG1))
            reg1 &= ~0x01
            self._i2c.mem_write (chr (reg1 & 0xFF), self._addr, CTRL_REG1)


    def get_ax_bits (self):
        """! Get the X acceleration from the accelerometer in A/D bits and 
        return it.
        @return The measured X acceleration in A/D conversion bits """

        print ('MMA845x clueless about X acceleration')
        return 0


    def get_ay_bits (self):
        """! Get the Y acceleration from the accelerometer in A/D bits and 
        return it.
        @return The measured Y acceleration in A/D conversion bits """

        print ('MMA845x clueless about Y acceleration')
        return 0


    def get_az_bits (self):
        """! Get the Z acceleration from the accelerometer in A/D bits and 
        return it.
        @return The measured Z acceleration in A/D conversion bits """

        print ('MMA845x clueless about Z acceleration')
        return 0


    def get_ax (self):
        """! Get the X acceleration from the accelerometer in g's, assuming
        that the accelerometer was correctly calibrated at the factory.
        @return The measured X acceleration in g's """

        print ('MMA845x uncalibrated X')
        return 0


    def get_ay (self):
        """! Get the Y acceleration from the accelerometer in g's, assuming
        that the accelerometer was correctly calibrated at the factory. The
        measurement is adjusted for the range (2g, 4g, or 8g) setting.
        @return The measured Y acceleration in g's """

        print ('MMA845x uncalibrated Y')
        return 0


    def get_az (self):
        """! Get the Z acceleration from the accelerometer in g's, assuming
        that the accelerometer was correctly calibrated at the factory. The
        measurement is adjusted for the range (2g, 4g, or 8g) setting.
        @return The measured Z acceleration in g's """

        print ('MMA845x uncalibrated Z')
        return 0


    def get_accels (self):
        """! Get all three accelerations from the MMA845x accelerometer. The
        measurement is adjusted for the range (2g, 4g, or 8g) setting.
        @return A tuple containing the X, Y, and Z accelerations in g's """

        return (self.get_ax (), self.get_ay (), self.get_az ())


    def __repr__ (self):
        """! 'Convert' The MMA845x accelerometer to a string. The string 
        contains information about the configuration and status of the
        accelerometer. 
        @return A string containing diagnostic information """

        if not self._works:
            return ('No working MMA845x at I2C address ' + str (self.addr))
        else:
            reg1 = ord (self.i2c.mem_read (1, self.addr, CTRL_REG1))
            diag_str = 'MMA845' + str (self._dev_id >> 4) \
                + ': I2C address ' + hex (self.addr) \
                + ', Range=' + str (1 << (self._range + 1)) + 'g, Mode='
            diag_str += 'active' if reg1 & 0x01 else 'standby'

            return diag_str



