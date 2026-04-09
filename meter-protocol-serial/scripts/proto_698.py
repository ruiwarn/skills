# proto_698.py
# DL/T698.45 协议处理模块
# 负责698协议的组帧和解析
# 第一版只支持 GET.request.normal / SET.request.normal

import struct
from dataclasses import dataclass, field
from typing import Optional, List, Union
from value_codec import encode_698_value, decode_hex, decode_by_hint


@dataclass
class Frame698Request:
    """698请求帧结构"""
    server_addr: str  # 服务器地址
    client_addr: str  # 客户机地址
    service_type: int  # 服务类型: 5=GET, 6=SET
    oad: str  # OAD: 8位十六进制
    value: Optional[bytes] = None  # SET时的值


@dataclass
class Frame698Response:
    """698响应帧解析结果"""
    raw_frame: bytes = b""  # 原始帧

    # 链路层字段
    len_bytes: bytes = b""  # 长度域原始字节
    ctrl: int = 0  # 控制域
    server_addr: str = ""  # 服务器地址
    client_addr: str = ""  # 客户机地址
    hcs_calc: int = 0  # 计算的HCS
    hcs_recv: int = 0  # 收到的HCS
    hcs_ok: bool = False
    fcs_calc: int = 0  # 计算的FCS
    fcs_recv: int = 0  # 收到的FCS
    fcs_ok: bool = False

    # 应用层字段
    service_type: int = 0  # 服务类型
    service_response: int = 0  # 响应类型(如 GET-Response, SET-Response)
    piid: int = 0  # PIID
    oad: str = ""  # OAD
    dar: Optional[int] = None  # 数据访问结果(如果有)
    data: bytes = b""  # 数据区原始字节
    data_typed: Union[str, int, None] = None  # 类型化数据(如果能解析)

    # 解析状态
    frame_complete: bool = False
    frame_valid: bool = False
    error: str = ""


# 698帧常量
FRAME_START = 0x68
FRAME_END = 0x16

# 应用层APDU起始字节
APDU_START = 0x01

# 服务类型
SERVICE_GET = 0x05
SERVICE_SET = 0x06
SERVICE_RESPONSE_OFFSET = 0x80

# 响应类型
GET_RESPONSE_NORMAL = 0x01
SET_RESPONSE_NORMAL = 0x01

# DAR定义 (数据访问结果)
DAR_SUCCESS = 0x00


def calc_crc16(data: bytes, init: int = 0xFFFF) -> int:
    """
    计算CRC16 (IBM/SDLC标准)
    698使用CRC16-IBM: x^16 + x^15 + x^2 + 1
    """
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def parse_server_addr(addr_str: str) -> bytes:
    """
    解析服务器地址
    格式: 逻辑地址(1字节) + 物理地址(可变长)
    第一版简化: 支持直接传入完整地址字符串
    """
    # 移除空格和分隔符
    addr = addr_str.replace(" ", "").replace("-", "").replace(":", "")

    if len(addr) % 2 != 0:
        raise ValueError(f"服务器地址长度必须是偶数: {addr_str}")

    try:
        return bytes.fromhex(addr)
    except ValueError:
        raise ValueError(f"无效的服务器地址: {addr_str}")


def parse_client_addr(ca_str: str) -> bytes:
    """解析客户机地址(1字节)"""
    ca = ca_str.replace(" ", "")
    if len(ca) == 2:
        return bytes.fromhex(ca)
    elif len(ca) == 1:
        # 可能是单个字符的十六进制
        return bytes.fromhex(ca.zfill(2))
    else:
        raise ValueError(f"客户机地址必须是1字节(2位十六进制): {ca_str}")


