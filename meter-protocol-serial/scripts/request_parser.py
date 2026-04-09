# request_parser.py
# 请求解析模块
# 将半结构化的 key=value 输入解析为结构化请求对象

import re
import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from profiles import parse_parity, parse_stop_bits


@dataclass
class ParsedRequest:
    """解析后的请求对象"""
    # 通用字段
    proto: str = ""  # 645 or 698
    op: str = ""  # read, write, set
    port: Optional[str] = None
    timeout_ms: Optional[int] = None
    baud: Optional[int] = None
    data_bits: Optional[int] = None
    parity: Optional[str] = None
    stop_bits: Optional[int] = None

    # 645专用字段
    di: Optional[str] = None  # 8位十六进制
    addr: Optional[str] = None  # 645地址
    value: Optional[str] = None  # 值(带类型前缀)
    fe_count: Optional[int] = None
    raw_prefix: Optional[str] = None  # hex:...
    raw_suffix: Optional[str] = None  # hex:...

    # 698专用字段
    oad: Optional[str] = None  # 8位十六进制
    server_addr: Optional[str] = None
    client_addr: Optional[str] = None
    ca: Optional[str] = None  # client_addr的缩写

    # 断言相关
    expect: Optional[str] = None
    decode_hint: Optional[str] = None
    note: Optional[str] = None

    # 原始参数字典(保留未识别的参数)
    raw_params: Dict[str, str] = field(default_factory=dict)


def parse_hex_value(value: str, expected_bytes: Optional[int] = None) -> bytes:
    """
    解析 hex: 前缀的值为字节序列
    hex:010203 -> b'\x01\x02\x03'
    """
    if not value.startswith("hex:"):
        raise ValueError(f"值必须以 hex: 开头，实际是: {value}")

    hex_str = value[4:].strip()
    # 移除可能存在的空格
    hex_str = hex_str.replace(" ", "").replace("\t", "")

    if len(hex_str) % 2 != 0:
        raise ValueError(f"十六进制字符串长度必须是偶数: {hex_str}")

    try:
        result = bytes.fromhex(hex_str)
    except ValueError as e:
        raise ValueError(f"无效的十六进制字符串: {hex_str}, 错误: {e}")

    if expected_bytes is not None and len(result) != expected_bytes:
        raise ValueError(f"期望{expected_bytes}字节，实际是{len(result)}字节")

    return result


def parse_typed_value(value: str) -> tuple:
    """
    解析带类型前缀的值
    返回: (type_name, decoded_value)
    支持的类型: hex:, ascii:, bool:, int8:, int16:, int32:, uint8:, uint16:, uint32:, enum:, octet:, string:
    """
    if not value or ":" not in value:
        raise ValueError(f"值必须包含类型前缀，如 hex:0102, bool:true 等，实际是: {value}")

    colon_pos = value.find(":")
    type_name = value[:colon_pos].lower()
    type_value = value[colon_pos + 1:]

    return type_name, type_value


def validate_di(di_str: str) -> str:
    """验证DI格式为8位十六进制"""
    di = di_str.strip().replace(" ", "")
    if len(di) != 8:
        raise ValueError(f"DI必须是8位十六进制，实际是{len(di)}位: {di}")
    try:
        int(di, 16)
    except ValueError:
        raise ValueError(f"DI包含无效的十六进制字符: {di}")
    return di.lower()


def validate_oad(oad_str: str) -> str:
    """验证OAD格式为8位十六进制"""
    oad = oad_str.strip().replace(" ", "")
    if len(oad) != 8:
        raise ValueError(f"OAD必须是8位十六进制，实际是{len(oad)}位: {oad}")
    try:
        int(oad, 16)
    except ValueError:
        raise ValueError(f"OAD包含无效的十六进制字符: {oad}")
    return oad.lower()


