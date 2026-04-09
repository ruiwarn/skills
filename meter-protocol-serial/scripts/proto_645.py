# proto_645.py
# DL/T645-2007 协议处理模块
# 负责645协议的组帧和解析

import struct
from dataclasses import dataclass, field
from typing import Optional, List
from value_codec import encode_645_value, apply_645_offset_33, remove_645_offset_33, decode_by_hint


@dataclass
class Frame645Request:
    """645请求帧结构"""
    addr: str  # 12位BCD地址
    ctrl: int  # 控制码
    data: bytes  # 数据区(未+0x33的原始数据)
    fe_count: int = 4  # 前导FE个数


@dataclass
class Frame645Response:
    """645响应帧解析结果"""
    raw_frame: bytes = b""  # 原始帧数据

    # 帧结构字段
    fe_count: int = 0
    addr: str = ""  # 12位BCD地址
    ctrl: int = 0  # 控制码
    data_len: int = 0  # 数据长度
    data_raw: bytes = b""  # 原始数据区(含+0x33)
    data_decoded: bytes = b""  # 解码后数据区(-0x33)

    # 645数据区解析
    di: str = ""  # 数据标识(4字节十六进制)
    payload: bytes = b""  # 除去DI后的有效数据

    # 校验和验证
    cs_calc: int = 0
    cs_recv: int = 0
    cs_ok: bool = False

    # 帧完整性
    frame_complete: bool = False
    frame_valid: bool = False

    # 错误信息
    error: str = ""


# 645帧常量
FRAME_START = 0x68
FRAME_END = 0x16

# 控制码定义
CTRL_READ = 0x11  # 读数据
CTRL_READ_RSP = 0x91  # 读数据响应
CTRL_WRITE = 0x14  # 写数据
CTRL_WRITE_RSP = 0x94  # 写数据响应


def reverse_bcd_addr(addr: str) -> bytes:
    """
    将12位BCD地址反转为字节序列
    例如: "000000000000" -> b'\x00\x00\x00\x00\x00\x00'
    广播地址: "AAAAAAAAAAAA" -> b'\xAA\xAA\xAA\xAA\xAA\xAA'
    地址按字节反转存储
    """
    if len(addr) != 12:
        raise ValueError(f"645地址必须是12位BCD码，实际是{len(addr)}位: {addr}")

    # 验证是BCD数字或广播地址(AA)
    addr_upper = addr.upper()
    if addr_upper == "AAAAAAAAAAAA":
        # 广播地址
        result = bytes.fromhex(addr)
    elif addr.isdigit():
        # BCD数字地址
        result = bytes.fromhex(addr)
    else:
        raise ValueError(f"645地址必须是BCD数字或广播地址(AA): {addr}")

    # 反转字节序
    return result[::-1]


def parse_bcd_addr(addr_bytes: bytes) -> str:
    """
    从字节序列解析BCD地址
    字节序列是反转存储的，需要再反转回来
    """
    if len(addr_bytes) != 6:
        return addr_bytes.hex().upper()

    # 反转回正常顺序
    normal = addr_bytes[::-1]
    return normal.hex().upper()


def di_to_bytes(di: str) -> bytes:
    """
    将8位十六进制DI转为4字节(小端序)
    例如: "00010000" -> b'\x00\x00\x01\x00'
    """
    if len(di) != 8:
        raise ValueError(f"DI必须是8位十六进制，实际是{len(di)}位")

    di_bytes = bytes.fromhex(di)
    # 小端序: 高低位交换
    return di_bytes[::-1]


def di_from_bytes(di_bytes: bytes) -> str:
    """从字节解析DI(小端序转回正常)"""
    if len(di_bytes) < 4:
        return di_bytes.hex().upper()

    # 小端序反转
    di_normal = di_bytes[:4][::-1]
    return di_normal.hex().upper()


def calc_cs(data: bytes) -> int:
    """计算645校验和: 从第一个0x68到数据区结束的所有字节累加和的低8位"""
    return sum(data) & 0xFF