def build_ctrl_byte(server_addr_len: int, is_downlink: bool = True) -> int:
    """
    构建698控制域字节

    控制域格式:
    - bit0: 传输方向 (0=客户机对服务器/下行, 1=服务器对客户机/上行)
    - bit1: 启动标志 (0=从动站, 1=启动站)
    - bit2: 分块标志 (0=不分块, 1=分块)
    - bit3: 保留
    - bit4: 保留
    - bit5-7: 服务器地址长度-1 (范围1-8字节, 编码为0-7)

    参数:
        server_addr_len: 服务器地址字节数 (1-8)
        is_downlink: True=下行(请求), False=上行(响应)
    """
    ctrl = 0x00

    # bit0: 传输方向 (下行=0, 上行=1)
    if not is_downlink:
        ctrl |= 0x01

    # bit1: 启动标志 (客户机发送=1)
    ctrl |= 0x02

    # bit5-7: 服务器地址长度-1
    addr_len_bits = (server_addr_len - 1) << 5
    ctrl |= addr_len_bits

    return ctrl


def build_link_header(server_addr: bytes, client_addr: bytes, apdu_len: int) -> bytes:
    """
    构建698链路层头部
    格式: 68 L L 68 C CA SA HCS APDU FCS 16

    其中L是长度域:
    - bit0-13: 用户数据长度(APDU长度)
    - bit14: 是否分块标志
    - bit15: 保留

    控制域C:
    - bit0: 传输方向 (0=下行, 1=上行)
    - bit1: 启动标志
    - bit2: 分块标志
    - bit5-7: 服务器地址长度-1
    """
    # 长度域: 14位长度 + bit14=0 + bit15=0
    user_data_len = apdu_len
    len_field = user_data_len & 0x3FFF

    # 构建长度域(小端序)
    len_bytes = struct.pack("<H", len_field)

    # 控制域: 根据服务器地址长度正确设置
    ctrl = build_ctrl_byte(len(server_addr), is_downlink=True)

    # 构建到HCS之前的数据
    header = bytes([FRAME_START])
    header += len_bytes
    header += bytes([FRAME_START])
    header += bytes([ctrl])
    header += client_addr
    header += server_addr

    # 计算HCS(包含长度域本身)
    hcs = calc_crc16(len_bytes + bytes([FRAME_START, ctrl]) + client_addr + server_addr)
    header += struct.pack("<H", hcs)

    return header


def complete_frame(header: bytes, apdu: bytes) -> bytes:
    """
    完成帧构建，添加APDU和FCS、结束符
    """
    frame = header + apdu

    # 计算FCS(从长度域开始到APDU结束，跳过第一个68)
    # 帧结构: 68(跳过) + LL(长度域) + 68 + C + CA + SA + HCS + APDU
    fcs_data = frame[1:]  # 跳过第一个68
    fcs = calc_crc16(fcs_data)
    frame += struct.pack("<H", fcs)

    # 结束符
    frame += bytes([FRAME_END])

    return frame


def build_apdu_get_normal(oad: str, piid: int = 0x00) -> bytes:
    """
    构建GET.request.normal的APDU
    APDU格式: 01 (APDU标签) + 服务类型 + PIID + OAD
    """
    # APDU起始
    apdu = bytes([APDU_START])

    # 服务类型: GET-Request (0x05)
    apdu += bytes([SERVICE_GET])

    # 服务选择: GET-Request-normal = 1
    apdu += bytes([0x01])

    # PIID (1字节)
    apdu += bytes([piid & 0xFF])

    # OAD (4字节)
    oad_bytes = bytes.fromhex(oad)
    if len(oad_bytes) != 4:
        raise ValueError(f"OAD必须是4字节: {oad}")
    apdu += oad_bytes

    return apdu


def build_apdu_set_normal(oad: str, value: bytes, piid: int = 0x00) -> bytes:
    """
    构建SET.request.normal的APDU
    APDU格式: 01 (APDU标签) + 服务类型 + 服务选择 + PIID + OAD + Data
    """
    # APDU起始
    apdu = bytes([APDU_START])

    # 服务类型: SET-Request (0x06)
    apdu += bytes([SERVICE_SET])

    # 服务选择: SET-Request-normal = 1
    apdu += bytes([0x01])

    # PIID (1字节)
    apdu += bytes([piid & 0xFF])

    # OAD (4字节)
    oad_bytes = bytes.fromhex(oad)
    if len(oad_bytes) != 4:
        raise ValueError(f"OAD必须是4字节: {oad}")
    apdu += oad_bytes

    # Data (编码后的值)
    apdu += value

    return apdu


