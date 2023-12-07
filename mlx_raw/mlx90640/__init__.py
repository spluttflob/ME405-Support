## @file __init__.py
#  This file contains a class which controls an MLX90640 thermal infrared
#  camera.
#
#  RAW VERSION
#  This version is a stripped down MLX90640 driver which produces only raw
#  data, not calibrated data, in order to save memory.

from gc import collect, mem_free
from ucollections import namedtuple
from mlx90640.regmap import (
    REGISTER_MAP,
    EEPROM_MAP,
    RegisterMap,
    CameraInterface,
    REG_SIZE,
    EEPROM_ADDRESS,
    EEPROM_SIZE,
)
# from mlx90640.calibration import CameraCalibration, TEMP_K
from mlx90640.image import RawImage, Subpage, get_pattern_by_id


class CameraDetectError(Exception):
    pass


## Detect the MLX90640 camera with the assumption that it is the only device on
#  the I2C interface.
#  @returns A reference to a new MLX90640 object which has been created
def detect_camera(i2c):

    scan = i2c.scan()
    if len(scan) == 0:
        raise CameraDetectError("No camera detected")
    if len(scan) > 1:
        scan = ", ".join(hex(s) for s in scan)
        raise CameraDetectError(f"Multiple devices on I2C bus: {scan}")
    cam_addr = scan[0]
    return MLX90640(i2c, cam_addr)


class RefreshRate:
    values = tuple(range(8))

    @classmethod
    def get_freq(cls, value):
        return 2.0**(value - 1)

    @classmethod
    def from_freq(cls, freq):
        _, value = min(
            (abs(freq - cls.get_freq(v)), v)
            for v in cls.values
        )
        return value


# container for momentary state needed for image compensation
CameraState = namedtuple('CameraState',
                         ('vdd', 'ta', 'ta_r', 'gain', 'gain_cp'))


class DataNotAvailableError(Exception):
    pass


class MLX90640:

    def __init__(self, i2c, addr):
        self.iface = CameraInterface(i2c, addr)
        self.registers = RegisterMap(self.iface, REGISTER_MAP)
        self.eeprom = RegisterMap(self.iface, EEPROM_MAP, readonly=True)
        self.calib = None
        self.raw = None
#         self.image = None
        self.last_read = None


    def setup(self, *, calib=None, raw=None, image=None):
        # We've been having some memory allocation errors which usually happen
        # as this method runs. As a workaround, run gc.collect() to keep memory
        # cleaned up, as when the process is finished, there is more free
        # memory available. Also running from frozen bytecode helps a lot
#         self.calib = calib or CameraCalibration(self.iface, self.eeprom)
        self.raw = raw or RawImage()
        collect()
#         self.image = image or ProcessedImage(self.calib)


    @property
    def refresh_rate(self):
        return RefreshRate.get_freq(self.registers['refresh_rate'])

    @refresh_rate.setter
    def refresh_rate(self, freq):
        self.registers['refresh_rate'] = RefreshRate.from_freq(freq)


    def get_pattern(self):
        return get_pattern_by_id(self.registers['read_pattern'])


    def set_pattern(self, pat):
        self.registers['read_pattern'] = pat.pattern_id


    ## Turned off to save memory for raw driver version.
    def read_vdd(self):
        # supply voltage calculation (delta Vdd)
        # type: (self) -> float
        vdd_pix = self.registers['vdd_pix'] * self._adc_res_corr()
#         return float(vdd_pix - self.calib.vdd_25)/self.calib.k_vdd
        return float(vdd_pix)


    ## Turned off to save memory for raw driver version.
    def _adc_res_corr(self):
        # type: (self) -> float
#         res_exp = self.calib.res_ee - self.registers['adc_resolution']
#         return 1 << res_exp
        return 0


    ## Turned off to save memory for raw driver version.
    def read_ta(self):
        # ambient temperature calculation (delta Ta in degC)
        # type: (self) -> float
        v_ptat = self.registers['ta_ptat']
        v_be = self.registers['ta_vbe']
#         v_ptat_art = v_ptat/(v_ptat*self.calib.alpha_ptat + v_be) * 262144
# 
#         v_ta = v_ptat_art/(1.0 + self.calib.kv_ptat*self.read_vdd() - self.calib.ptat_25)

        # print('v_ptat: ', v_ptat)
        # print('v_be:', v_be)
        # print('v_ptat_art: ', v_ptat_art)

#         return v_ta/self.calib.kt_ptat
        return 0.0


    ## Turned off to save memory for raw driver version.
    def read_gain(self):
        # gain calculation
        # type: (self) -> float
#         return self.calib.gain / self.registers['gain']
        return float(self.registers['gain'])


    # tr - temperature of reflected environment
    def read_state(self, *, tr=None):
        """!
        """
        gain = self.read_gain()
        cp_sp_0 = gain * self.registers['cp_sp_0']
        cp_sp_1 = gain * self.registers['cp_sp_1']

        ta = self.read_ta()

        ta_abs = ta + 25
#         if self.calib.emissivity == 1:
        ta_r = (ta_abs + TEMP_K)**4
#         else:
#             tr = tr if tr is not None else ta_abs - 8
#             ta_k4 = (ta_abs + TEMP_K)**4
#             tr_k4 = (tr + TEMP_K)**4
#             ta_r = tr_k4 - (tr_k4 - ta_k4)/self.calib.emissivity

        return CameraState(
            vdd = self.read_vdd(),
            ta = ta,
            ta_r = ta_r,
            gain = gain,
            gain_cp = (cp_sp_0, cp_sp_1),
        )


    ## Report whether there's data available from the camera.
    @property
    def has_data(self):
        return bool(self.registers['data_available'])


    @property
    def last_subpage(self):
        return self.registers['last_subpage']


    def read_image(self, sp_id = None):
        if not self.has_data:
            raise DataNotAvailableError

        if sp_id is None:
            sp_id = self.last_subpage

        subpage = Subpage(self.get_pattern(), sp_id)
        self.last_read = subpage

        # print(f"read SP {subpage.id}")
        self.raw.read(self.iface, subpage.sp_range())
        self.registers['data_available'] = 0
        return self.raw


#     def process_image(self, sp_id = None, state = None):
#         """!
#         """
#         if self.last_read is None:
#             raise DataNotAvailableError
# 
#         subpage = self.last_read
#         if sp_id is not None:
#             subpage.id = sp_id
# 
#         state = state or self.read_state()
# 
#         # print(f"process SP {subpage.id}")
#         raw_data = ((idx, self.raw[idx]) for idx in subpage.sp_range())
#         self.image.update(raw_data, subpage, state)
#         return self.image


