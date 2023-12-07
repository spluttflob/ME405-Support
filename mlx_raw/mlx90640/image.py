## @file image.py
#  This file contains image storage and processing classes for the MLX90640 camera
#  driver.
#
#  RAW VERSION
#  This version is a stripped down MLX90640 driver which produces only raw data,
#  not calibrated data, in order to save memory.

import math
import struct
from array import array
from ucollections import namedtuple
from mlx90640.utils import (Struct, StructProto, field_desc, array_filled)

from mlx90640.regmap import REG_SIZE
from mlx90640.calibration import NUM_COLS, IMAGE_SIZE, TEMP_K


PIX_STRUCT_FMT = '>h'
PIX_DATA_ADDRESS = const(0x0400)


class _BasePattern:
    @classmethod
    def sp_range(cls, sp_id):
        return (
            idx for idx, sp in enumerate(cls.iter_sp()) 
            if sp == sp_id
        )

    @classmethod
    def iter_sp(cls):
        return (
            cls.get_sp(idx) for idx in range(IMAGE_SIZE)
        )


class ChessPattern(_BasePattern):
    pattern_id = 0x1

    @classmethod
    def get_sp(cls, idx):
        return (idx//32 - (idx//64)*2) ^ (idx - (idx//2)*2)


class InterleavedPattern(_BasePattern):
    pattern_id = 0x0

    @classmethod
    def get_sp(cls, idx):
        return idx//32 - (idx//64)*2


_READ_PATTERNS = {
    pat.pattern_id : pat for pat in (ChessPattern, InterleavedPattern)
}


def get_pattern_by_id(pattern_id):
    return _READ_PATTERNS.get(pattern_id)


class Subpage:
    def __init__(self, pattern, sp_id):
        self.pattern = pattern
        self.id = sp_id

    def sp_range(self):
        return self.pattern.sp_range(self.id)


## Image Buffers

class RawImage:
    def __init__(self):
        self.pix = array_filled('h', IMAGE_SIZE)

    def __getitem__(self, idx):
        return self.pix[idx]

    def read(self, iface, update_idx = None):
        buf = bytearray(REG_SIZE)
        update_idx = update_idx or range(IMAGE_SIZE)
        for offset in update_idx:
            iface.read_into(PIX_DATA_ADDRESS + offset, buf)
            self.pix[offset] = struct.unpack(PIX_STRUCT_FMT, buf)[0]


ImageLimits = namedtuple('ScaleLimits', ('min_h', 'max_h', 'min_idx', 'max_idx'))


_INTERP_NEIGHBOURS = tuple(
    row * NUM_COLS + col
    for row in (-1, 0, 1)
    for col in (-1, 0, 1)
    if row != 0 or col != 0
)


# class ProcessedImage:
#     def __init__(self, calib):
#         # pix_data should be a sequence of ints
#         self.calib = calib
#         self.v_ir = array_filled('f', IMAGE_SIZE, 0.0)
#         self.alpha = array_filled('f', IMAGE_SIZE, 1.0)
#         self.buf = array_filled('f', IMAGE_SIZE, 1.0)
# 
#     def update(self, pix_data, subpage, state):
#         if self.calib.use_tgc:
#             pix_os_cp = self._calc_os_cp(subpage, state)
#             pix_alpha_cp = self.calib.pix_alpha_cp[subpage.id]
# 
#         for idx, raw in pix_data:
#             ## IR data compensation - offset, Vdd, and Ta
#             kta = self.calib.pix_kta[idx]
# 
#             row, col = divmod(idx, NUM_COLS)
#             kv = self.calib.kv_avg[row % 2][col % 2]
#             
#             offset = self.calib.pix_os_ref[idx]
#             offset *= (1 + kta*state.ta)*(1 + kv*state.vdd)
# 
#             v_os = raw*state.gain - offset
#             if subpage.pattern is InterleavedPattern:
#                 v_os += self.calib.il_offset[idx]
#             v_ir = v_os / self.calib.emissivity
# 
#             ## IR data gradient compensation
#             if self.calib.use_tgc:
#                 v_ir -= self.calib.tgc*pix_os_cp
# 
#             # preserve v_ir for temperature calculations
#             self.v_ir[idx] = v_ir
# 
#             alpha = self._calc_alpha(idx, state.ta)
#             self.buf[idx] = v_ir/alpha
# 
#     def _calc_os_cp(self, subpage, state):
#         pix_os_cp = self.calib.pix_os_cp[subpage.id]
#         if subpage.pattern is InterleavedPattern:
#             pix_os_cp += self.calib.il_chess_c1
#         return state.gain_cp[subpage.id] - pix_os_cp*(1 + self.calib.kta_cp*state.ta)*(1 + self.calib.kv_cp*state.vdd)
# 
#     def _calc_os_cp2(self, pattern, state):
#         pix_os_cp = list(self.calib.pix_os_cp)
#         if pattern is InterleavedPattern:
#             for i in range(len(pix_os_cp)):
#                 pix_os_cp[i] += self.calib.il_chess_c1
# 
#         k = (1 + self.calib.kta_cp*state.ta)*(1 + self.calib.kv_cp*state.vdd)
#         return [
#             gain_cp_sp - pix_os_cp_sp*k
#             for pix_os_cp_sp, gain_cp_sp in zip(pix_os_cp, state.gain_cp)
#         ]
# 
#     def _calc_alpha(self, idx, ta):
#         alpha = self.calib.pix_alpha[idx]
#         if self.calib.use_tgc:
#             alpha -= self.calib.tgc*pix_alpha_cp
#         alpha *= (1 + self.calib.ksta*ta)
#         return alpha
# 
#     def _calc_to(self, idx, alpha, ta_r):
#         v_ir = self.v_ir[idx]
# 
#         s_x = v_ir*(alpha**3) + ta_r*(alpha**4)
#         s_x = math.sqrt(math.sqrt(s_x))*self.calib.ksto[1]
# 
#         to = v_ir/(alpha*(1 - TEMP_K*self.calib.ksto[1]) + s_x) + ta_r
#         to = math.sqrt(math.sqrt(to)) - TEMP_K
#         return to + self.calib.drift
# 
#     def calc_temperature(self, idx, state):
#         alpha = self._calc_alpha(idx, state.ta)
#         return self._calc_to(idx, alpha, state.ta_r)
# 
#     def calc_temperature_ext(self, idx, state):
#         v_ir = self.v_ir[idx]
#         alpha = self._calc_alpha(idx, state.ta)
#         to = self._calc_to(idx, alpha, state.ta_r)
# 
#         band = self._get_range_band(to)
#         if band < 0:
#             return self.calib.ct[0]
# 
#         alpha_ext = self.calib.alpha_ext[band]
#         ksto_ext = self.calib.ksto[band]
#         ct = self.calib.ct[band]
#         to_ext = v_ir/(alpha*alpha_ext*(1 + ksto_ext*(to - ct))) + state.ta_r
#         to_ext = math.sqrt(math.sqrt(to_ext)) - TEMP_K
#         return to_ext  + self.calib.drift
# 
#     def _get_range_band(self, t):
#         return sum(1 for ct in self.calib.ct if t >= ct) - 1
# 
#     def calc_limits(self, *, exclude_idx=()):
#         # find min/max in place to keep mem usage down
#         min_h, min_idx = None, None
#         max_h, max_idx = None, None
#         for idx, h in enumerate(self.buf):
#             if idx in exclude_idx:
#                 continue
#             if min_h is None or h < min_h:
#                 min_h, min_idx = h, idx
#             if max_h is None or h > max_h:
#                 max_h, max_idx = h, idx
#         return ImageLimits(min_h, max_h, min_idx, max_idx)
# 
#     def interpolate_bad_pixels(self, bad_pixels):
#         for bad_idx in bad_pixels:
#             count = 0
#             total = 0
#             for offset in _INTERP_NEIGHBOURS:
#                 idx = bad_idx + offset
#                 if idx in range(IMAGE_SIZE) and idx not in bad_pixels:
#                     count += 1
#                     total += self.buf[idx]
#             if count > 0:
#                 self.buf[bad_idx] = total/count