def parse_apdu(apdu: bytes) -> dict:
    """
    解析APDU，提取关键信息
    第一版只做基础解析
    """
    result = {
        "apdu_start": 0,
        "service_type": 0,
        "service_response": 0,
        "piid": 0,
        "oad": "",
        "dar": None,
        "data": b"",
        "data_type": None,
    }

    if len(apdu) < 2:
        return result

    pos = 0

    # APDU起始标签
    if apdu[pos] != APDU_START:
        return result
    result["apdu_start"] = apdu[pos]
    pos += 1

    if pos >= len(apdu):
        return result

    # 服务类型
    service = apdu[pos]
    result["service_type"] = service
    pos += 1

    if pos >= len(apdu):
        return result

    # 响应类型
    response_type = apdu[pos]
    result["service_response"] = response_type
    pos += 1

    if pos >= len(apdu):
        return result

    # PIID
    result["piid"] = apdu[pos]
    pos += 1

    if pos + 4 > len(apdu):
        return result

    # OAD
    oad_bytes = apdu[pos:pos + 4]
    result["oad"] = oad_bytes.hex().upper()
    pos += 4

    # 检查是否有DAR
    if pos < len(apdu):
        # 简单判断: 如果下一个字节是0x00表示成功，否则可能是DAR
        next_byte = apdu[pos]

        # 检查是否是Data标签 (简单判断)
        if next_byte in (0x00,):  # DAR=0表示成功
            result["dar"] = next_byte
            pos += 1
        elif next_byte < 0x80:  # 可能是长度或类型标签
            # 尝试解析A-XDR数据
            data, data_type = parse_axdr_data(apdu[pos:])
            result["data"] = data
            result["data_type"] = data_type
        else:
            # 原始数据
            result["data"] = apdu[pos:]

    return result


def parse_axdr_data(data: bytes) -> tuple:
    """
    简单解析A-XDR编码数据
    第一版只支持基本类型

    返回: (原始数据, 类型名称)
    """
    if len(data) == 0:
        return (b"", None)

    first_byte = data[0]

    # 基本类型标签
    if first_byte == 0x01:  # BOOL
        if len(data) >= 2:
            return (data[:2], "bool")
    elif first_byte == 0x02:  # BIT-STRING (简化处理)
        if len(data) >= 2:
            bit_len = data[1]
            return (data[:2 + bit_len], "bit_string")
    elif first_byte == 0x03:  # DOUBLE-LONG (int32)
        if len(data) >= 5:
            return (data[:5], "int32")
    elif first_byte == 0x05:  # UNSIGNED32
        if len(data) >= 5:
            return (data[:5], "uint32")
    elif first_byte == 0x06:  # OCTET-STRING
        if len(data) >= 2:
            str_len = data[1]
            return (data[:2 + str_len], "octet_string")
    elif first_byte == 0x0A:  # VISIBLE-STRING
        if len(data) >= 2:
            str_len = data[1]
            return (data[:2 + str_len], "string")
    elif first_byte == 0x10:  # INTEGER
        if len(data) >= 2:
            int_len = data[1]
            return (data[:2 + int_len], "integer")
    elif first_byte == 0x12:  # UNSIGNED
        if len(data) >= 2:
            uint_len = data[1]
            return (data[:2 + uint_len], "unsigned")
    elif first_byte == 0x16:  # ENUM
        if len(data) >= 2:
            return (data[:2], "enum")

    # 未知类型，返回全部
    return (data, "raw")


