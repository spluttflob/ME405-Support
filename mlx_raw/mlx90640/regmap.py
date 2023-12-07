## MLX90640 register mapping

from mlx90640.utils import (
    field_desc,
    FieldDesc,
    FD_BYTE,
    FD_WORD,
    Struct,
    StructProto,
)


REG_SIZE = const(2)

REGISTER_MAP = {
    # Status Register
    0x8000 : (
        field_desc('last_subpage',      3, 0),
        field_desc('data_available',    1, 3),
        field_desc('overwrite_enable',  1, 4),
    ),

    # Control Register 1
    0x800D : (
        field_desc('subpage_enable',    1,  0),
        field_desc('data_hold',         1,  2),
        field_desc('subpage_repeat',    1,  3),
        field_desc('repeat_select',     3,  4),
        field_desc('refresh_rate',      3,  7),
        field_desc('adc_resolution',    2, 10),
        field_desc('read_pattern',      1, 12),
    ),

    # I2C Config Register
    0x800F : (
        field_desc('fmplus_enable',     1, 0),
        field_desc('i2c_levels',        1, 1),
        field_desc('sda_current_limit', 1, 2),
    ),

    # I2C Address
    0x8010 : field_desc('i2c_address',  FD_BYTE, 1),
    0x0700 : field_desc('ta_vbe',       FD_WORD, signed=True),
    0x0708 : field_desc('cp_sp_0',      FD_WORD, signed=True),
    0x070A : field_desc('gain',         FD_WORD, signed=True),
    0x0720 : field_desc('ta_ptat',      FD_WORD, signed=True),
    0x0728 : field_desc('cp_sp_1',      FD_WORD, signed=True),
    0x072A : field_desc('vdd_pix',      FD_WORD, signed=True),
}

# Calibration Data
EEPROM_ADDRESS = const(0x2400)
EEPROM_SIZE    = const(0x340)

# From table on page 21
EEPROM_MAP = {
    0x2410 : (
        field_desc('k_ptat',         4, 12),
        field_desc('scale_occ_row',  4,  8),
        field_desc('scale_occ_col',  4,  4),
        field_desc('scale_occ_rem',  4,  0),
    ),
    0x2411 : field_desc('pix_os_average', FD_WORD, signed=True),
    0x2420 : (
        field_desc('alpha_scale',    4, 12),
        field_desc('scale_acc_row',  4,  8),
        field_desc('scale_acc_col',  4,  4),
        field_desc('scale_acc_rem',  4,  0),
    ),
    0x2421 : field_desc('pix_sensitivity_average', FD_WORD),
    0x2430 : field_desc('gain',    FD_WORD, signed=True),
    0x2431 : field_desc('ptat_25', FD_WORD, signed=True),
    0x2432 : (
        field_desc('kv_ptat',  6, 10, signed=True),
        field_desc('kt_ptat', 10,  0, signed=True),
    ),
    0x2433 : (
        field_desc('k_vdd', FD_BYTE, 1, signed=True),
        field_desc('vdd_25', FD_BYTE, 0),
    ),
    0x2434 : (
        field_desc('kv_avg_ro_co', 4, 12, signed=True),
        field_desc('kv_avg_re_co', 4,  8, signed=True),
        field_desc('kv_avg_ro_ce', 4,  4, signed=True),
        field_desc('kv_avg_re_ce', 4,  0, signed=True),
    ),
    0x2435 : (
        field_desc('il_chess_c3', 5, 11, signed=True),
        field_desc('il_chess_c2', 5,  6, signed=True),
        field_desc('il_chess_c1', 6,  0, signed=True),
    ),
    0x2436 : (
        field_desc('kta_avg_ro_co', FD_BYTE, 1, signed=True),
        field_desc('kta_avg_re_co', FD_BYTE, 0, signed=True),
    ),
    0x2437 : (
        field_desc('kta_avg_ro_ce', FD_BYTE, 1, signed=True),
        field_desc('kta_avg_re_ce', FD_BYTE, 0, signed=True),
    ),
    0x2438 : (
        field_desc('res_ctrl_cal', 2, 12),
        field_desc('kv_scale',     4,  8),
        field_desc('kta_scale_1',  4,  4),
        field_desc('kta_scale_2',  4,  0),
    ),
    0x2439 : (
        field_desc('cp_sp_ratio',    6, 10, signed=True),
        field_desc('alpha_cp_sp_0', 10,  0),
    ),
    0x243A : (
        field_desc('offset_cp_delta',  6, 10, signed=True),
        field_desc('offset_cp_sp_0',  10,  0, signed=True),
    ),
    0x243B : (
        field_desc('kv_cp',  FD_BYTE, 1, signed=True),
        field_desc('kta_cp', FD_BYTE, 0, signed=True),
    ),
    0x243C : (
        field_desc('ksta',   FD_BYTE, 1, signed=True),
        field_desc('tgc',    FD_BYTE, 0),
    ),
    0x243D : (
        field_desc('ksto_2', FD_BYTE, 1, signed=True),
        field_desc('ksto_1', FD_BYTE, 0, signed=True),
    ),
    0x243E : (
        field_desc('ksto_4', FD_BYTE, 1, signed=True),
        field_desc('ksto_3', FD_BYTE, 0, signed=True),
    ),
    0x243F : (
        field_desc('step',       2, 12),
        field_desc('ct4',        4,  8),
        field_desc('ct3',        4,  4),
        field_desc('ksto_scale', 4,  0),
    ),
}

import time
class CameraInterface:
    def __init__(self, i2c, addr):
        self.i2c = i2c   # HW interface
        self.addr = addr # device address

    ## raw register read/write

    def read(self, mem_addr):
        return self.i2c.readfrom_mem(self.addr, mem_addr, 2, addrsize=16)
    def read_into(self, mem_addr, buf):
        self.i2c.readfrom_mem_into(self.addr, mem_addr, buf, addrsize=16)
    def write(self, mem_addr, buf):
        self.i2c.writeto_mem(self.addr, mem_addr, buf, addrsize=16)


class ReadOnlyError(Exception): pass

class RegisterMap:
    def __init__(self, iface, register_map, readonly=False):
        # register_map should be a dict of { I2C address : FieldDesc(s) }
        self.iface = iface
        self.readonly = readonly
        self._fields = self._build_lookup(register_map)

    @staticmethod
    def _build_lookup(register_map):
        lookup = {}
        for address, fields in register_map.items():
            if isinstance(fields, FieldDesc):
                fields = (fields,)

            proto = StructProto(fields)
            for fld in fields:
                if fld.name in lookup:
                    raise ValueError(f"duplicate field name: {fld.name}")
                lookup[fld.name] = (address, proto)

        return lookup

    def __iter__(self):
        return iter(self.keys())
    def __len__(self):
        return len(self._fields)
    def __contains__(self, name):
        return name in self._fields

    def __getitem__(self, name):
        address, proto = self._fields[name]

        buf = self.iface.read(address)
        struct = Struct(buf, proto)
        return struct[name]

    def __setitem__(self, name, value):
        if self.readonly:
            raise ReadOnlyError(f"can't write to '{name}': not permitted")

        address, proto = self._fields[name]

        buf = bytearray(REG_SIZE)
        self.iface.read_into(address, buf)
        struct = Struct(buf, proto)
        struct[name] = value
        self.iface.write(address, buf)
