# result_formatter.py
# 结果格式化模块
# 统一输出格式，方便AI和脚本二次解析

import sys
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ExecutionResult:
    """执行结果数据结构"""
    # 模式信息
    mode: str = "frame_only"  # frame_only 或 serial_roundtrip

    # 协议信息
    proto: str = ""  # 645 或 698
    op: str = ""  # read, write, set
    target: str = ""  # di:xxx 或 oad:xxx

    # 帧数据
    request_hex: str = ""  # 请求帧十六进制
    response_hex: str = ""  # 响应帧十六进制(如果有)

    # 校验状态
    frame_check: str = "ok"  # ok, fail, partial
    decode_status: str = "ok"  # ok, partial, fail
    result: str = "success"  # success, error, timeout

    # 解析后的数据
    data_hex: str = ""  # 数据区十六进制
    data_typed: Any = None  # 类型化数据(如果有)

    # 645特有字段
    addr_645: str = ""  # 645地址
    ctrl_645: str = ""  # 645控制码
    di_645: str = ""  # 645数据标识

    # 698特有字段
    server_addr_698: str = ""  # 698服务器地址
    client_addr_698: str = ""  # 698客户机地址
    piid_698: str = ""  # PIID
    oad_698: str = ""  # OAD
    dar_698: Optional[int] = None  # DAR

    # 断言结果
    assert_result: str = "skipped"  # pass, fail, skipped
    assert_reason: str = ""  # 断言结果说明

    # 错误信息
    error: str = ""  # 错误描述

    # 摘要
    summary: str = ""  # 简短中文摘要

    # 原始参数字典(用于调试)
    raw_params: Dict[str, str] = field(default_factory=dict)


def format_output(result: ExecutionResult, output_format: str = "text") -> str:
    """
    格式化输出结果
    支持格式: text (KEY=VALUE格式)
    """
    if output_format != "text":
        raise ValueError(f"不支持的输出格式: {output_format}")

    lines = []

    # 模式
    lines.append(f"MODE={result.mode}")

    # 协议信息
    lines.append(f"PROTO={result.proto}")
    lines.append(f"OP={result.op}")
    if result.target:
        lines.append(f"TARGET={result.target}")

    # 帧数据
    lines.append(f"REQUEST_HEX={result.request_hex}")
    if result.response_hex:
        lines.append(f"RESPONSE_HEX={result.response_hex}")

    # 状态
    lines.append(f"FRAME_CHECK={result.frame_check}")
    lines.append(f"DECODE_STATUS={result.decode_status}")
    lines.append(f"RESULT={result.result}")

    # 645特有
    if result.proto == "645":
        if result.addr_645:
            lines.append(f"645_ADDR={result.addr_645}")
        if result.ctrl_645:
            lines.append(f"645_CTRL={result.ctrl_645}")
        if result.di_645:
            lines.append(f"645_DI={result.di_645}")

    # 698特有
    if result.proto == "698":
        if result.server_addr_698:
            lines.append(f"698_SERVER_ADDR={result.server_addr_698}")
        if result.client_addr_698:
            lines.append(f"698_CLIENT_ADDR={result.client_addr_698}")
        if result.piid_698:
            lines.append(f"698_PIID={result.piid_698}")
        if result.oad_698:
            lines.append(f"698_OAD={result.oad_698}")
        if result.dar_698 is not None:
            lines.append(f"698_DAR={result.dar_698:02X}")

    # 数据
    if result.data_hex:
        lines.append(f"DATA_HEX={result.data_hex}")
    if result.data_typed is not None:
        lines.append(f"DATA_TYPED={result.data_typed}")

    # 断言
    lines.append(f"ASSERT_RESULT={result.assert_result}")
    if result.assert_reason:
        lines.append(f"ASSERT_REASON={result.assert_reason}")

    # 错误
    if result.error:
        lines.append(f"ERROR={result.error}")

    # 摘要
    lines.append(f"SUMMARY={result.summary}")

    return "\n".join(lines)


def print_result(result: ExecutionResult, file=sys.stdout):
    """打印结果到指定输出"""
    output = format_output(result)
    print(output, file=file)


def get_exit_code(result: ExecutionResult) -> int:
    """
    根据执行结果获取进程退出码
    0: 成功
    2: 输入参数错误
    3: 串口打开或发送失败
    4: 超时无响应
    5: 收到响应但解析失败
    6: 断言失败
    """
    if result.result == "error":
        if "参数" in result.error:
            return 2
        elif "串口" in result.error or "发送" in result.error:
            return 3
        elif "解析" in result.error:
            return 5
        else:
            return 1

    if result.result == "timeout":
        return 4

    if result.assert_result == "fail":
        return 6

    return 0
