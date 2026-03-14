from . import arrayable_class
import struct as _struct
from typing import get_type_hints, Any, Union, Optional, TextIO
import ctypes
from ctypes import wintypes
import decimal
import math
import sys
import re

def _generate_format(*args):
    """
    识别类型，生成 struct 格式字符串
    支持：int, float, bool, ctypes, wintypes
    注意：Int128/Float128 需要特殊处理，不在此生成
    """
    parts = []
    for arg in args:
        # 基础类型
        if isinstance(arg, bool):
            parts.append('?')
        elif isinstance(arg, int):
            # 默认 int64
            parts.append('q')
        elif isinstance(arg, float):
            parts.append('d')
        
        # ctypes 类型
        elif isinstance(arg, ctypes.c_bool):
            parts.append('?')
        elif isinstance(arg, ctypes.c_int8):
            parts.append('b')
        elif isinstance(arg, ctypes.c_uint8):
            parts.append('B')
        elif isinstance(arg, ctypes.c_int16):
            parts.append('h')
        elif isinstance(arg, ctypes.c_uint16):
            parts.append('H')
        elif isinstance(arg, ctypes.c_int32):
            parts.append('i')
        elif isinstance(arg, ctypes.c_uint32):
            parts.append('I')
        elif isinstance(arg, ctypes.c_int64):
            parts.append('q')
        elif isinstance(arg, ctypes.c_uint64):
            parts.append('Q')
        elif isinstance(arg, ctypes.c_float):
            parts.append('f')
        elif isinstance(arg, ctypes.c_double):
            parts.append('d')
        elif isinstance(arg, ctypes.c_char):
            parts.append('c')
        elif isinstance(arg, ctypes.c_wchar):
            raise ValueError("wchar not supported in struct, use bytes")
        elif isinstance(arg, ctypes.c_void_p):
            parts.append('P')
        
        # wintypes（继承自 ctypes，上面已覆盖大部分）
        # 特殊 wintypes
        elif isinstance(arg, wintypes.BOOL):
            parts.append('?')
        elif isinstance(arg, wintypes.BYTE):
            parts.append('B')
        elif isinstance(arg, wintypes.WORD):
            parts.append('H')
        elif isinstance(arg, wintypes.DWORD):
            parts.append('I')
        elif isinstance(arg, wintypes.INT):
            parts.append('i')
        elif isinstance(arg, wintypes.UINT):
            parts.append('I')
        elif isinstance(arg, wintypes.LONG):
            parts.append('l')
        elif isinstance(arg, wintypes.ULONG):
            parts.append('L')
        elif isinstance(arg, wintypes.HANDLE):
            parts.append('P')  # 指针大小
        
        else:
            parts.append('')
    
    return ''.join(parts)

def is_packable(fmt: str, *values) -> bool:
    """检测是否能用 struct.pack 成功打包"""
    try:
        packed = _struct.pack(fmt, *values)
        return True, packed
    except (_struct.error, OverflowError, TypeError):
        return False, None


decimal.getcontext().prec = 50

def printf(text, *formatter):
    print(str(text) % formatter)

@arrayable_class.arrayable
class char(object):
    _size = 1
    def __init__(self, value):
        if isinstance(value, int):
            self.value = value
        elif isinstance(value, str):
            self.value = ord(value)
    def __str__(self):
        return self.value
    def __repr__(self):
        return f"{self.__class__}({self.value})"
    def __eq__(self,o):
        return self.value == o.value
    def __lt__(self,o):
        return self.value < o.value
    def __gt__(self,o):
        return self.value > o.value
    def __le__(self,o):
        return self.value <= o.value
    def __ge__(self,o):
        return self.value >= o.value
    def __int__(self):
        return self.value
    # 可选：支持 ord(c) 直接返回 int
    def __index__(self):
        return self.__int__()
    def __setattr__(self, key, value):
        if hasattr(self, 'value'):
            raise TypeError("'char' object does not support item assignment")
        super().__setattr__(key, value)
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>b', self.value)
        elif byteorder == "<":
            return _struct.pack('<b', self.value)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>b', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<b', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls(_low)