def build_read_frame(req: Frame645Request) -> bytes:
    """
    构建645读数据帧
    格式: FE FE FE FE 68 A0 A1 A2 A3 A4 A5 68 11 L DI0 DI1 DI2 DI3 CS 16
    """
    # 前导FE
    frame = b'\xFE' * req.fe_count

    # 起始符1
    frame += bytes([FRAME_START])

    # 地址域(6字节，反转存储)
    addr_bytes = reverse_bcd_addr(req.addr)
    frame += addr_bytes

    # 起始符2
    frame += bytes([FRAME_START])

    # 控制码: 读数据
    frame += bytes([CTRL_READ])

    # 数据长度: DI占4字节
    data_len = 4
    frame += bytes([data_len])

    # 数据区: DI(小端序) + 0x33偏移
    di_bytes = di_to_bytes(req.di) if hasattr(req, 'di') and req.di else req.data[:4]
    di_offset = apply_645_offset_33(di_bytes)
    frame += di_offset

    # 计算校验和(从第一个0x68开始)
    cs_start = frame.find(bytes([FRAME_START]))
    cs_data = frame[cs_start:]
    cs = calc_cs(cs_data)
    frame += bytes([cs])

    # 结束符
    frame += bytes([FRAME_END])

    return frame


def build_write_frame(req: Frame645Request, di: str) -> bytes:
    """
    构建645写数据帧
    格式: FE FE FE FE 68 A0-A5 68 14 L DI0-DI3 D0-Dn CS 16
    数据区 = DI(小端) + 原始数据，全部+0x33
    """
    # 前导FE
    frame = b'\xFE' * req.fe_count

    # 起始符1
    frame += bytes([FRAME_START])

    # 地址域
    addr_bytes = reverse_bcd_addr(req.addr)
    frame += addr_bytes

    # 起始符2
    frame += bytes([FRAME_START])

    # 控制码: 写数据
    frame += bytes([CTRL_WRITE])

    # 数据长度: DI(4字节) + 数据长度
    di_bytes = di_to_bytes(di)
    data_len = 4 + len(req.data)
    frame += bytes([data_len])

    # 数据区: DI + 数据，全部+0x33
    full_data = di_bytes + req.data
    data_offset = apply_645_offset_33(full_data)
    frame += data_offset

    # 计算校验和
    cs_start = frame.find(bytes([FRAME_START]))
    cs_data = frame[cs_start:]
    cs = calc_cs(cs_data)
    frame += bytes([cs])

    # 结束符
    frame += bytes([FRAME_END])

    return frame


def parse_response_frame(frame: bytes, decode_hint: Optional[str] = None) -> Frame645Response:
    """
    解析645响应帧
    """
    rsp = Frame645Response()
    rsp.raw_frame = frame

    if len(frame) < 12:
        rsp.error = f"帧太短，至少12字节，实际{len(frame)}字节"
        return rsp

    pos = 0

    # 1. 跳过前导FE
    fe_count = 0
    while pos < len(frame) and frame[pos] == 0xFE:
        fe_count += 1
        pos += 1
    rsp.fe_count = fe_count

    # 2. 检查起始符1
    if pos >= len(frame) or frame[pos] != FRAME_START:
        rsp.error = "未找到起始符0x68"
        return rsp
    pos += 1

    # 3. 地址域(6字节)
    if pos + 6 > len(frame):
        rsp.error = "地址域不完整"
        return rsp
    addr_bytes = frame[pos:pos + 6]
    rsp.addr = parse_bcd_addr(addr_bytes)
    pos += 6

    # 4. 检查起始符2
    if pos >= len(frame) or frame[pos] != FRAME_START:
        rsp.error = "未找到第二个起始符0x68"
        return rsp
    pos += 1

    # 5. 控制码
    if pos >= len(frame):
        rsp.error = "缺少控制码"
        return rsp
    rsp.ctrl = frame[pos]
    pos += 1

    # 6. 数据长度
    if pos >= len(frame):
        rsp.error = "缺少数据长度"
        return rsp
    rsp.data_len = frame[pos]
    pos += 1

    # 7. 数据区
    if pos + rsp.data_len > len(frame):
        rsp.error = f"数据区不完整，期望{rsp.data_len}字节，实际{len(frame) - pos}字节"
        return rsp
    rsp.data_raw = frame[pos:pos + rsp.data_len]
    pos += rsp.data_len

    # 8. 校验和
    if pos >= len(frame):
        rsp.error = "缺少校验和"
        return rsp
    rsp.cs_recv = frame[pos]
    pos += 1

    # 9. 结束符
    if pos >= len(frame) or frame[pos] != FRAME_END:
        rsp.error = "未找到结束符0x16"
        return rsp
    pos += 1

    rsp.frame_complete = True

    # 计算校验和
    # CS从第一个0x68到数据区结束
    frame_start = frame.find(bytes([FRAME_START]))
    cs_end = frame_start + 1 + 6 + 1 + 1 + 1 + rsp.data_len  # 68 + 地址 + 68 + ctrl + len + data
    cs_data = frame[frame_start:cs_end]
    rsp.cs_calc = calc_cs(cs_data)
    rsp.cs_ok = (rsp.cs_calc == rsp.cs_recv)
    rsp.frame_valid = rsp.cs_ok

    # 解码数据区(-0x33)
    rsp.data_decoded = remove_645_offset_33(rsp.data_raw)

    # 提取DI和前4字节
    if len(rsp.data_decoded) >= 4:
        rsp.di = di_from_bytes(rsp.data_decoded)
        rsp.payload = rsp.data_decoded[4:]

    return rsp


