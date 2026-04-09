# profiles.py
# 默认配置管理模块
# 存放所有协议相关的默认配置，避免硬编码分散在各处

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SerialConfig:
    """串口配置数据类"""
    baud: int = 2400
    data_bits: int = 8
    parity: str = "even"  # even, odd, none
    stop_bits: int = 1
    timeout_ms: int = 2000


@dataclass
class Profile645:
    """DL/T645-2007 协议默认配置"""
    # 默认地址: 12位BCD码，这里是"000000000000"
    default_addr: str = "000000000000"
    # 前导FE个数
    fe_count: int = 4
    # 串口配置
    serial: SerialConfig = field(default_factory=lambda: SerialConfig(
        baud=2400,
        data_bits=8,
        parity="even",
        stop_bits=1,
        timeout_ms=2000
    ))


@dataclass
class Profile698:
    """DL/T698.45 协议默认配置"""
    # 服务器地址(逻辑地址+物理地址)
    default_server_addr: str = "000000000000"
    # 客户机地址
    default_client_addr: str = "00"
    # 客户机地址(CA)缩写形式
    default_ca: str = "00"
    # 串口配置 (698常用9600bps)
    serial: SerialConfig = field(default_factory=lambda: SerialConfig(
        baud=9600,
        data_bits=8,
        parity="even",
        stop_bits=1,
        timeout_ms=2000
    ))


# 全局单例配置实例
PROFILE_645 = Profile645()
PROFILE_698 = Profile698()


def get_profile_645() -> Profile645:
    """获取645协议默认配置"""
    return PROFILE_645


def get_profile_698() -> Profile698:
    """获取698协议默认配置"""
    return PROFILE_698


def parse_parity(parity_str: str) -> str:
    """解析校验位字符串为标准格式"""
    p = parity_str.lower()
    if p in ("even", "e", "偶"):
        return "even"
    elif p in ("odd", "o", "奇"):
        return "odd"
    elif p in ("none", "n", "无"):
        return "none"
    return "even"


def parse_stop_bits(stop_str: str) -> int:
    """解析停止位字符串为整数"""
    try:
        val = float(stop_str)
        if val in (1, 1.5, 2):
            return int(val) if val != 1.5 else 1
    except ValueError:
        pass
    return 1
