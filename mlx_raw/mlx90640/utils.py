## @file utils.py
#  @brief Buffer carving utilities for MicroPython, providing helpers for 
#  defining and accessing structured binary data.
#  This module includes:
#  - Functions for creating filled arrays and converting values to two's 
#    complement.
#  - Field descriptor utilities for defining binary layouts.
#  - Classes for describing and accessing structured binary data using field 
#    descriptors.
#  Designed for use with MicroPython and low-level sensor data parsing 
#  (e.g., MLX90640).

from array import array
from ucollections import namedtuple
from uctypes import (
    INT8, UINT8,
    INT16, UINT16,
    BFUINT16,
    BF_POS,
    BF_LEN,
    BIG_ENDIAN,
    addressof,
    struct as uc_struct,
)

def array_filled(typecode, length, fill=0):
    return array(typecode, (fill for i in range(length)))


## Convert a value to its two's complement representation for a given bit width.
#  If the value is negative, it wraps around using the bit width.
#  If the value is above the signed range, it wraps to negative.
#  @param bits: The number of bits for the two's complement representation.
#  @param value: The integer value to convert.
#  @return: The two's complement representation of the input value.
def twos_complement(bits, value):
    if value < 0:
        return value + (1 << bits)
    if value >= (1 << (bits - 1)):
        return value - (1 << bits)
    return value


FD_BYTE = object()
FD_WORD = object()


FieldDesc = namedtuple('FieldDesc', ('name', 'layout', 'signed_bits'))

##
# @brief Creates a FieldDesc object describing a field's layout in a data structure.
# 
# @param name The name of the field.
# @param bits The number of bits in the field, or a constant indicating 
#        word/byte size.
# @param pos The bit position of the field within the structure (default is 0).
# @param signed Boolean indicating if the field is signed (default is False).
# @return FieldDesc object representing the field's layout and properties.
def field_desc(name, bits, pos=0, signed=False):
    if bits is FD_WORD:
        layout = 0 | (INT16 if signed else UINT16)
        return FieldDesc(name, layout, None)
    
    if bits is FD_BYTE:
        layout = pos | (INT8 if signed else UINT8)
        return FieldDesc(name, layout, None)

    layout = 0 | BFUINT16 | pos << BF_POS | bits << BF_LEN
    return FieldDesc(name, layout, bits if signed else None)


class StructProto:
    # data needed to create a Struct
    # can be instantiated once and reused between Struct instances
    def __init__(self, fields):
        self.layout = {}
        self.signed = {}
        for fld in fields:
            self.layout[fld.name] = fld.layout
            if fld.signed_bits is not None:
                self.signed[fld.name] = fld.signed_bits


class Struct:
    def __init__(self, buf, proto):
        self._signed = proto.signed
        self._struct = uc_struct(addressof(buf), proto.layout, BIG_ENDIAN)

    def __getitem__(self, name):
        value = getattr(self._struct, name)
        signed = self._signed.get(name)
        if signed is not None:
            return twos_complement(signed, value)
        return value

    def __setitem__(self, name, value):
        signed = self._signed.get(name)
        if signed is not None:
            value = twos_complement(signed, value)
        setattr(self._struct, name, value)