def decode_axdr_to_value(data: bytes, data_type: str) -> Union[str, int, None]:
    """
    将A-XDR编码数据解码为Python值
    """
    if len(data) < 1:
        return None

    try:
        if data_type == "bool" and len(data) >= 2:
            return data[1] != 0
        elif data_type == "int32" and len(data) >= 5:
            return struct.unpack(">i", data[1:5])[0]
        elif data_type == "uint32" and len(data) >= 5:
            return struct.unpack(">I", data[1:5])[0]
        elif data_type == "octet_string" and len(data) >= 2:
            str_len = data[1]
            return data[2:2 + str_len].hex().upper()
        elif data_type == "string" and len(data) >= 2:
            str_len = data[1]
            try:
                return data[2:2 + str_len].decode("ascii")
            except UnicodeDecodeError:
                return data[2:2 + str_len].hex().upper()
        elif data_type == "enum" and len(data) >= 2:
            return data[1]
        else:
            return data.hex().upper()
    except Exception:
        return data.hex().upper()


def encode_request(server_addr: str, client_addr: str, op: str, oad: str,
                  value: Optional[str] = None) -> bytes:
    """
    编码698请求帧的高层接口

    参数:
        server_addr: 服务器地址
        client_addr: 客户机地址
        op: 操作类型，'read'(GET) 或 'set'(SET)
        oad: OAD，8位十六进制
        value: SET操作时的值(带类型前缀)

    返回:
        完整的698帧字节序列
    """
    # 解析地址
    server_bytes = parse_server_addr(server_addr)
    client_bytes = parse_client_addr(client_addr)

    # 构建APDU
    if op == "read":
        apdu = build_apdu_get_normal(oad)
    elif op == "set":
        if value is None:
            raise ValueError("SET操作需要提供value参数")
        val_bytes = encode_698_value(value)
        apdu = build_apdu_set_normal(oad, val_bytes)
    else:
        raise ValueError(f"698不支持的操作: {op}")

    # 构建链路层头部
    header = build_link_header(server_bytes, client_bytes, len(apdu))

    # 完成帧
    return complete_frame(header, apdu)


