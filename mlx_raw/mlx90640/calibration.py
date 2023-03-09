from array import array
from mlx90640.utils import (
    Struct, 
    StructProto,
    field_desc,
)
from mlx90640.regmap import REG_SIZE

NUM_ROWS = const(24)
NUM_COLS = const(32)
IMAGE_SIZE = const(24*32)

OCC_ROWS_ADDRESS = const(0x2412)
OCC_COLS_ADDRESS = const(0x2418)

ACC_ROWS_ADDRESS = const(0x2422)
ACC_COLS_ADDRESS = const(0x2428)

CC_PROTO = StructProto((
    field_desc('0', 4,  0, signed=True),
    field_desc('1', 4,  4, signed=True),
    field_desc('2', 4,  8, signed=True),
    field_desc('3', 4, 12, signed=True),
))

def _read_cc_iter(iface, base, size):
    buf = bytearray(REG_SIZE)
    struct = Struct(buf, CC_PROTO)
    for addr_off in range(size // 4):
        cc_addr = base + addr_off
        iface.read_into(cc_addr, buf)
        yield struct['0']
        yield struct['1']
        yield struct['2']
        yield struct['3']

def read_occ_rows(iface):
    return _read_cc_iter(iface, OCC_ROWS_ADDRESS, NUM_ROWS)
def read_occ_cols(iface):
    return _read_cc_iter(iface, OCC_COLS_ADDRESS, NUM_COLS)

def read_acc_rows(iface):
    return _read_cc_iter(iface, ACC_ROWS_ADDRESS, NUM_ROWS)
def read_acc_cols(iface):
    return _read_cc_iter(iface, ACC_COLS_ADDRESS, NUM_COLS)

PIX_CALIB_PROTO = StructProto((
    field_desc('offset',  6, 10, signed=True),
    field_desc('alpha',   6,  4, signed=True),
    field_desc('kta',     3,  1, signed=True),
    field_desc('outlier', 1,  0),
))

PIX_CALIB_ADDRESS = const(0x2440)


class PixelCalibrationData:
    def __init__(self, iface):
        pix_count = NUM_ROWS * NUM_COLS
        self._data = bytearray(pix_count * REG_SIZE)

        failed = []
        buf = bytearray(REG_SIZE)
        for idx in range(pix_count):
            offset = idx * REG_SIZE
            iface.read_into(PIX_CALIB_ADDRESS + offset, buf)
            if buf != bytes(REG_SIZE):
                self._data[offset:offset+REG_SIZE] = buf
            else:
                failed.append(idx)
        self.failed = tuple(failed)

    def __len__(self):
        return len(self._data)//REG_SIZE
    def __getitem__(self, idx):
        offset = idx * REG_SIZE
        return Struct(self._data[offset:offset+REG_SIZE], PIX_CALIB_PROTO)
    def __iter__(self):
        for idx in range(len(self)):
            yield self[idx]

TEMP_K = 273.15

class CameraCalibration:
    def __init__(self, iface, eeprom, *, emissivity=1, use_tgc=False):
        self.emissivity = emissivity

        # restore VDD sensor parameters
        self.k_vdd = eeprom['k_vdd'] * 32
        self.vdd_25 = (eeprom['vdd_25'] - 256) * 32 - 8192

        # resolution control
        self.res_ee = eeprom['res_ctrl_cal']

        # ambient temperature
        self.kv_ptat = eeprom['kv_ptat'] / 4096.0
        self.kt_ptat = eeprom['kt_ptat'] / 8.0
        self.ptat_25 = eeprom['ptat_25']
        self.alpha_ptat = eeprom['k_ptat'] / 4.0 + 8.0

        # gain
        self.gain = eeprom['gain']

        # pixel calibration data
        self.pix_data = PixelCalibrationData(iface)
        self.pix_os_ref = array('h', self._calc_pix_os_ref(iface, eeprom))
        self.outliers = tuple(idx for idx, data in enumerate(self.pix_data) if data['outlier'])

        # IR data compensation
        self.kta_scale_1 = 1 << (eeprom['kta_scale_1'] + 8)
        self.kta_scale_2 = 1 << eeprom['kta_scale_2']
        self.pix_kta = array('f', self._calc_pix_kta(eeprom))

        self.kv_scale = 1 << eeprom['kv_scale']
        self.kv_avg = (
            # index by [row % 2][col % 2]
            (eeprom['kv_avg_re_ce']/self.kv_scale, eeprom['kv_avg_re_co']/self.kv_scale),
            (eeprom['kv_avg_ro_ce']/self.kv_scale, eeprom['kv_avg_ro_co']/self.kv_scale),
        )
        
        # IR gradient compensation

        # tgc only available for device type 'C'
        self.use_tgc = use_tgc

        if use_tgc:
            self.tgc = eeprom['tgc'] / 32.0 if use_tgc else False

            offset_cp_sp_0 = eeprom['offset_cp_sp_0']
            offset_cp_sp_1 = offset_cp_sp_0 + eeprom['offset_cp_delta']
            self.pix_os_cp = (offset_cp_sp_0, offset_cp_sp_1)

            self.kta_cp = eeprom['kta_cp'] / self.kta_scale_1
            self.kv_cp = eeprom['kv_cp'] / self.kv_scale

        # sensitivity normalization
        self.pix_alpha = array('f', self._calc_pix_alpha_ref(iface, eeprom))
        self.ksta = eeprom['ksta'] / 8192.0

        if use_tgc:
            alpha_scale_cp = 1 << (eeprom['alpha_scale'] + 27)
            cp_sp_ratio = eeprom['cp_sp_ratio']
            pix_alpha_cp_sp_0 = eeprom['alpha_cp_sp_0'] / alpha_scale_cp
            pix_alpha_cp_sp_1 = pix_alpha_cp_sp_0*(1 + cp_sp_ratio/128.0)
            self.pix_alpha_cp = (pix_alpha_cp_sp_0, pix_alpha_cp_sp_1)

        # interleaved pattern
        self.il_chess_c1 = eeprom['il_chess_c1'] / 16.0
        self.il_chess_c2 = eeprom['il_chess_c2'] / 2.0
        self.il_chess_c3 = eeprom['il_chess_c3'] / 8.0
        self.il_offset = array('f', self._calc_il_offset())

        # temperature calculation
        self.drift = 0  # temperature drift correction

        self.ksto_scale = 1 << (eeprom['ksto_scale'] + 8)
        ksto1 = eeprom['ksto_1'] / self.ksto_scale
        ksto2 = eeprom['ksto_2'] / self.ksto_scale
        ksto3 = eeprom['ksto_3'] / self.ksto_scale
        ksto4 = eeprom['ksto_4'] / self.ksto_scale
        self.ksto = (ksto1, ksto2, ksto3, ksto4)

        step = eeprom['step'] * 10
        ct1 = const(-40)
        ct2 = const(0)
        ct3 = eeprom['ct3'] * step
        ct4 = eeprom['ct4'] * step + ct3
        self.ct = (ct1, ct2, ct3, ct4)

        alpha_1 = 1.0/(1.0 + ksto1*(ct2 - ct1))
        alpha_2 = 1.0
        alpha_3 = (1.0 + ksto2*(ct3 - ct2))
        alpha_4 = alpha_3*(1.0 + ksto3*(ct4 - ct3))
        self.alpha_ext = (alpha_1, alpha_2, alpha_3, alpha_4)

    def _calc_pix_os_ref(self, iface, eeprom):
        offset_avg = eeprom['pix_os_average']
        occ_scale_row = 1 << eeprom['scale_occ_row']
        occ_scale_col = 1 << eeprom['scale_occ_col']
        occ_scale_rem = 1 << eeprom['scale_occ_rem']

        occ_rows = tuple(read_occ_rows(iface))
        occ_cols = tuple(read_occ_cols(iface))

        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                idx = row * NUM_COLS + col
                yield (
                    offset_avg
                    + occ_rows[row] * occ_scale_row
                    + occ_cols[col] * occ_scale_col
                    + self.pix_data[idx]['offset'] * occ_scale_rem
                )

    def _calc_pix_alpha_ref(self, iface, eeprom):
        alpha_ref = eeprom['pix_sensitivity_average']
        alpha_scale = 1 << (eeprom['alpha_scale'] + 30)
        acc_scale_row = 1 << eeprom['scale_acc_row']
        acc_scale_col = 1 << eeprom['scale_acc_col']
        acc_scale_rem = 1 << eeprom['scale_acc_rem']

        acc_rows = tuple(read_acc_rows(iface))
        acc_cols = tuple(read_acc_cols(iface))

        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                idx = row * NUM_COLS + col
                yield (
                    alpha_ref
                    + acc_rows[row] * acc_scale_row
                    + acc_cols[col] * acc_scale_col
                    + self.pix_data[idx]['alpha'] * acc_scale_rem
                ) / alpha_scale

    def _calc_pix_kta(self, eeprom):
        # index by [row % 2][col % 2]
        kta_avg = (
            (eeprom['kta_avg_re_ce'], eeprom['kta_avg_re_co']),
            (eeprom['kta_avg_ro_ce'], eeprom['kta_avg_ro_co']),
        )

        for row in range(NUM_ROWS):
            for col in range(NUM_COLS):
                idx = row * NUM_COLS + col
                kta_ee = self.pix_data[idx]['kta']
                kta_rc = kta_avg[row % 2][col % 2]
                yield (kta_rc + kta_ee * self.kta_scale_2)/self.kta_scale_1

    def _calc_il_offset(self):
        for idx in range(NUM_ROWS*NUM_COLS):
            il_pattern = idx//32 - (idx//64)*2
            conv_pattern = (
                ((idx-2)//4 - (idx-1)//4 + (idx+1)//4 - (idx-1)//4)
                * (1 - 2*il_pattern)
            )
            yield (
                self.il_chess_c3*(2*il_pattern - 1) 
                - self.il_chess_c2*conv_pattern
            )
