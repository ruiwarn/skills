# proto_698.py
# DL/T698.45 协议处理模块
# 负责698协议的组帧和解析
#
# 帧格式 (Section 6.2):
#   68 | LL(2) C(1) SA(1+N) CA(1) HCS(2) APDU(M) FCS(2) | 16
#   L = 从L自身到FCS(含)的总字节数, 存储为小端14位
#   HCS = FCS-16(LL + C + SA + CA), 不含68和HCS自身
#   FCS = FCS-16(LL + C + SA + CA + HCS + APDU), 不含68和FCS自身
#
# Client-APDU tags: GET-Request[5], SET-Request[6], ACTION-Request[7]
# Server-APDU tags: GET-Response[133/0x85], SET-Response[134/0x86]

import struct
from dataclasses import dataclass, field
from typing import Optional, List, Union
from value_codec import encode_698_value, decode_hex, decode_by_hint


@dataclass
class Frame698Request:
    """698请求帧结构"""
    server_addr: str
    client_addr: str
    service_type: int  # 5=GET, 6=SET
    oad: str  # 8位十六进制
    value: Optional[bytes] = None


@dataclass
class Frame698Response:
    """698响应帧解析结果"""
    raw_frame: bytes = b""

    # 链路层字段
    len_bytes: bytes = b""
    ctrl: int = 0
    server_addr: str = ""
    client_addr: str = ""
    hcs_calc: int = 0
    hcs_recv: int = 0
    hcs_ok: bool = False
    fcs_calc: int = 0
    fcs_recv: int = 0
    fcs_ok: bool = False

    # 应用层字段
    service_type: int = 0
    service_response: int = 0
    piid: int = 0
    oad: str = ""
    dar: Optional[int] = None
    data: bytes = b""
    data_typed: Union[str, int, None] = None

    # 解析状态
    frame_complete: bool = False
    frame_valid: bool = False
    error: str = ""


# 698帧常量
FRAME_START = 0x68
FRAME_END = 0x16

# Client-APDU service tags (Section 7.4.1.2)
SERVICE_GET = 0x05       # [5] GET-Request
SERVICE_SET = 0x06       # [6] SET-Request
SERVICE_ACTION = 0x07    # [7] ACTION-Request

# Server-APDU service tags (Section 7.4.1.3)
SERVICE_GET_RESP = 0x85   # [133] GET-Response
SERVICE_SET_RESP = 0x86   # [134] SET-Response
SERVICE_ACTION_RESP = 0x87  # [135] ACTION-Response

# GET-Request subtypes
GET_REQUEST_NORMAL = 0x01
GET_REQUEST_NORMAL_LIST = 0x02

# SET-Request subtypes
SET_REQUEST_NORMAL = 0x01
SET_REQUEST_NORMAL_LIST = 0x02

# DAR定义 (数据访问结果)
DAR_SUCCESS = 0x00