class Int128(object):
    _size = 16
    def __init__(self, value: int):
        self._high = (value >> 64) & 0xFFFFFFFFFFFFFFFF
        if self._high > 0x7FFFFFFFFFFFFFFF:
            self._high -= 0x10000000000000000
        self._low = value & 0xFFFFFFFFFFFFFFFF
    def to_int(self):
        if self._high < 0:
            _high = self._high + 0x10000000000000000
        else:
            _high = self._high
        v = (_high << 64) | (self._low)
        if v > 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
            v -= 0x100000000000000000000000000000000
        return v
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>qQ', self._high, self._low)
        elif byteorder == "<":
            return _struct.pack('<Qq', self._low, self._high)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_high_low(cls, high, low):
        obj = cls(0)
        obj._high = high
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _high, _low = _struct.unpack('>qQ', packed[:cls._size])
        elif byteorder == "<":
            _low, _high = _struct.unpack('<qQ', packed[:cls._size])
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_high_low(_high, _low)

class UInt128(object):
    _size = 16
    def __init__(self, value: int):
        self._high = (value >> 64) & 0xFFFFFFFFFFFFFFFF
        self._low = value & 0xFFFFFFFFFFFFFFFF
    def to_int(self):
        return (self._high << 64) | (self._low)
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>QQ', self._high, self._low)
        elif byteorder == "<":
            return _struct.pack('<QQ', self._low, self._high)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_high_low(cls, high, low):
        obj = cls(0)
        obj._high = high
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _high, _low = _struct.unpack('>QQ', packed[:cls._size])
        elif byteorder == "<":
            _low, _high = _struct.unpack('<QQ', packed[:cls._size])
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_high_low(_high, _low)

