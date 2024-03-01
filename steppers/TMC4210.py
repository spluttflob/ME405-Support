## @file tmc4210.py
#  This file contains a driver for the TMC4210, an oddball stepper driver.

from pyb import SPI, Timer, Pin
from time import sleep


## @brief     A class for interfacing with TMC4210 stepper drivers.
#  @details    An instance of this class enables the user to interact with the
#              basic parameters required to enable and move a stepper motor
#              driven by a Trinamic TMC4210 stepper motor driver.

class TMC4210:

    ## Addresses of the registers inside the TMC4210.
    class registers:
        # Stepper Motor Register Set
        X_TARGET               = 0b0000000
        X_ACTUAL               = 0b0000001
        V_MIN                  = 0b0000010
        V_MAX                  = 0b0000011
        V_TARGET               = 0b0000100
        V_ACTUAL               = 0b0000101
        A_MAX                  = 0b0000110
        A_ACTUAL               = 0b0000111
        PMUL_PDIV              = 0b0001001
        lp_REFCONF_RM          = 0b0001010
        INTERRUPT_MASK_FLAGS   = 0b0001011
        PULSE_RAMP_DIV         = 0b0001100
        DX_REF_TOLERANCE       = 0b0001101
        X_LATCHED              = 0b0001110
        USTEP_COUNT_4210       = 0b0001111
        
        # Global Parameter Registers
        IF_CONFIGURATION_4210  = 0b0110100
        POS_COMP_4210          = 0b0110101
        POS_COMP_INT_4210_M_I  = 0b0110110
        POWER_DOWN             = 0b0111000
        TYPE_VERSION           = 0b0111001
        gp_in_r_l_r_r          = 0b0111110
        mot1r_STPDIV_4210      = 0b0111111


    ## The codes used to select motion modes for the TMC4210.
    class motion_modes:
        RAMP_MODE              = 0b00
        SOFT_MODE              = 0b01
        VELOCITY_MODE          = 0b10
        HOLD_MODE              = 0b11


    ## @brief   Initializes and returns an object corresponding to a single 
    #           Trinamic TMC4210 stepper motor driver.
    #  @details This method creates an instance of a TMC4210 stepper driver for 
    #           control of a single stepper motor.
    # @param chip_select  @c pyb.Pin object instantiated for an MCU GPIO pin in
    #           @c OUT_PP mode. Acts as active-low chip select for determining
    #           which device is being communicated with over the SPI bus.
    # @param chip_enable @c pyb.Pin object instantiated for an MCU GPIO pin in
    #           #c OUT_PP mode. Acts as an active-low enable input for the
    #           TMC2208 being controlled by the TMC4210.
    # @param serial_bus @c pyb.SPI serial bus object. Used for serial-peripheral
    #           communication between the MCU and the TMC4210.
    # @param clock @c pyb.Timer object instantiated with period=3, prescaler=4,
    #           mode=PWM, pulse_width=2) used by the TMC4210 for calculation of
    #           acceleration ramping functions.
    def __init__(self, chip_select, chip_enable, serial_bus, clock):
        
        self.send_buf = bytearray(4)
        self.recv_buf = bytearray(4)
        # Movement parameters
        self.ramp_div = 8
        self.pulse_div = 8
        
        #Enable and Chip Select Pin Configuration
        self.ENN = Pin(chip_enable, mode=Pin.OUT_PP)
        self.CS  = Pin(chip_select, mode=Pin.OUT_PP)
        
        #SPI Bus Configuration
        self.spi = serial_bus
        self.CLK = clock

        # Set ENN pins high in preparation for instantiating SPI object
        self.ENN.low()  #The 2208 is active low; enable on startup
        self.CS.high()  #Active low; only activate when communicating with chip
        
        # Initialize acceleration ramp parameters to Nonetype
        (self.PMUL, self.PDIV, _) = self.calc_PMUL_PDIV(255,
                                                        self.ramp_div,
                                                        self.pulse_div)

        # Configure the settings
        self.EN_SD          = True
        self.V_MIN          = 1
        self.V_MAX          = 1288
        self.PULSE_RAMP_DIV = self.pulse_div, self.ramp_div
        self.RM             = self.motion_modes.RAMP_MODE
        self.A_MAX          = 255
        self.PMUL_PDIV      = self.PMUL, self.PDIV
        
    
    ## @brief   Reads the TMC4210 data register associated with the input
    #           address.
    #  @details Method takes in a 7-bit TMC4210 register address, appends the
    #           read bit to the end of the address, places it in a byte array,
    #           and communicates that array to the device over the SPI bus.
    #  @param   address 7-bit TMC4210 register address (integer equivalent also
    #           acceptable)
    #  @return  A tuple containing the returned status byte as the first
    #           element and the returned 3-byte data as the second element
    #
    def readRegister(self, address):
        self.send_buf = bytearray([address<<1|1,
                                   0b00000000,
                                   0b00000000,
                                   0b00000000])

        self.CS.low()
        self.spi.send_recv(self.send_buf, self.recv_buf)
        self.CS.high()
        
        return (self.recv_buf[0], self.recv_buf[1:])


    ## @brief    Reads the TMC4210 data register associated with the input
    #            address.
    #  @details  Method takes in a 7-bit TMC4210 register address, appends the 
    #            read bit to the end of the address, places it in a byte array,
    #            and communicates that array to the device over the SPI bus.
    #  @param    address 7-bit TMC4210 register address (integer equivalent
    #            also acceptable)
    #  @param    data A bytearray or bytes object holding 3 data bytes to send
    #  @return   The returned status byte
    #
    def writeRegister(self, address,data):

        if len(data) != 3:
            raise ValueErrror('Register data must be 3 bytes')
            
        self.send_buf = bytearray([address<<1|0]) + data
        
        self.CS.low()
        self.spi.send_recv(self.send_buf, self.recv_buf)
        self.CS.high()

        return self.recv_buf[0]


    # ######### X_TARGET Register ##########
    @property
    def X_TARGET(self):
        status, data = self.readRegister(self.registers.X_TARGET)
        return int.from_bytes(data, 'big', True), status
    
    @X_TARGET.setter
    def X_TARGET(self, position):
        if type(position) is not int:
            raise TypeError('Position value must be a 24-bit integer')
        if position >= 2**23 or position < -2**23:
            raise ValueError('Position value must be a 24-bit integer')
        status = self.writeRegister(self.registers.X_TARGET,
                                    position.to_bytes(3, 'big', 'true'))
        return status


    # ######### X_ACTUAL Register ##########
    @property
    def X_ACTUAL(self):
        status, data = self.readRegister(self.registers.X_ACTUAL)
        return int.from_bytes(data, 'big', True), status
    
    @X_ACTUAL.setter
    def X_ACTUAL(self, position):
        if type(position) is not int:
            raise TypeError('Position value must be a 24-bit integer')
        if position >= 2**23 or position < -2**23:
            raise ValueError('Position value must be a 24-bit integer')
        status = self.writeRegister(self.registers.X_ACTUAL,
                                    position.to_bytes(3, 'big', 'true'))
        return int.from_bytes(data, 'big', True), status


    # ######### V_MIN REGISTER ########
    @property
    def V_MIN(self):
        status, data = self.readRegister(self.registers.V_MIN)
        return int.from_bytes(data, 'big', False), status
    
    @V_MIN.setter
    def V_MIN(self, velocity):
        if type(velocity) is not int:
            raise TypeError('Velocity value must be an 11-bit integer')
        if velocity >= 2**11:
            raise ValueError('Velocity value must be a 11-bit integer')
        status = self.writeRegister(self.registers.V_MIN,
                                    velocity.to_bytes(3, 'big', 'false'))
        return status


    # ######### V_MAX REGISTER ########
    @property
    def V_MAX(self):
        status, data = self.readRegister(self.registers.V_MAX)
        return int.from_bytes(data, 'big', False), status
    
    @V_MAX.setter
    def V_MAX(self velocity):
        if type(velocity) is not int:
            raise TypeError('Velocity value must be an 11-bit integer')
        if velocity >= 2**11:
            raise ValueError('Velocity value must be a 11-bit integer')
        status = self.writeRegister(self.registers.V_MAX,
                                    velocity.to_bytes(3, 'big', 'false'))
        return status


    # ######### A_MAX REGISTER ########
    @property
    def A_MAX(self):
        status, data = self.readRegister(self.registers.A_MAX)
        return int.from_bytes(data, 'big', False), status
    
    @A_MAX.setter
    def A_MAX(self, acceleration):
        if type(acceleration) is not int:
            raise TypeError('Acceleration value must be an 11-bit integer')
        if acceleration >= 2**11:
            raise ValueError('Acceleration value must be an 11-bit integer')
        status = self.writeRegister(self.registers.A_MAX,
                                    acceleration.to_bytes(3, 'big', 'false'))
        return status


    # ######### PMUL_PDIV Register
    @property
    def PMUL_PDIV(self):
        status, data = self.readRegister(self.registers.PMUL_PDIV)
        return data[1], data[2] & 0x0F, status
    
    @PMUL_PDIV.setter
    def PMUL_PDIV(self, PMUL_PDIV):
        try:
            PMUL, PDIV = PMUL_PDIV
        except ValueError:
            raise ValueError('PMUL and PDIV must be passed in as an iterable')

        if type(PMUL) is not int:
            raise TypeError('PMUL must be an integer')
        if not (127 < PMUL <= 255):
            raise ValueError('PMUL must be an integer between 128 and 255 inclusive')

        if type(PDIV) is not int:
            raise TypeError('PDIV must be an integer')
        if not (0 < PDIV <= 15):
            raise ValueError('PDIV must be an integer between 0 and 15 inclusive')

        status = self.writeRegister(self.registers.PMUL_PDIV,
                                    bytearray([0,
                                               PMUL,
                                               PDIV]))
        return status


    # ######### PULSE_RAMP_DIV Register
    @property
    def PULSE_RAMP_DIV(self):
        status, data = self.readRegister(self.registers.PULSE_RAMP_DIV)
        return (data[2] & 0xF0) >> 4, data[2] & 0x0F, status
    
    @PULSE_RAMP_DIV.setter
    def PULSE_RAMP_DIV(self, PULSE_RAMP_DIV):
        try:
            PULSE_DIV, RAMP_DIV = PULSE_RAMP_DIV
        except ValueError:
            raise ValueError('PULSE_DIV and RAMP_DIV must be passed in as an iterable')

        if type(PULSE_DIV) is not int:
            raise TypeError('PULSE_DIV must be an integer')
        if not (0 < PULSE_DIV <= 15):
            raise ValueError('PULSE_DIV must be an integer between 128 and 255 inclusive')

        if type(RAMP_DIV) is not int:
            raise TypeError('RAMP_DIV must be an integer')
        if not (0 < RAMP_DIV <= 15):
            raise ValueError('RAMP_DIV must be an integer between 0 and 15 inclusive')

        status = self.writeRegister(self.registers.PULSE_RAMP_DIV,
                                    bytearray([0,
                                               PULSE_DIV<<4 | RAMP_DIV,
                                               0]))
        return status


    ## ######## IF_CONFIGURATION_4210 REGISTER ########
    @property
    def EN_SD(self):
        status, data = self.readRegister(self.registers.IF_CONFIGURATION_4210)
        return bool(data[2] & 1<<5), status
    
    @EN_SD.setter
    def EN_SD(self, en):
        if type(en) is not bool:
            raise TypeError('Enable input must be a boolean')
        _, data = self.readRegister(self.registers.IF_CONFIGURATION_4210)
        status = self.writeRegister(self.registers.IF_CONFIGURATION_4210,
                                    bytearray([data[0],
                                               data[1],
                                               (data[2] & ~(1 << 5)) | en << 5]))
        
        return status


    # ######### lp_REFCONF_RM Register ########
    @property
    def RM(self):
        status, data = self.readRegister(self.registers.lp_REFCONF_RM)
        return bool(data[3] & 0b11), status
    
    @RM.setter
    def RM(self, RM):

        if type(RM) is not int:
            raise TypeError('RM must be an integer')
        if not (0 <= RM <= 3):
            raise ValueError('RM must be an integer between 0 and 3 inclusive')
            
        _, data = self.readRegister(self.registers.lp_REFCONF_RM)
        status = self.writeRegister(self.registers.lp_REFCONF_RM,
                                    bytearray([data[0],
                                               data[1],
                                               (data[2] & ~0b11) | RM]))
        
        return status


    ## @brief   Calculates all valid PMUL, PDIV pairs based on the current AMAX, 
    #           RAMP_DIV, and PULSE_DIV settings. Returns the first valid pair.
    #  @details This method is used to calculated a (non-optimized) valid pair
    #           of the ramping function parameters PMUL and PDIV.
    #  @param   AMAX      AMAX setting of the TMC4210
    #  @param   RAMP_DIV  Ramp divisor ramping function parameter
    #  @param   PULSE_DIV Clock divisor ramping function parameter
    #
    def calc_PMUL_PDIV(self, AMAX, RAMP_DIV, PULSE_DIV):
        p = AMAX/((128)*(2)**(RAMP_DIV-PULSE_DIV))

        q_max = 0
        for pmul in range(128, 255):
            for j in range(3, 16):
                pdiv = 2**j
                p_prime = pmul/pdiv
                q = p_prime/p
                if q > q_max and q <= 1.0:
                    q_max = q 
                    PMUL = pmul
                    PDIV = j-3
        if q_max == 0:
            raise ValueError(("The AMAX/RAMP_DIV/PULSE_DIV selection does not "
                              "result in a valid PMUL/PDIV output."))

        return PMUL, PDIV, q_max


if __name__=='__main__':
    
    # Timer signal setup
    timer = Timer(4, period=3, prescaler=0)
    CLK = timer.channel(1, pin=Pin.board.PB6, mode=Timer.PWM, pulse_width=2)

    # Set up SPI serial communication
    spi = SPI(2, SPI.CONTROLLER, baudrate = 1_000_000, polarity = 1, phase = 1)

    # Driver object(s) instantiation
    DRV1 = TMC4210(Pin.cpu.B0, Pin.board.PC3, spi, CLK)
    DRV2 = TMC4210(Pin.cpu.C0, Pin.board.PC2, spi, CLK)
