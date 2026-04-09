# value_codec.py
# 值编解码模块
# 处理各种类型的编码和解码

import struct
from typing import Union, Optional, Tuple


def encode_hex_value(value_str: str) -> bytes:
    """编码 hex: 前缀的值"""
    if not value_str.startswith("hex:"):
        raise ValueError(f"值必须以 hex: 开头: {value_str}")

    hex_str = value_str[4:].replace(" ", "").replace("\t", "")
    if len(hex_str) % 2 != 0:
        raise ValueError(f"十六进制字符串长度必须是偶数: {hex_str}")

    return bytes.fromhex(hex_str)


def encode_ascii_value(value_str: str) -> bytes:
    """编码 ascii: 前缀的值"""
    if not value_str.startswith("ascii:"):
        raise ValueError(f"值必须以 ascii: 开头: {value_str}")

    ascii_str = value_str[6:]
    return ascii_str.encode("ascii")


def encode_bool_value(value_str: str) -> bytes:
    """
    编码 bool: 前缀的值为 A-XDR Data 格式
    A-XDR BOOL: tag=0x01, 值=0x00/0x01
    """
    if not value_str.startswith("bool:"):
        raise ValueError(f"值必须以 bool: 开头: {value_str}")

    val = value_str[5:].lower().strip()
    if val in ("true", "1", "yes", "on"):
        return b'\x01\x01'  # tag=BOOL(0x01), value=1
    else:
        return b'\x01\x00'  # tag=BOOL(0x01), value=0


def encode_int_value(value_str: str) -> bytes:
    """
    编码整数类型值为 A-XDR Data 格式
    A-XDR INTEGER: tag=0x10, length, value
    A-XDR LONG: tag=0x05, 4字节值 (大端有符号)
    """
    for prefix, size, tag in [("int8:", 1, 0x10), ("int16:", 2, 0x10), ("int32:", 4, 0x05)]:
        if value_str.startswith(prefix):
            try:
                val = int(value_str[len(prefix):])
                if size == 4:
                    # DOUBLE-LONG (int32): tag=0x05, 4字节大端有符号
                    return bytes([tag]) + struct.pack(">i", val)
                else:
                    # INTEGER: tag=0x10, length, value
                    fmt = {1: "b", 2: ">h"}[size]
                    return bytes([tag, size]) + struct.pack(fmt, val)
            except (ValueError, struct.error) as e:
                raise ValueError(f"无法编码 {prefix} 值: {value_str}, 错误: {e}")
    raise ValueError(f"未知的整数类型: {value_str}")


def encode_uint_value(value_str: str) -> bytes:
    """
    编码无符号整数类型值为 A-XDR Data 格式
    A-XDR UNSIGNED: tag=0x12, length, value
    A-XDR UNSIGNED32: tag=0x06, 4字节值 (大端无符号)
    """
    for prefix, size, tag in [("uint8:", 1, 0x12), ("uint16:", 2, 0x12), ("uint32:", 4, 0x06)]:
        if value_str.startswith(prefix):
            try:
                val = int(value_str[len(prefix):])
                if size == 4:
                    # UNSIGNED32: tag=0x06, 4字节大端无符号
                    return bytes([tag]) + struct.pack(">I", val)
                else:
                    # UNSIGNED: tag=0x12, length, value
                    fmt = {1: "B", 2: ">H"}[size]
                    return bytes([tag, size]) + struct.pack(fmt, val)
            except (ValueError, struct.error) as e:
                raise ValueError(f"无法编码 {prefix} 值: {value_str}, 错误: {e}")
    raise ValueError(f"未知的无符号整数类型: {value_str}")


def encode_enum_value(value_str: str) -> bytes:
    """
    编码 enum: 前缀的值为 A-XDR Data 格式
    A-XDR ENUM: tag=0x16, value (1字节)
    """
    if not value_str.startswith("enum:"):
        raise ValueError(f"值必须以 enum: 开头: {value_str}")

    try:
        val = int(value_str[5:])
        # ENUM: tag=0x16, value (1字节)
        return bytes([0x16, val & 0xFF])
    except (ValueError, struct.error) as e:
        raise ValueError(f"无法编码 enum 值: {value_str}, 错误: {e}")


def encode_octet_value(value_str: str) -> bytes:
    """编码 octet: 前缀的值为八位串，格式: octet:11223344 或 octet:1122"""
    if not value_str.startswith("octet:"):
        raise ValueError(f"值必须以 octet: 开头: {value_str}")

    hex_str = value_str[6:].replace(" ", "").replace("\t", "")
    if len(hex_str) % 2 != 0:
        raise ValueError(f"octet 十六进制字符串长度必须是偶数: {hex_str}")

    data = bytes.fromhex(hex_str)
    # 698 A-XDR: octet-string 带长度前缀(1字节)
    return bytes([len(data)]) + data