def find_complete_frame(data: bytes) -> Optional[bytes]:
    """
    从字节流中提取完整的645帧
    645帧特征: ... FE* 68 AA AA AA AA AA AA 68 CC LL ... CS 16
    返回完整帧或None
    """
    # 寻找第一个0x68
    pos = 0
    while pos < len(data):
        # 跳过前导FE
        while pos < len(data) and data[pos] == 0xFE:
            pos += 1

        if pos >= len(data):
            break

        if data[pos] != FRAME_START:
            pos += 1
            continue

        frame_start = pos

        # 检查是否有足够长度
        # 68 + 6字节地址 + 68 + 1字节控制 + 1字节长度 = 至少10字节才能读到长度
        if pos + 10 > len(data):
            return None

        # 验证第二个0x68在位置pos+7
        if data[pos + 7] != FRAME_START:
            pos += 1
            continue

        # 读取数据长度
        data_len = data[pos + 9]

        # 计算完整帧长度: 从第一个68开始到16结束
        # 68(1) + 地址(6) + 68(1) + 控制(1) + 长度(1) + 数据(data_len) + CS(1) + 16(1)
        full_len = 1 + 6 + 1 + 1 + 1 + data_len + 1 + 1

        # 包含前导FE
        fe_start = frame_start
        while fe_start > 0 and data[fe_start - 1] == 0xFE:
            fe_start -= 1

        total_len = (frame_start - fe_start) + full_len

        if pos + full_len > len(data):
            return None

        # 验证结束符
        if data[pos + full_len - 1] != FRAME_END:
            pos += 1
            continue

        # 提取完整帧
        return data[fe_start:pos + full_len]

    return None


def encode_request(di: str, addr: str, op: str, value: Optional[str] = None,
                  fe_count: int = 4, raw_prefix: Optional[str] = None,
                  raw_suffix: Optional[str] = None) -> bytes:
    """
    编码645请求帧的高层接口

    参数:
        di: 数据标识，8位十六进制
        addr: 12位BCD地址
        op: 操作类型，'read' 或 'write'
        value: 写操作时的值(带类型前缀)
        fe_count: 前导FE个数
        raw_prefix: 前置原始字节(hex:...)
        raw_suffix: 后置原始字节(hex:...)

    返回:
        完整的645帧字节序列
    """
    req = Frame645Request(
        addr=addr,
        ctrl=CTRL_READ if op == "read" else CTRL_WRITE,
        data=b"",
        fe_count=fe_count
    )

    if op == "read":
        req.di = di
        return build_read_frame(req)
    elif op == "write":
        # 构建数据区: raw_prefix + value + raw_suffix
        data_parts = []

        if raw_prefix:
            prefix = encode_645_value(raw_prefix)
            data_parts.append(prefix)

        if value:
            val_bytes = encode_645_value(value)
            data_parts.append(val_bytes)

        if raw_suffix:
            suffix = encode_645_value(raw_suffix)
            data_parts.append(suffix)

        req.data = b"".join(data_parts)
        return build_write_frame(req, di)
    else:
        raise ValueError(f"不支持的操作: {op}")


def decode_response(frame: bytes, decode_hint: Optional[str] = None) -> Frame645Response:
    """
    解码645响应帧的高层接口

    参数:
        frame: 原始帧字节序列
        decode_hint: 可选的解码提示

    返回:
        Frame645Response对象
    """
    rsp = parse_response_frame(frame, decode_hint)

    # 应用decode_hint解码payload
    if decode_hint and rsp.payload:
        try:
            rsp.payload_decoded = decode_by_hint(rsp.payload, decode_hint)
        except Exception:
            pass  # 解码失败时保持原始值

    return rsp