class Int64(object):
    _size = 8
    def __init__(self, value: int):
        self._low = value & 0xFFFFFFFFFFFFFFFF
        if self._low > 0x7FFFFFFFFFFFFFFF:
            self._low -= 0x10000000000000000
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>q', self._low)
        elif byteorder == "<":
            return _struct.pack('<q', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>q', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<q', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class UInt64(object):
    _size = 8
    def __init__(self, value: int):
        self._low = value & 0xFFFFFFFFFFFFFFFF
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>Q', self._low)
        elif byteorder == "<":
            return _struct.pack('<Q', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>Q', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<Q', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class Int32(object):
    _size = 4
    def __init__(self, value: int):
        self._low = value & 0xFFFFFFFF
        if self._low > 0x7FFFFFFF:
            self._low -= 0x100000000
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>i', self._low)
        elif byteorder == "<":
            return _struct.pack('<i', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>i', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<i', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class UInt32(object):
    _size = 4
    def __init__(self, value: int):
        self._low = value & 0xFFFFFFFF
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>I', self._low)
        elif byteorder == "<":
            return _struct.pack('<I', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>I', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<I', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class Int16(object):
    _size = 2
    def __init__(self, value: int):
        self._low = value & 0xFFFF
        if self._low > 0x7FFF:
            self._low -= 0x10000
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>h', self._low)
        elif byteorder == "<":
            return _struct.pack('<h', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>h', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<h', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class UInt16(object):
    _size = 2
    def __init__(self, value: int):
        self._low = value & 0xFFFF
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>H', self._low)
        elif byteorder == "<":
            return _struct.pack('<H', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>H', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<H', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
Int8 = char
class UInt8(object):
    _size = 1
    def __init__(self, value: int):
        self._low = value & 0xFF
    def to_int(self):
        return self._low
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('>B', self._low)
        elif byteorder == "<":
            return _struct.pack('<B', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>B', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<B', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)
class UInt1(object):
    _size = 1
    def __init__(self, value: int):
        self._low = value & 0x1
    def to_int(self):
        return self._low
    def to_bool(self):
        return bool(self._low)
    def pack(self, byteorder="<"):
        if byteorder == ">":
            return _struct.pack('?', self._low)
        elif byteorder == "<":
            return _struct.pack('?', self._low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")
    @classmethod
    def from_low(cls, low):
        obj = cls(0)
        obj._low = low
        return obj
    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            _low = _struct.unpack('>?', packed[:cls._size])[0]
        elif byteorder == "<":
            _low = _struct.unpack('<?', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        return cls.from_low(_low)


class Float128(object):
    _size = 16
    def __init__(self, value: float):
        int64_v = int.from_bytes(_struct.pack('>d', value), byteorder="big")
        sign = (int64_v >> 63) & 1
        exp64 = (int64_v >> 52) & 0x7FF
        man64 = int64_v & 0xFFFFFFFFFFFFF
        self._sign = sign
        if exp64 == 0:  # subnormal 或 0
            self._exp = 0
            self._man = man64 << (112 - 52)  # 左填0
        elif exp64 == 0x7FF:  # inf/nan
            self._exp = 0x7FFF
            self._man = man64 << (112 - 52) if man64 else 0
        else:
            self._exp = exp64 - 1023 + 16383  # 转偏移
            self._man = (man64 | (1 << 52)) << (112 - 52)  # 含隐含1，扩展
    @staticmethod
    def parse_exp_man(exp64, man64):
        if exp64 == 0:  # subnormal 或 0
            exp = 0
            man = man64 << (112 - 52)  # 左填0
        elif exp64 == 0x7FF:  # inf/nan
            exp = 0x7FFF
            man = man64 << (112 - 52) if man64 else 0
        else:
            exp = exp64 - 1023 + 16383  # 转偏移
            man = (man64 | (1 << 52)) << (112 - 52)  # 含隐含1，扩展
        return exp, man
        
    def to_float(self, byteorder="<"):
        # 先转回实际值，再让 Python 处理截断
        # 或检查范围，溢出时返回 inf
        if self._exp > 0x7FF + 1023:  # 太大
            return float('inf') if self._sign == 0 else float('-inf')
        if self._exp < 0:  # 太小
            return 0.0 * (-1 if self._sign else 1)
        
        # 正常范围，指数转偏移，尾数截断
        exp64 = self._exp - 16383 + 1023  # 128偏移 → 64偏移
        man64 = self._man >> (112 - 52)   # 高52位
        
        int64 = (self._sign << 63) | ((exp64 & 0x7FF) << 52) | (man64 & 0xFFFFFFFFFFFFF)
        return float.from_bytes(_struct.pack(f'{byteorder}Q', int64))
    def to_int128_v(self):
        return (self._sign << 127) | (self._exp << 112) | self._man
    def pack(self, byteorder="<"):
        # 16字节 = 128位
        # sign(1) | exp(15) | man(112)
        high = (self._sign << 63) | (self._exp << 48) | (self._man >> 64)
        low = self._man & 0xFFFFFFFFFFFFFFFF
        if byteorder == ">":
            return _struct.pack('>QQ', high, low)
        elif byteorder == "<":
            return _struct.pack('<QQ', low, high)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")

    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            high, low = _struct.unpack('>QQ', packed[:cls._size])
        elif byteorder == "<":
            low, high = _struct.unpack('<QQ', packed[:cls._size])
        else:
            raise ValueError("byteorder is not < or >")
        _sign = (high >> 63) & 1
        _exp = (high >> 48) & 0x7FFF
        _man = ((high & 0xFFFFFFFFFFFF) << 64) | low
        return cls.from_sign_exp_man(_sign, _exp, _man)
    @classmethod
    def from_sign_exp_man(cls, sign, exp, man):
        obj = cls(0.0)
        obj._sign = sign
        obj._exp = exp
        obj._man = man
        return obj
    @classmethod
    def from_string(cls, s: str):
        d = decimal.Decimal(s)
        
        # 特殊值
        if d.is_nan():
            return cls.from_sign_exp_man(0, 0x7FFF, 0x8000000000000000000000000000)
        if d.is_infinite():
            return cls.from_sign_exp_man(1 if d < 0 else 0, 0x7FFF, 0)
        
        # 零
        if d == 0:
            sign = 1 if str(d).startswith('-') else 0
            return cls.from_sign_exp_man(sign, 0, 0)
        
        # 符号
        sign = 1 if d < 0 else 0
        d = abs(d)
        
        # 科学计数法：coefficient × 10^exp10
        digits = d.as_tuple().digits
        exp10 = d.as_tuple().exponent
        
        # 系数作为整数
        coeff = int(''.join(map(str, digits)))
        # 调整：实际值 = coeff × 10^(exp10 - len(digits) + 1)
        real_exp10 = exp10 - len(digits) + 1
        
        # 目标：找到 exp2 使得 coeff × 10^real_exp10 = man × 2^exp2
        # 且 2^112 ≤ man < 2^113（正常数）
        
        # 估算 exp2
        # log2(d) = log2(coeff) + real_exp10 × log2(10)
        log2_10 = math.log2(10)
        log2_coeff = coeff.bit_length() - 1 if coeff > 0 else 0
        exp2_est = int(log2_coeff + real_exp10 * log2_10)
        
        # 精确计算：man = round(d × 2^(112 - exp2))
        target_shift = 112 - exp2_est
        man_dec = d * (decimal.Decimal(2) ** target_shift)
        man = int(man_dec.to_integral_value(rounding=decimal.ROUND_HALF_EVEN))
        
        # 标准化
        if man >= (1 << 113):
            man >>= 1
            exp2_est += 1
        elif man < (1 << 112):
            # 需要左移，但可能变成 subnormal
            shift_needed = (1 << 112).bit_length() - man.bit_length()
            if exp2_est - shift_needed > -16382:  # 还能正常化
                man <<= shift_needed
                exp2_est -= shift_needed
            else:
                # subnormal
                exp2_est = -16382
                man >>= (-16382 - (exp2_est - shift_needed))
        
        # 检查范围
        if exp2_est > 16383:  # overflow
            return cls.from_sign_exp_man(sign, 0x7FFF, 0)
        if exp2_est <= -16382:  # subnormal or underflow
            if exp2_est < -16382 - 112:  # underflow to zero
                return cls.from_sign_exp_man(sign, 0, 0)
            # subnormal：exp=0，man右移
            shift = -16382 - exp2_est + 1
            man >>= shift
            exp = 0
        else:
            exp = exp2_est + 16383
        
        # 去掉隐含位
        if exp > 0:  # 正常数
            man &= (1 << 112) - 1
        
        return cls.from_sign_exp_man(sign, exp, man)
    def to_decimal(self):
        """返回 Decimal，保留 128 位精度"""
        if self._exp == 0x7FFF:
            return decimal.Decimal('NaN') if self._man else decimal.Decimal('Infinity') * (-1 if self._sign else 1)
        if self._exp == 0 and self._man == 0:
            return decimal.Decimal(0) * (-1 if self._sign else 1)
        
        # 计算实际值
        exp = self._exp - 16383 if self._exp > 0 else -16382
        man = self._man | (1 << 112) if self._exp > 0 else self._man  # 正常数加隐含位
        
        # man × 2^exp
        d = decimal.Decimal(man) * (decimal.Decimal(2) ** exp)
        return -d if self._sign else d

class Double(object):
    _size = 8
    def __init__(self, value: float):
        int64_v = int.from_bytes(_struct.pack('>d', value), byteorder="big")
        sign = (int64_v >> 63) & 1
        exp64 = (int64_v >> 52) & 0x7FF
        man64 = int64_v & 0xFFFFFFFFFFFFF
        self._sign = sign
        self._exp = exp64
        self._man = man64
        
    def to_float(self, byteorder="<"):
        int64 = self.to_int()
        return float.from_bytes(_struct.pack(f'{byteorder}Q', int64))
    def to_int(self):
        return (self._sign << 63) | (self._exp << 52) | self._man
    def pack(self, byteorder="<"):
        # 16字节 = 128位
        # sign(1) | exp(15) | man(112)
        low = self.to_int()
        if byteorder == ">":
            return _struct.pack('>Q', low)
        elif byteorder == "<":
            return _struct.pack('<Q', low)  # 小端：低64位在前
        else:
            raise ValueError("byteorder is not < or >")

    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            low = _struct.unpack('>Q', packed[:cls._size])[0]
        elif byteorder == "<":
            low = _struct.unpack('<Q', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        _sign = (low >> 63) & 1
        _exp = (low >> 52) & 0x7FF
        _man = low & 0xFFFFFFFFFFFFF
        return cls.from_sign_exp_man(_sign, _exp, _man)
    @classmethod
    def from_sign_exp_man(cls, sign, exp, man):
        obj = cls(0.0)
        obj._sign = sign
        obj._exp = exp
        obj._man = man
        return obj
    @classmethod
    def from_string(cls, s: str):
        d = decimal.Decimal(s)
        
        # 特殊值
        if d.is_nan():
            return cls.from_sign_exp_man(0, 0x7FF, 0x8000000000000000)
        if d.is_infinite():
            return cls.from_sign_exp_man(1 if d < 0 else 0, 0x7FF, 0)
        
        # 零
        if d == 0:
            sign = 1 if str(d).startswith('-') else 0
            return cls.from_sign_exp_man(sign, 0, 0)
        
        # 符号
        sign = 1 if d < 0 else 0
        d = abs(d)
        
        # 科学计数法
        digits = d.as_tuple().digits
        exp10 = d.as_tuple().exponent
        
        coeff = int(''.join(map(str, digits)))
        real_exp10 = exp10 - len(digits) + 1
        
        # 目标：2^52 ≤ man < 2^53
        log2_10 = math.log2(10)
        log2_coeff = coeff.bit_length() - 1 if coeff > 0 else 0
        exp2_est = int(log2_coeff + real_exp10 * log2_10)
        
        # 精确计算
        target_shift = 52 - exp2_est
        man_dec = d * (decimal.Decimal(2) ** target_shift)
        man = int(man_dec.to_integral_value(rounding=decimal.ROUND_HALF_EVEN))
        
        # 标准化
        if man >= (1 << 53):
            man >>= 1
            exp2_est += 1
        elif man < (1 << 52):
            shift_needed = (1 << 52).bit_length() - man.bit_length()
            if exp2_est - shift_needed > -1022:  # 还能正常化
                man <<= shift_needed
                exp2_est -= shift_needed
            else:
                # subnormal
                exp2_est = -1022
                man >>= (-1022 - (exp2_est - shift_needed))
        
        # 检查范围
        if exp2_est > 1023:  # overflow
            return cls.from_sign_exp_man(sign, 0x7FF, 0)
        if exp2_est <= -1022:  # subnormal or underflow
            if exp2_est < -1022 - 52:  # underflow to zero
                return cls.from_sign_exp_man(sign, 0, 0)
            # subnormal
            shift = -1022 - exp2_est + 1
            man >>= shift
            exp = 0
        else:
            exp = exp2_est + 1023
        
        # 去掉隐含位
        if exp > 0:
            man &= (1 << 52) - 1
        
        return cls.from_sign_exp_man(sign, exp, man)
    def to_decimal(self):
        """返回 Decimal，保留 64 位精度"""
        if self._exp == 0x7FF:
            return decimal.Decimal('NaN') if self._man else decimal.Decimal('Infinity') * (-1 if self._sign else 1)
        if self._exp == 0 and self._man == 0:
            return decimal.Decimal(0) * (-1 if self._sign else 1)
        
        # 计算实际值
        exp = self._exp - 1023 if self._exp > 0 else -1022
        man = self._man | (1 << 52) if self._exp > 0 else self._man  # 正常数加隐含位
        
        # man × 2^exp
        d = decimal.Decimal(man) * (decimal.Decimal(2) ** exp)
        return -d if self._sign else d
class Float(object):
    _size = 4
    
    def __init__(self, value: float):
        int32_v = int.from_bytes(_struct.pack('>f', value), byteorder="big")
        self._sign = (int32_v >> 31) & 1
        self._exp = (int32_v >> 23) & 0xFF
        self._man = int32_v & 0x7FFFFF
        
    def to_float(self, byteorder="<"):
        int32 = self.to_int()
        return float.from_bytes(_struct.pack(f'{byteorder}I', int32))
    
    def to_int(self):
        return (self._sign << 31) | (self._exp << 23) | self._man
    
    def pack(self, byteorder="<"):
        low = self.to_int()
        if byteorder == ">":
            return _struct.pack('>I', low)
        elif byteorder == "<":
            return _struct.pack('<I', low)
        else:
            raise ValueError("byteorder is not < or >")

    @classmethod
    def unpack(cls, packed, byteorder="<"):
        if byteorder == ">":
            low = _struct.unpack('>I', packed[:cls._size])[0]
        elif byteorder == "<":
            low = _struct.unpack('<I', packed[:cls._size])[0]
        else:
            raise ValueError("byteorder is not < or >")
        _sign = (low >> 31) & 1
        _exp = (low >> 23) & 0xFF
        _man = low & 0x7FFFFF
        return cls.from_sign_exp_man(_sign, _exp, _man)
    
    @classmethod
    def from_sign_exp_man(cls, sign, exp, man):
        obj = cls(0.0)
        obj._sign = sign
        obj._exp = exp
        obj._man = man
        return obj
    
    @classmethod
    def from_string(cls, s: str):
        d = decimal.Decimal(s)
        
        if d.is_nan():
            return cls.from_sign_exp_man(0, 0xFF, 0x400000)
        if d.is_infinite():
            return cls.from_sign_exp_man(1 if d < 0 else 0, 0xFF, 0)
        
        if d == 0:
            sign = 1 if str(d).startswith('-') else 0
            return cls.from_sign_exp_man(sign, 0, 0)
        
        sign = 1 if d < 0 else 1
        d = abs(d)
        
        digits = d.as_tuple().digits
        exp10 = d.as_tuple().exponent
        
        coeff = int(''.join(map(str, digits)))
        real_exp10 = exp10 - len(digits) + 1
        
        log2_10 = math.log2(10)
        log2_coeff = coeff.bit_length() - 1 if coeff > 0 else 0
        exp2_est = int(log2_coeff + real_exp10 * log2_10)
        
        target_shift = 23 - exp2_est
        man_dec = d * (decimal.Decimal(2) ** target_shift)
        man = int(man_dec.to_integral_value(rounding=decimal.ROUND_HALF_EVEN))
        
        if man >= (1 << 24):
            man >>= 1
            exp2_est += 1
        elif man < (1 << 23):
            shift_needed = (1 << 23).bit_length() - man.bit_length()
            if exp2_est - shift_needed > -126:
                man <<= shift_needed
                exp2_est -= shift_needed
            else:
                exp2_est = -126
                man >>= (-126 - (exp2_est - shift_needed))
        
        if exp2_est > 127:
            return cls.from_sign_exp_man(sign, 0xFF, 0)
        if exp2_est <= -126:
            if exp2_est < -126 - 23:
                return cls.from_sign_exp_man(sign, 0, 0)
            shift = -126 - exp2_est + 1
            man >>= shift
            exp = 0
        else:
            exp = exp2_est + 127
        
        if exp > 0:
            man &= (1 << 23) - 1
        
        return cls.from_sign_exp_man(sign, exp, man)
    
    def to_decimal(self):
        if self._exp == 0xFF:
            return decimal.Decimal('NaN') if self._man else decimal.Decimal('Infinity') * (-1 if self._sign else 1)
        if self._exp == 0 and self._man == 0:
            return decimal.Decimal(0) * (-1 if self._sign else 1)
        
        exp = self._exp - 127 if self._exp > 0 else -126
        man = self._man | (1 << 23) if self._exp > 0 else self._man
        
        d = decimal.Decimal(man) * (decimal.Decimal(2) ** exp)
        return -d if self._sign else d


class struct(object):
    def __init__(self, **kwargs):
        for key in get_type_hints(self.__class__):
            value = kwargs.get(key, getattr(self.__class__, key, None))
            setattr(self, key, value)
    
    def pack(self, byteorder='<'):
        pack_buffer = bytearray()
        for k, v in vars(self).items():  # 修正：vars(self).items()
            packable, packed = is_packable(_generate_format(v), v)
            if hasattr(v, 'pack'):
                # 检查 pack 方法是否接受 byteorder
                import inspect
                sig = inspect.signature(v.pack)
                if 'byteorder' in sig.parameters:
                    pack_buffer.extend(v.pack(byteorder=byteorder))
                else:
                    pack_buffer.extend(v.pack())
            elif packable:
                pack_buffer.extend(packed)
            else:
                raise TypeError(f'{v.__class__} object is not packable')
        return bytes(pack_buffer)
    
    @classmethod
    def unpack(cls, data: bytes, byteorder='<'):
        """从字节反序列化"""
        # 获取字段类型提示
        hints = get_type_hints(cls)
        
        # 计算每个字段的大小
        offset = 0
        kwargs = {}
        
        for name, typ in hints.items():
            # 获取类型对应的 unpack 方法
            value, size = cls._unpack_field(data, offset, typ, byteorder)
            kwargs[name] = value
            offset += size
        
        return cls(**kwargs)
    
    @classmethod
    def _unpack_field(cls, data: bytes, offset: int, typ, byteorder: str):
        """解包单个字段，返回 (值, 字节大小)"""
        # 基础类型
        if typ is int:
            fmt = f'{byteorder}q'
            size = 8
            value = _struct.unpack(fmt, data[offset:offset+size])[0]
            return value, size
        
        if typ is float:
            fmt = f'{byteorder}d'
            size = 8
            value = _struct.unpack(fmt, data[offset:offset+size])[0]
            return value, size
        
        if typ is bool:
            fmt = '?'
            size = 1
            value = _struct.unpack(fmt, data[offset:offset+size])[0]
            return value, size
        
        # 自定义类型（假设都有 unpack 类方法）
        if hasattr(typ, 'unpack'):
            # 获取 pack 大小（假设有 _size 或从 pack 推断）
            if hasattr(typ, '_size'):
                size = typ._size
            else:
                # 通过空 pack 推断大小
                size = len(typ(0).pack(byteorder)) if hasattr(typ, '__init__') else 16
            
            value = typ.unpack(data[offset:offset+size], byteorder)
            return value, size
        
        raise TypeError(f"unsupported type: {typ}")
                

class Variable:
    """
    变量包装器类，利用 Python 列表的引用特性模拟 C++ 引用传参
    """
    def __init__(self, value):
        self._value = [value]
    
    @property
    def value(self):
        return self._value[0]
    
    @value.setter
    def value(self, new_value):
        self._value[0] = new_value
    
    def __getitem__(self, index):
        return self._value[index]
    
    def __setitem__(self, index, value):
        self._value[index] = value
    
    def __str__(self):
        return str(self._value[0])
    
    def __repr__(self):
        return f"Variable({self._value[0]!r})"
    
    def get(self):
        return self._value[0]


class IStream:
    """输入流类，模拟 C++ 的 std::istream"""
    def __init__(self, io_obj: Optional[TextIO] = None):
        self.io = io_obj or sys.stdin
        self._buffer = ""
        self._failbit = False
        self._eofbit = False
        self._goodbit = True
    
    def _get_token(self):
        while not self._buffer.strip():
            new_data = self.io.readline()
            if not new_data:
                self._eofbit = True
                return None
            self._buffer += new_data
        
        self._buffer = self._buffer.lstrip()
        match_obj = re.search(r'\s', self._buffer)
        if match_obj:
            token = self._buffer[:match_obj.start()]
            self._buffer = self._buffer[match_obj.end():]
        else:
            token = self._buffer
            self._buffer = ""
        return token
    
    def __rshift__(self, dest):
        try:
            if isinstance(dest, Variable):
                token = self._get_token()
                if token is None:
                    self._failbit = True
                else:
                    target_type = type(dest._value[0]) if dest._value[0] is not None else str
                    try:
                        if target_type == str:
                            dest._value[0] = token
                        else:
                            dest._value[0] = target_type(token)
                    except ValueError:
                        self._failbit = True
                return self
            
            if isinstance(dest, list):
                token = self._get_token()
                if token is None:
                    self._failbit = True
                elif len(dest) > 0:
                    target_type = type(dest[0]) if dest[0] is not None else str
                    try:
                        if target_type == str:
                            dest[0] = token
                        else:
                            dest[0] = target_type(token)
                    except ValueError:
                        self._failbit = True
                return self
            
            data = self._buffer + self.io.read()
            self._buffer = ""
            if not data:
                self._eofbit = True
            
            if isinstance(dest, OStream):
                dest.io.write(data)
            elif isinstance(dest, IStream):
                if hasattr(dest.io, 'write'):
                    dest.io.write(data)
            elif isinstance(dest, str):
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(data)
            elif hasattr(dest, 'write'):
                dest.write(data)
            else:
                raise TypeError(f"Unsupported destination type: {type(dest)}")
            return self
            
        except Exception:
            self._failbit = True
            self._goodbit = False
            return self
    
    def good(self):
        return self._goodbit and not (self._failbit or self._eofbit)
    
    def fail(self):
        return self._failbit
    
    def eof(self):
        return self._eofbit
    
    def clear(self):
        self._failbit = False
        self._eofbit = False
        self._goodbit = True
        self._buffer = ""
    
    def __bool__(self):
        """支持 if cin: 用法"""
        return self.good()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.io and self.io not in (sys.stdin, sys.stdout, sys.stderr):
            if hasattr(self.io, 'close'):
                self.io.close()


class OStream:
    """输出流类，模拟 C++ 的 std::ostream"""
    def __init__(self, io_obj=None):
        self.io = io_obj or sys.stdout
        self._failbit = False
        self._goodbit = True
    
    def __lshift__(self, src):
        try:
            if hasattr(src, '__ostream__'):
                return src.__ostream__(self)
            
            data = ""
            if isinstance(src, Variable):
                data = str(src._value[0])
            elif isinstance(src, IStream):
                data = src.io.read()
            elif isinstance(src, OStream):
                if hasattr(src.io, 'read'):
                    data = src.io.read()
                else:
                    data = str(src.io)
            elif isinstance(src, str):
                try:
                    with open(src, 'r', encoding='utf-8') as f:
                        data = f.read()
                except (IOError, OSError):
                    data = src
            elif hasattr(src, 'read'):
                data = src.read()
            elif callable(src):
                src(self)
                return self
            else:
                data = str(src)
            
            if data:
                self.io.write(data)
            return self
            
        except Exception:
            self._failbit = True
            self._goodbit = False
            return self    
    def write(self, data):
        self.io.write(str(data))
        return self
    
    def flush(self):
        if hasattr(self.io, 'flush'):
            self.io.flush()
        return self
    
    def good(self):
        return self._goodbit and not self._failbit
    
    def fail(self):
        return self._failbit
    
    def clear(self):
        self._failbit = False
        self._goodbit = True
    
    def __bool__(self):
        """支持 if cout: 用法"""
        return self.good()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        if self.io and self.io not in (sys.stdin, sys.stdout, sys.stderr):
            if hasattr(self.io, 'close'):
                self.io.close()


class _Endl:
    def __call__(self, stream):
        stream.io.write('\n')
        if hasattr(stream.io, 'flush'):
            stream.io.flush()
        return stream

class _Flush:
    def __call__(self, stream):
        if hasattr(stream.io, 'flush'):
            stream.io.flush()
        return stream

class _Ws:
    def __call__(self, stream):
        return stream

endl = _Endl()
flush = _Flush()
ws = _Ws()

cin = IStream(sys.stdin)
cout = OStream(sys.stdout)
cerr = OStream(sys.stderr)
clog = OStream(sys.stderr)

class _Namespace:
    pass

std = _Namespace()
std.cin = cin
std.cout = cout
std.cerr = cerr
std.clog = clog
std.endl = endl
std.flush = flush
std.ws = ws
std.IStream = IStream
std.OStream = OStream
std.Variable = Variable
std.Int128 = Int128
std.UInt128 = UInt128
std.Int64 = Int64
std.UInt64 = UInt64
std.Int32 = Int32
std.UInt32 = UInt32
std.Int16 = Int16
std.UInt16 = UInt16
std.Int8 = Int8
std.char = char
std.UInt8 = UInt8
std.UInt1 = UInt1
std.struct = struct
std._Namespace = _Namespace