def parse_response(frame: bytes, decode_hint: Optional[str] = None) -> Frame698Response:
    """
    解析698响应帧的高层接口

    参数:
        frame: 原始帧字节序列
        decode_hint: 可选的解码提示

    返回:
        Frame698Response对象
    """
    rsp = Frame698Response()
    rsp.raw_frame = frame

    if len(frame) < 12:
        rsp.error = f"帧太短，至少12字节，实际{len(frame)}字节"
        return rsp

    pos = 0

    # 1. 起始符
    if frame[pos] != FRAME_START:
        rsp.error = "未找到起始符0x68"
        return rsp
    pos += 1

    # 2. 长度域(2字节，小端)
    if pos + 2 > len(frame):
        rsp.error = "长度域不完整"
        return rsp
    rsp.len_bytes = frame[pos:pos + 2]
    len_field = struct.unpack("<H", rsp.len_bytes)[0]
    user_data_len = len_field & 0x3FFF
    pos += 2

    # 3. 第二个起始符
    if pos >= len(frame) or frame[pos] != FRAME_START:
        rsp.error = "未找到第二个起始符0x68"
        return rsp
    pos += 1

    # 4. 控制域
    if pos >= len(frame):
        rsp.error = "缺少控制域"
        return rsp
    rsp.ctrl = frame[pos]
    pos += 1

    # 5. 地址域长度 (从控制域bit5-7)
    addr_len = ((rsp.ctrl >> 5) & 0x07) + 1

    # 6. 客户机地址(1字节)
    if pos >= len(frame):
        rsp.error = "缺少客户机地址"
        return rsp
    rsp.client_addr = frame[pos:pos + 1].hex().upper()
    pos += 1

    # 7. 服务器地址
    if pos + addr_len > len(frame):
        rsp.error = "服务器地址不完整"
        return rsp
    rsp.server_addr = frame[pos:pos + addr_len].hex().upper()
    pos += addr_len

    # 8. HCS(2字节)
    if pos + 2 > len(frame):
        rsp.error = "缺少HCS"
        return rsp
    rsp.hcs_recv = struct.unpack("<H", frame[pos:pos + 2])[0]

    # 计算HCS
    hcs_data = rsp.len_bytes + bytes([FRAME_START, rsp.ctrl]) + \
               bytes.fromhex(rsp.client_addr) + bytes.fromhex(rsp.server_addr)
    rsp.hcs_calc = calc_crc16(hcs_data)
    rsp.hcs_ok = (rsp.hcs_calc == rsp.hcs_recv)
    pos += 2

    # 9. APDU
    apdu_end = len(frame) - 3  # 留出FCS(2)和16(1)的位置
    if apdu_end <= pos:
        rsp.error = "APDU区域不完整"
        return rsp

    apdu = frame[pos:apdu_end]
    pos = apdu_end

    # 10. FCS
    if pos + 2 > len(frame):
        rsp.error = "缺少FCS"
        return rsp
    rsp.fcs_recv = struct.unpack("<H", frame[pos:pos + 2])[0]

    # 计算FCS(从长度域到APDU结束)
    fcs_data = frame[1:apdu_end]  # 从长度域开始，跳过第一个68
    rsp.fcs_calc = calc_crc16(fcs_data)
    rsp.fcs_ok = (rsp.fcs_calc == rsp.fcs_recv)
    pos += 2

    # 11. 结束符
    if pos >= len(frame) or frame[pos] != FRAME_END:
        rsp.error = "未找到结束符0x16"
        return rsp

    rsp.frame_complete = True
    rsp.frame_valid = rsp.hcs_ok and rsp.fcs_ok

    # 解析APDU
    apdu_info = parse_apdu(apdu)
    rsp.service_type = apdu_info["service_type"]
    rsp.service_response = apdu_info["service_response"]
    rsp.piid = apdu_info["piid"]
    rsp.oad = apdu_info["oad"]
    rsp.dar = apdu_info["dar"]
    rsp.data = apdu_info["data"]

    # 尝试类型化解析
    if apdu_info["data"] and apdu_info["data_type"]:
        rsp.data_typed = decode_axdr_to_value(apdu_info["data"], apdu_info["data_type"])

    # 应用decode_hint
    if decode_hint and rsp.data:
        try:
            decoded = decode_by_hint(rsp.data, decode_hint)
            if decoded:
                rsp.data_typed = decoded
        except Exception:
            pass

    return rsp


def find_complete_frame(data: bytes) -> Optional[bytes]:
    """
    从字节流中提取完整的698帧
    698帧特征: 68 L0 L1 68 CA SA... FCS0 FCS1 16
    """
    pos = 0
    while pos < len(data) - 11:  # 至少要有基本帧头
        if data[pos] != FRAME_START:
            pos += 1
            continue

        # 检查长度域
        if pos + 3 >= len(data):
            return None

        len_field = struct.unpack("<H", data[pos + 1:pos + 3])[0]
        user_data_len = len_field & 0x3FFF

        # 检查第二个68
        if pos + 3 >= len(data) or data[pos + 3] != FRAME_START:
            pos += 1
            continue

        # 计算完整帧长度
        # 68(1) + L(2) + 68(1) + C(1) + CA(1) + SA(n) + HCS(2) + APDU(user_data_len) + FCS(2) + 16(1)
        # 需要从控制域获取地址长度
        if pos + 4 >= len(data):
            return None

        ctrl = data[pos + 4]
        addr_len = ((ctrl >> 5) & 0x07) + 1

        full_len = 1 + 2 + 1 + 1 + 1 + addr_len + 2 + user_data_len + 2 + 1

        if pos + full_len > len(data):
            return None

        # 验证结束符
        if data[pos + full_len - 1] != FRAME_END:
            pos += 1
            continue

        # 提取帧
        return data[pos:pos + full_len]

    return None