def encode_string_value(value_str: str) -> bytes:
    """编码 string: 前缀的值为可见字符串，格式: string:abc"""
    if not value_str.startswith("string:"):
        raise ValueError(f"值必须以 string: 开头: {value_str}")

    str_data = value_str[7:]
    ascii_data = str_data.encode("ascii")
    # 698 A-XDR: visible-string 带长度前缀
    return bytes([len(ascii_data)]) + ascii_data


def encode_698_value(value_str: str) -> bytes:
    """
    编码698协议的value值
    支持: bool:, int8:, int16:, int32:, uint8:, uint16:, uint32:, enum:, octet:, string:, hex:
    """
    if not value_str:
        raise ValueError("value不能为空")

    type_prefix = value_str.split(":")[0].lower()

    if type_prefix == "bool":
        return encode_bool_value(value_str)
    elif type_prefix in ("int8", "int16", "int32"):
        return encode_int_value(value_str)
    elif type_prefix in ("uint8", "uint16", "uint32"):
        return encode_uint_value(value_str)
    elif type_prefix == "enum":
        return encode_enum_value(value_str)
    elif type_prefix == "octet":
        return encode_octet_value(value_str)
    elif type_prefix == "string":
        return encode_string_value(value_str)
    elif type_prefix == "hex":
        # hex: 表示用户直接提供完整编码后的Data字节
        return encode_hex_value(value_str)
    else:
        raise ValueError(f"698协议不支持的value类型: {type_prefix}")


def encode_645_value(value_str: str) -> bytes:
    """
    编码645协议的value值
    支持: hex:, ascii:
    645的数据区需要先 +0x33 处理
    """
    if not value_str:
        raise ValueError("value不能为空")

    type_prefix = value_str.split(":")[0].lower()

    if type_prefix == "hex":
        return encode_hex_value(value_str)
    elif type_prefix == "ascii":
        return encode_ascii_value(value_str)
    else:
        raise ValueError(f"645协议不支持的value类型: {type_prefix}，请使用 hex: 或 ascii:")


def decode_hex(data: bytes) -> str:
    """解码为十六进制字符串"""
    return data.hex().upper()


def decode_ascii(data: bytes) -> str:
    """解码为ASCII字符串"""
    try:
        return data.decode("ascii")
    except UnicodeDecodeError:
        # 如果包含非ASCII字符，返回hex表示
        return f"hex:{data.hex().upper()}"


def decode_uint16_le(data: bytes) -> int:
    """解码小端uint16"""
    if len(data) < 2:
        raise ValueError("需要至少2字节")
    return struct.unpack("<H", data[:2])[0]


def decode_uint32_le(data: bytes) -> int:
    """解码小端uint32"""
    if len(data) < 4:
        raise ValueError("需要至少4字节")
    return struct.unpack("<I", data[:4])[0]


def decode_uint16_be(data: bytes) -> int:
    """解码大端uint16"""
    if len(data) < 2:
        raise ValueError("需要至少2字节")
    return struct.unpack(">H", data[:2])[0]


def decode_uint32_be(data: bytes) -> int:
    """解码大端uint32"""
    if len(data) < 4:
        raise ValueError("需要至少4字节")
    return struct.unpack(">I", data[:4])[0]


def decode_bcd(data: bytes) -> str:
    """解码BCD码为字符串表示"""
    hex_str = data.hex()
    return hex_str


def apply_645_offset_33(data: bytes) -> bytes:
    """645协议: 数据区字节 +0x33 处理"""
    return bytes([(b + 0x33) & 0xFF for b in data])


def remove_645_offset_33(data: bytes) -> bytes:
    """645协议: 数据区字节 -0x33 处理"""
    return bytes([(b - 0x33) & 0xFF for b in data])


def decode_by_hint(data: bytes, hint: str) -> Union[str, int]:
    """根据decode_hint解码数据"""
    hint = hint.lower()

    if hint == "hex":
        return decode_hex(data)
    elif hint == "ascii":
        return decode_ascii(data)
    elif hint == "uint16_le":
        return decode_uint16_le(data)
    elif hint == "uint32_le":
        return decode_uint32_le(data)
    elif hint == "uint16_be":
        return decode_uint16_be(data)
    elif hint == "uint32_be":
        return decode_uint32_be(data)
    elif hint == "bcd":
        return decode_bcd(data)
    else:
        raise ValueError(f"未知的decode_hint: {hint}")