def calc_fcs16(data: bytes) -> int:
    """
    计算 FCS-16 (CRC-16/X.25), 按 DL/T698.45 附录D.

    多项式: x^16 + x^12 + x^5 + 1, 反射形式 0x8408
    初值: 0xFFFF
    最终: 结果 XOR 0xFFFF (取反)
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    crc ^= 0xFFFF
    return crc & 0xFFFF


def build_addr_feature(addr_type: int, logic_addr: int, addr_len: int) -> int:
    """
    构建698地址特征字节
    
    地址特征字节格式:
    - bit6-7: 地址类型 (0=单地址, 1=通配地址, 2=组地址, 3=广播)
    - bit4-5: 逻辑地址 (0-3)
    - bit0-3: 地址字节数-1 (范围1-16字节, 编码为0-15)
    
    参数:
        addr_type: 地址类型 0-3
        logic_addr: 逻辑地址 0-3
        addr_len: 地址字节数 1-16
    """
    feature = 0
    feature |= (addr_type & 0x03) << 6
    feature |= (logic_addr & 0x03) << 4
    feature |= (addr_len - 1) & 0x0F
    return feature


def parse_server_addr(addr_str: str, addr_type: int = 1, logic_addr: int = 0) -> bytes:
    """
    解析服务器地址并构建完整的SA字段
    
    698协议SA格式: 地址特征字节(1B) + 实际地址(NB)
    
    参数:
        addr_str: 地址字符串(十六进制)
        addr_type: 地址类型 (0=单地址, 1=通配地址, 2=组地址, 3=广播)
        logic_addr: 逻辑地址 0-3
    
    返回:
        完整的SA字节序列 (特征字节 + 地址)
    """
    # 移除空格和分隔符
    addr = addr_str.replace(" ", "").replace("-", "").replace(":", "")
    
    if len(addr) % 2 != 0:
        raise ValueError(f"服务器地址长度必须是偶数: {addr_str}")
    
    try:
        addr_bytes = bytes.fromhex(addr)
    except ValueError:
        raise ValueError(f"无效的服务器地址: {addr_str}")
    
    # 构建地址特征字节
    addr_len = len(addr_bytes)
    if addr_len < 1 or addr_len > 16:
        raise ValueError(f"698服务器地址长度必须在1-16字节之间: {addr_len}")
    
    feature = build_addr_feature(addr_type, logic_addr, addr_len)
    
    # 返回 特征字节 + 地址
    return bytes([feature]) + addr_bytes


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


def build_ctrl_byte(is_downlink: bool = True, is_start_station: bool = True, 
                    slice_flag: bool = False, sc_flag: bool = False, 
                    func_code: int = 3) -> int:
    """
    构建698控制域字节

    控制域格式:
    - bit7: 传输方向DIR (0=客户机对服务器/下行, 1=服务器对客户机/上行)
    - bit6: 启动标志PRM (0=从动站, 1=启动站)
    - bit5: 分帧标志 (0=完整APDU, 1=APDU片段)
    - bit4: 保留
    - bit3: 扰码标志SC (0=不加扰码, 1=加扰码)
    - bit2-0: 功能码
    
    常用功能码:
    - 1: 链路管理 (链路检测/断开)
    - 2: 保留
    - 3: 应用层数据服务

    参数:
        is_downlink: True=下行(请求), False=上行(响应)
        is_start_station: True=启动站, False=从动站
        slice_flag: True=分帧, False=完整帧
        sc_flag: True=加扰码, False=不加
        func_code: 功能码 0-7
    """
    ctrl = 0x00
    
    # bit7: 传输方向
    if not is_downlink:
        ctrl |= 0x80
    
    # bit6: 启动标志
    if is_start_station:
        ctrl |= 0x40
    
    # bit5: 分帧标志
    if slice_flag:
        ctrl |= 0x20
    
    # bit3: 扰码标志
    if sc_flag:
        ctrl |= 0x08
    
    # bit2-0: 功能码
    ctrl |= (func_code & 0x07)
    
    return ctrl


def build_frame(sa_bytes: bytes, ca_bytes: bytes, apdu: bytes,
                ctrl: Optional[int] = None) -> bytes:
    """
    构建完整的698帧.

    帧格式: 68 LL C SA CA HCS APDU FCS 16
    L = LL(2) + C(1) + SA + CA + HCS(2) + APDU + FCS(2) 的总字节数
    HCS = FCS-16(LL + C + SA + CA)
    FCS = FCS-16(LL + C + SA + CA + HCS + APDU)
    """
    if ctrl is None:
        ctrl = build_ctrl_byte(is_downlink=True, is_start_station=True,
                               slice_flag=False, sc_flag=False, func_code=3)

    # L = 2(LL) + 1(C) + len(SA) + len(CA) + 2(HCS) + len(APDU) + 2(FCS)
    l_value = 2 + 1 + len(sa_bytes) + len(ca_bytes) + 2 + len(apdu) + 2
    len_bytes = struct.pack("<H", l_value & 0x3FFF)

    # HCS covers: LL + C + SA + CA
    hcs_data = len_bytes + bytes([ctrl]) + sa_bytes + ca_bytes
    hcs = calc_fcs16(hcs_data)
    hcs_bytes = struct.pack("<H", hcs)

    # FCS covers: LL + C + SA + CA + HCS + APDU
    fcs_data = hcs_data + hcs_bytes + apdu
    fcs = calc_fcs16(fcs_data)
    fcs_bytes = struct.pack("<H", fcs)

    # Assemble: 68 + LL + C + SA + CA + HCS + APDU + FCS + 16
    frame = bytes([FRAME_START])
    frame += len_bytes
    frame += bytes([ctrl])
    frame += sa_bytes
    frame += ca_bytes
    frame += hcs_bytes
    frame += apdu
    frame += fcs_bytes
    frame += bytes([FRAME_END])
    return frame


def build_apdu_get_normal(oad: str, piid: int = 0x00) -> bytes:
    """
    构建 GET-Request Normal APDU (附录H.3.1).

    格式: 05 01 PIID OAD(4) 00
    05 = [5] GET-Request
    01 = [1] GetRequestNormal
    PIID = 1 byte
    OAD = 4 bytes
    00 = TimeTag OPTIONAL absent
    """
    oad_bytes = bytes.fromhex(oad)
    if len(oad_bytes) != 4:
        raise ValueError(f"OAD必须是4字节: {oad}")

    apdu = bytes([SERVICE_GET, GET_REQUEST_NORMAL, piid & 0xFF])
    apdu += oad_bytes
    apdu += bytes([0x00])  # no TimeTag
    return apdu


def build_apdu_get_normal_list(oads: list, piid: int = 0x00) -> bytes:
    """
    构建 GET-Request NormalList APDU.

    格式: 05 02 PIID count OAD1 OAD2 ... 00
    """
    apdu = bytes([SERVICE_GET, GET_REQUEST_NORMAL_LIST, piid & 0xFF])
    apdu += bytes([len(oads)])
    for oad in oads:
        oad_bytes = bytes.fromhex(oad)
        if len(oad_bytes) != 4:
            raise ValueError(f"OAD必须是4字节: {oad}")
        apdu += oad_bytes
    apdu += bytes([0x00])  # no TimeTag
    return apdu


def build_apdu_set_normal(oad: str, value: bytes, piid: int = 0x00) -> bytes:
    """
    构建 SET-Request Normal APDU.

    格式: 06 01 PIID OAD(4) Data 00
    06 = [6] SET-Request
    01 = [1] SetRequestNormal
    """
    oad_bytes = bytes.fromhex(oad)
    if len(oad_bytes) != 4:
        raise ValueError(f"OAD必须是4字节: {oad}")

    apdu = bytes([SERVICE_SET, SET_REQUEST_NORMAL, piid & 0xFF])
    apdu += oad_bytes
    apdu += value
    apdu += bytes([0x00])  # no TimeTag
    return apdu


def parse_apdu(apdu: bytes) -> dict:
    """
    解析APDU, 提取关键信息.

    GET-Response Normal (附录H.3.1):
      85 01 PIID_ACD OAD choice(01=Data|00=DAR) ...data... FollowReport TimeTag

    SET-Response Normal:
      86 01 PIID_ACD OAD DAR
    """
    result = {
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

    # 服务类型 (第一个字节: 0x85=GET-Response, 0x86=SET-Response, etc.)
    result["service_type"] = apdu[pos]
    pos += 1

    # 服务子类型 (1=Normal, 2=NormalList, etc.)
    result["service_response"] = apdu[pos]
    pos += 1

    if pos >= len(apdu):
        return result

    # PIID or PIID-ACD
    result["piid"] = apdu[pos]
    pos += 1

    if pos + 4 > len(apdu):
        return result

    # OAD (4 bytes)
    oad_bytes = apdu[pos:pos + 4]
    result["oad"] = oad_bytes.hex().upper()
    pos += 4

    # 判断是GET-Response还是SET-Response
    service = result["service_type"]

    if service == SERVICE_GET_RESP:
        # GET-Response: choice byte: 0=DAR(error), 1=Data
        if pos < len(apdu):
            choice = apdu[pos]
            pos += 1
            if choice == 0x00:
                # DAR error code
                if pos < len(apdu):
                    result["dar"] = apdu[pos]
                    pos += 1
            elif choice == 0x01:
                # Data follows — parse A-XDR
                remaining = apdu[pos:]
                # Skip trailing FollowReport(1) + TimeTag(1) if present
                data, data_type = parse_axdr_data(remaining)
                result["data"] = data
                result["data_type"] = data_type
            else:
                result["data"] = apdu[pos:]
    elif service == SERVICE_SET_RESP:
        # SET-Response: DAR directly
        if pos < len(apdu):
            result["dar"] = apdu[pos]
            pos += 1
    else:
        # Unknown service — store remaining as raw data
        result["data"] = apdu[pos:]

    return result


def parse_axdr_data(data: bytes) -> tuple:
    """
    解析A-XDR编码数据 (Section 7.2 type tags).

    Tags: NULL=0, array=1, structure=2, bool=3, bit-string=4,
    double-long(int32)=5, double-long-unsigned(uint32)=6,
    octet-string=9, visible-string=10, UTF8-string=12,
    integer(int8)=15, long(int16)=16, unsigned(uint8)=17,
    long-unsigned(uint16)=18, long64=20, long64-unsigned=21,
    enum=22, float32=23, float64=24,
    date_time=25, date=26, time=27, date_time_s=28
    """
    if len(data) == 0:
        return (b"", None)

    tag = data[0]

    if tag == 0:  # NULL
        return (data[:1], "null")
    elif tag == 3:  # bool
        if len(data) >= 2:
            return (data[:2], "bool")
    elif tag == 4:  # bit-string: length(1 byte = num bits) + data
        if len(data) >= 2:
            num_bits = data[1]
            byte_count = (num_bits + 7) // 8
            total = 2 + byte_count
            if len(data) >= total:
                return (data[:total], "bit_string")
    elif tag == 5:  # double-long (int32): 4 bytes BE
        if len(data) >= 5:
            return (data[:5], "int32")
    elif tag == 6:  # double-long-unsigned (uint32): 4 bytes BE
        if len(data) >= 5:
            return (data[:5], "uint32")
    elif tag == 9:  # octet-string: length(1) + data
        if len(data) >= 2:
            slen = data[1]
            total = 2 + slen
            if len(data) >= total:
                return (data[:total], "octet_string")
    elif tag == 10:  # visible-string: length(1) + data
        if len(data) >= 2:
            slen = data[1]
            total = 2 + slen
            if len(data) >= total:
                return (data[:total], "visible_string")
    elif tag == 12:  # UTF8-string: length(1) + data
        if len(data) >= 2:
            slen = data[1]
            total = 2 + slen
            if len(data) >= total:
                return (data[:total], "utf8_string")
    elif tag == 15:  # integer (int8): 1 byte
        if len(data) >= 2:
            return (data[:2], "int8")
    elif tag == 16:  # long (int16): 2 bytes BE
        if len(data) >= 3:
            return (data[:3], "int16")
    elif tag == 17:  # unsigned (uint8): 1 byte
        if len(data) >= 2:
            return (data[:2], "uint8")
    elif tag == 18:  # long-unsigned (uint16): 2 bytes BE
        if len(data) >= 3:
            return (data[:3], "uint16")
    elif tag == 20:  # long64 (int64): 8 bytes BE
        if len(data) >= 9:
            return (data[:9], "int64")
    elif tag == 21:  # long64-unsigned (uint64): 8 bytes BE
        if len(data) >= 9:
            return (data[:9], "uint64")
    elif tag == 22:  # enum: 1 byte
        if len(data) >= 2:
            return (data[:2], "enum")
    elif tag == 23:  # float32: 4 bytes
        if len(data) >= 5:
            return (data[:5], "float32")
    elif tag == 24:  # float64: 8 bytes
        if len(data) >= 9:
            return (data[:9], "float64")
    elif tag == 25:  # date_time: 10 bytes
        if len(data) >= 11:
            return (data[:11], "date_time")
    elif tag == 26:  # date: 5 bytes
        if len(data) >= 6:
            return (data[:6], "date")
    elif tag == 27:  # time: 3 bytes
        if len(data) >= 4:
            return (data[:4], "time")
    elif tag == 28:  # date_time_s: 7 bytes
        if len(data) >= 8:
            return (data[:8], "date_time_s")
    elif tag == 1:  # array
        return (data, "array")
    elif tag == 2:  # structure
        return (data, "structure")

    return (data, "raw")


def decode_axdr_to_value(data: bytes, data_type: str) -> Union[str, int, None]:
    """将A-XDR编码数据解码为Python值"""
    if len(data) < 1:
        return None

    try:
        if data_type == "null":
            return None
        elif data_type == "bool" and len(data) >= 2:
            return data[1] != 0
        elif data_type == "int8" and len(data) >= 2:
            return struct.unpack(">b", data[1:2])[0]
        elif data_type == "int16" and len(data) >= 3:
            return struct.unpack(">h", data[1:3])[0]
        elif data_type == "int32" and len(data) >= 5:
            return struct.unpack(">i", data[1:5])[0]
        elif data_type == "int64" and len(data) >= 9:
            return struct.unpack(">q", data[1:9])[0]
        elif data_type == "uint8" and len(data) >= 2:
            return data[1]
        elif data_type == "uint16" and len(data) >= 3:
            return struct.unpack(">H", data[1:3])[0]
        elif data_type == "uint32" and len(data) >= 5:
            return struct.unpack(">I", data[1:5])[0]
        elif data_type == "uint64" and len(data) >= 9:
            return struct.unpack(">Q", data[1:9])[0]
        elif data_type == "float32" and len(data) >= 5:
            return struct.unpack(">f", data[1:5])[0]
        elif data_type == "float64" and len(data) >= 9:
            return struct.unpack(">d", data[1:9])[0]
        elif data_type == "octet_string" and len(data) >= 2:
            slen = data[1]
            return data[2:2 + slen].hex().upper()
        elif data_type == "visible_string" and len(data) >= 2:
            slen = data[1]
            try:
                return data[2:2 + slen].decode("ascii")
            except UnicodeDecodeError:
                return data[2:2 + slen].hex().upper()
        elif data_type == "utf8_string" and len(data) >= 2:
            slen = data[1]
            try:
                return data[2:2 + slen].decode("utf-8")
            except UnicodeDecodeError:
                return data[2:2 + slen].hex().upper()
        elif data_type == "enum" and len(data) >= 2:
            return data[1]
        elif data_type == "date_time" and len(data) >= 11:
            return data[1:11].hex().upper()
        elif data_type == "date" and len(data) >= 6:
            return data[1:6].hex().upper()
        elif data_type == "time" and len(data) >= 4:
            return data[1:4].hex().upper()
        elif data_type == "date_time_s" and len(data) >= 8:
            return data[1:8].hex().upper()
        else:
            return data.hex().upper()
    except Exception:
        return data.hex().upper()


def encode_request(server_addr: str, client_addr: str, op: str, oad: str,
                  value: Optional[str] = None) -> bytes:
    """
    编码698请求帧.

    参数:
        server_addr: 服务器地址(纯地址,不含特征字节)
        client_addr: 客户机地址
        op: 'read'(GET) 或 'set'(SET)
        oad: OAD, 8位十六进制
        value: SET操作时的值(带类型前缀)
    返回:
        完整的698帧字节序列 (不含前导FE)
    """
    sa_bytes = parse_server_addr(server_addr, addr_type=1, logic_addr=0)
    ca_bytes = parse_client_addr(client_addr)

    if op == "read":
        apdu = build_apdu_get_normal(oad)
    elif op == "set":
        if value is None:
            raise ValueError("SET操作需要提供value参数")
        val_bytes = encode_698_value(value)
        apdu = build_apdu_set_normal(oad, val_bytes)
    else:
        raise ValueError(f"698不支持的操作: {op}")

    return build_frame(sa_bytes, ca_bytes, apdu)


def parse_response(frame: bytes, decode_hint: Optional[str] = None) -> Frame698Response:
    """
    解析698响应帧.

    帧格式: 68 LL(2) C(1) SA(1+N) CA(1) HCS(2) APDU(M) FCS(2) 16
    注意: 只有一个 0x68, 没有第二个!
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

    # 2. 长度域 (2字节, 小端)
    if pos + 2 > len(frame):
        rsp.error = "长度域不完整"
        return rsp
    rsp.len_bytes = frame[pos:pos + 2]
    len_field = struct.unpack("<H", rsp.len_bytes)[0]
    l_value = len_field & 0x3FFF
    pos += 2

    # 3. 控制域 C (1字节) — 紧跟在LL之后, 没有第二个68!
    if pos >= len(frame):
        rsp.error = "缺少控制域"
        return rsp
    rsp.ctrl = frame[pos]
    pos += 1

    # 4. 服务器地址 SA (特征字节 + 地址)
    if pos >= len(frame):
        rsp.error = "缺少服务器地址"
        return rsp
    addr_feature = frame[pos]
    addr_len = (addr_feature & 0x0F) + 1
    sa_total_len = 1 + addr_len

    if pos + sa_total_len > len(frame):
        rsp.error = f"服务器地址不完整，需要{sa_total_len}字节"
        return rsp
    sa_bytes = frame[pos:pos + sa_total_len]
    rsp.server_addr = sa_bytes.hex().upper()
    pos += sa_total_len

    # 5. 客户机地址 CA (1字节)
    if pos >= len(frame):
        rsp.error = "缺少客户机地址"
        return rsp
    ca_byte = frame[pos:pos + 1]
    rsp.client_addr = f"{frame[pos]:02X}"
    pos += 1

    # 6. HCS (2字节)
    if pos + 2 > len(frame):
        rsp.error = "缺少HCS"
        return rsp
    rsp.hcs_recv = struct.unpack("<H", frame[pos:pos + 2])[0]

    # HCS covers: LL + C + SA + CA (不含68, 不含HCS自身)
    hcs_data = rsp.len_bytes + bytes([rsp.ctrl]) + sa_bytes + ca_byte
    rsp.hcs_calc = calc_fcs16(hcs_data)
    rsp.hcs_ok = (rsp.hcs_calc == rsp.hcs_recv)
    pos += 2

    # 7. APDU (从HCS之后到FCS之前)
    # 帧总长 = 1(68) + l_value + 1(16) = len(frame)
    # FCS在倒数第3-2字节, 16在最后
    apdu_end = len(frame) - 3  # FCS(2) + 16(1)
    if apdu_end <= pos:
        rsp.error = "APDU区域不完整"
        return rsp

    apdu = frame[pos:apdu_end]
    pos = apdu_end

    # 8. FCS (2字节)
    if pos + 2 > len(frame):
        rsp.error = "缺少FCS"
        return rsp
    rsp.fcs_recv = struct.unpack("<H", frame[pos:pos + 2])[0]

    # FCS covers: LL + C + SA + CA + HCS + APDU (不含68, 不含FCS, 不含16)
    fcs_data = frame[1:apdu_end]
    rsp.fcs_calc = calc_fcs16(fcs_data)
    rsp.fcs_ok = (rsp.fcs_calc == rsp.fcs_recv)
    pos += 2

    # 9. 结束符
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

    # 类型化解析
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
    从字节流中提取完整的698帧.

    帧格式: 68 LL C SA CA HCS APDU FCS 16
    帧总长 = 1(68) + L + 1(16), 其中 L 从LL字段读取.
    """
    pos = 0
    while pos < len(data) - 5:  # 最少需要 68 LL(2) ... 16
        if data[pos] != FRAME_START:
            pos += 1
            continue

        # 读取长度域
        if pos + 3 > len(data):
            return None

        len_field = struct.unpack("<H", data[pos + 1:pos + 3])[0]
        l_value = len_field & 0x3FFF

        if l_value < 7:  # 最小: LL(2)+C(1)+SA(2)+CA(1)+HCS(2)=8, 再加FCS(2)=10... 至少7
            pos += 1
            continue

        # 帧总长度 = 1(68) + l_value + 1(16)
        total_len = 1 + l_value + 1

        if pos + total_len > len(data):
            return None

        # 验证结束符
        if data[pos + total_len - 1] != FRAME_END:
            pos += 1
            continue

        # 验证控制域后面的SA特征字节合理性
        # pos+3 = C, pos+4 = SA feature byte
        if pos + 4 < len(data):
            addr_feature = data[pos + 4]
            addr_byte_count = (addr_feature & 0x0F) + 1
            # SA总长 = 1(feature) + addr_byte_count
            sa_total = 1 + addr_byte_count
            # 检查: LL(2) + C(1) + SA + CA(1) + HCS(2) <= l_value
            min_header = 2 + 1 + sa_total + 1 + 2
            if min_header > l_value:
                pos += 1
                continue

        return data[pos:pos + total_len]

    return None