def parse_request(args: list) -> ParsedRequest:
    """
    解析命令行参数列表为ParsedRequest对象
    参数格式: key=value 或 key:value
    """
    req = ParsedRequest()

    for arg in args:
        # 支持 key=value 或 key:value
        if "=" in arg:
            sep = "="
        elif ":" in arg:
            sep = ":"
        else:
            # 无分隔符的参数，尝试作为proto或port
            if arg.lower() in ("645", "698"):
                req.proto = arg.lower()
            elif arg.startswith("COM") or arg.startswith("/dev/"):
                req.port = arg
            continue

        parts = arg.split(sep, 1)
        if len(parts) != 2:
            continue

        key = parts[0].lower().strip()
        value = parts[1].strip()

        # 通用字段
        if key == "proto":
            req.proto = value.lower()
        elif key == "op":
            req.op = value.lower()
        elif key == "port":
            req.port = value
        elif key == "timeout_ms":
            try:
                req.timeout_ms = int(value)
            except ValueError:
                raise ValueError(f"timeout_ms必须是整数: {value}")
        elif key == "baud":
            try:
                req.baud = int(value)
            except ValueError:
                raise ValueError(f"baud必须是整数: {value}")
        elif key == "data_bits":
            try:
                req.data_bits = int(value)
            except ValueError:
                raise ValueError(f"data_bits必须是整数: {value}")
        elif key == "parity":
            req.parity = parse_parity(value)
        elif key == "stop_bits":
            req.stop_bits = parse_stop_bits(value)

        # 645专用字段
        elif key == "di":
            req.di = validate_di(value)
        elif key == "addr":
            req.addr = value
        elif key == "fe_count":
            try:
                req.fe_count = int(value)
            except ValueError:
                raise ValueError(f"fe_count必须是整数: {value}")
        elif key == "raw_prefix":
            req.raw_prefix = value
        elif key == "raw_suffix":
            req.raw_suffix = value

        # 698专用字段
        elif key == "oad":
            req.oad = validate_oad(value)
        elif key == "server_addr":
            req.server_addr = value
        elif key == "client_addr":
            req.client_addr = value
        elif key == "ca":
            req.ca = value

        # 值字段(645和698共用)
        elif key == "value":
            req.value = value

        # 断言和解码相关
        elif key == "expect":
            req.expect = value
        elif key == "decode_hint":
            req.decode_hint = value.lower()
        elif key == "note":
            req.note = value
        else:
            # 保留未识别的参数
            req.raw_params[key] = value

    return req


def validate_request(req: ParsedRequest) -> list:
    """
    验证请求对象的完整性
    返回错误信息列表，空列表表示验证通过
    """
    errors = []

    # 验证必需字段
    if not req.proto:
        errors.append("缺少必需参数: proto (645 或 698)")
    elif req.proto not in ("645", "698"):
        errors.append(f"不支持的协议: {req.proto} (必须是 645 或 698)")

    if not req.op:
        errors.append("缺少必需参数: op (read, write, set)")
    elif req.op not in ("read", "write", "set"):
        errors.append(f"不支持的操作: {req.op} (必须是 read, write, set)")

    # 645协议特有验证
    if req.proto == "645":
        # 645不支持 set 操作
        if req.op == "set":
            errors.append("645协议不支持 set 操作，请使用 write")
        # read/write 都需要 DI
        elif req.op in ("read", "write"):
            if not req.di:
                errors.append("645协议 read/write 操作需要指定 di 参数")
            # write 操作必须有 value
            if req.op == "write" and not req.value:
                errors.append("645协议 write 操作需要指定 value 参数")

    # 698协议特有验证
    if req.proto == "698":
        # 698不支持 write 操作
        if req.op == "write":
            errors.append("698协议不支持 write 操作，请使用 set")
        # read 需要 OAD
        elif req.op == "read":
            if not req.oad:
                errors.append("698协议 read 操作需要指定 oad 参数")
        # set 需要 OAD 和 value
        elif req.op == "set":
            if not req.oad:
                errors.append("698协议 set 操作需要指定 oad 参数")
            if not req.value:
                errors.append("698协议 set 操作需要指定 value 参数")

    return errors
