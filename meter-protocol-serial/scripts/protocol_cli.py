#!/usr/bin/env python3
# protocol_cli.py
# 协议CLI主入口
# 处理命令行参数，协调各模块完成组帧、发送、解析和输出

import sys
import os

# 将脚本目录加入路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from request_parser import parse_request, validate_request, ParsedRequest
from profiles import get_profile_645, get_profile_698
from serial_transport import create_transport, SerialResult
from result_formatter import ExecutionResult, format_output, get_exit_code

import proto_645
import proto_698


def build_request(req: ParsedRequest) -> bytes:
    """根据请求构建协议帧"""
    if req.proto == "645":
        profile = get_profile_645()

        # 确定地址
        addr = req.addr if req.addr else profile.default_addr

        # 确定FE个数
        fe_count = req.fe_count if req.fe_count is not None else profile.fe_count

        # 确定DI
        di = req.di if req.di else "00010000"  # 默认读组合有功总电能

        # 构建请求
        if req.op == "read":
            return proto_645.encode_request(
                di=di,
                addr=addr,
                op="read",
                fe_count=fe_count
            )
        elif req.op == "write":
            return proto_645.encode_request(
                di=di,
                addr=addr,
                op="write",
                value=req.value,
                fe_count=fe_count,
                raw_prefix=req.raw_prefix,
                raw_suffix=req.raw_suffix
            )
        else:
            raise ValueError(f"645不支持的操作: {req.op}")

    elif req.proto == "698":
        profile = get_profile_698()

        # 确定地址
        server_addr = req.server_addr if req.server_addr else profile.default_server_addr
        # client_addr可以从多个来源获取
        if req.client_addr:
            client_addr = req.client_addr
        elif req.ca:
            client_addr = req.ca
        else:
            client_addr = profile.default_client_addr

        # 确定OAD
        oad = req.oad if req.oad else "00000000"

        # 转换操作类型
        op = req.op
        if op == "read":
            op = "read"
        elif op == "set":
            op = "set"

        # 构建请求
        return proto_698.encode_request(
            server_addr=server_addr,
            client_addr=client_addr,
            op=op,
            oad=oad,
            value=req.value
        )

    else:
        raise ValueError(f"不支持的协议: {req.proto}")


def parse_response(req: ParsedRequest, response: bytes) -> dict:
    """解析响应帧"""
    result = {}

    if req.proto == "645":
        rsp = proto_645.decode_response(response, req.decode_hint)

        result["frame_complete"] = rsp.frame_complete
        result["frame_valid"] = rsp.frame_valid
        result["addr"] = rsp.addr
        result["ctrl"] = f"{rsp.ctrl:02X}"
        result["di"] = rsp.di
        result["data_hex"] = rsp.payload.hex().upper() if rsp.payload else ""
        result["data_typed"] = rsp.payload_decoded if hasattr(rsp, 'payload_decoded') else None
        result["cs_ok"] = rsp.cs_ok
        result["error"] = rsp.error

    elif req.proto == "698":
        rsp = proto_698.parse_response(response, req.decode_hint)

        result["frame_complete"] = rsp.frame_complete
        result["frame_valid"] = rsp.frame_valid
        result["server_addr"] = rsp.server_addr
        result["client_addr"] = rsp.client_addr
        result["piid"] = f"{rsp.piid:02X}"
        result["oad"] = rsp.oad
        result["dar"] = rsp.dar
        result["data_hex"] = rsp.data.hex().upper() if rsp.data else ""
        result["data_typed"] = rsp.data_typed
        result["hcs_ok"] = rsp.hcs_ok
        result["fcs_ok"] = rsp.fcs_ok
        result["error"] = rsp.error

    return result


def check_expect(expect: str, data_hex: str, data_typed) -> tuple:
    """
    检查期望结果
    返回: (assert_result, assert_reason)
    """
    if not expect:
        return "skipped", ""

    try:
        if expect == "ack":
            # 只要有响应就算成功
            return "pass", "收到响应"

        elif expect.startswith("hex:"):
            expected_hex = expect[4:].replace(" ", "").upper()
            actual_hex = data_hex.replace(" ", "")
            if expected_hex == actual_hex:
                return "pass", f"数据匹配: {expected_hex}"
            else:
                return "fail", f"期望: {expected_hex}, 实际: {actual_hex}"

        elif expect.startswith("bool:"):
            val = expect[5:].lower().strip()
            expected_bool = val in ("true", "1", "yes", "on")

            if isinstance(data_typed, bool):
                actual_bool = data_typed
            elif data_hex == "01":
                actual_bool = True
            elif data_hex == "00":
                actual_bool = False
            else:
                return "fail", f"无法判断布尔值: {data_hex}"

            if expected_bool == actual_bool:
                return "pass", f"布尔值匹配: {actual_bool}"
            else:
                return "fail", f"期望: {expected_bool}, 实际: {actual_bool}"

        elif expect.startswith("int:"):
            expected_int = int(expect[4:])

            if isinstance(data_typed, int):
                actual_int = data_typed
            else:
                try:
                    actual_int = int(data_hex, 16)
                except ValueError:
                    return "fail", f"无法转换为整数: {data_hex}"

            if expected_int == actual_int:
                return "pass", f"整数值匹配: {actual_int}"
            else:
                return "fail", f"期望: {expected_int}, 实际: {actual_int}"

        else:
            return "fail", f"未知的expect格式: {expect}"

    except Exception as e:
        return "fail", f"断言检查异常: {e}"


def main():
    """主函数"""
    # 解析命令行参数
    args = sys.argv[1:]

    if not args:
        print("ERROR=缺少参数", file=sys.stderr)
        print("USAGE: protocol_cli.py proto=645 op=read di=00010000 [port=COM1]", file=sys.stderr)
        sys.exit(2)

    # 显示帮助
    if "-h" in args or "--help" in args or "help" in args:
        print("""698/645 电表协议串口工具

用法: protocol_cli.py [参数...]

通用参数:
  proto=645|698         协议类型
  op=read|write|set     操作类型
  port=COMx             串口(可选，省略则只组帧)
  timeout_ms=2000       超时时间(毫秒)
  baud=9600             波特率
  data_bits=8           数据位
  parity=even           校验位(even/odd/none)
  stop_bits=1           停止位
  expect=hex:0102       期望结果断言
  decode_hint=hex       解码提示
  note=...              备注

645专用:
  di=00010000           数据标识(8位十六进制)
  addr=AAAAAAAAAAAA     表地址(12位BCD)
  value=hex:0102        写数据值
  fe_count=4            前导FE个数
  raw_prefix=hex:...    前置数据
  raw_suffix=hex:...    后置数据

698专用:
  oad=40010200          对象属性描述符(8位十六进制)
  server_addr=...       服务器地址
  client_addr=00        客户机地址
  ca=00                 客户机地址(缩写)
  value=bool:true       写数据值

value格式:
  645: hex:010203, ascii:abc
  698: bool:true, int8:1, int16:1, int32:1, uint8:1, uint16:1, uint32:1,
       enum:1, octet:1122, string:abc, hex:010203
""", file=sys.stderr)
        sys.exit(0)

    try:
        req = parse_request(args)
    except ValueError as e:
        print(f"ERROR=参数解析错误: {e}", file=sys.stderr)
        sys.exit(2)

    # 验证请求
    errors = validate_request(req)
    if errors:
        for err in errors:
            print(f"ERROR={err}", file=sys.stderr)
        sys.exit(2)

    # 创建结果对象
    result = ExecutionResult()
    result.proto = req.proto
    result.op = req.op
    result.target = f"{('di' if req.proto == '645' else 'oad')}:{req.di if req.proto == '645' else req.oad}"

    # 构建请求帧
    try:
        request_frame = build_request(req)
        result.request_hex = request_frame.hex().upper()
    except ValueError as e:
        print(f"ERROR=组帧失败: {e}", file=sys.stderr)
        sys.exit(2)

    # 判断模式
    if req.port:
        result.mode = "serial_roundtrip"
    else:
        result.mode = "frame_only"
        result.summary = f"组帧成功: {result.request_hex[:32]}..." if len(result.request_hex) > 32 else f"组帧成功: {result.request_hex}"
        print(format_output(result))
        sys.exit(0)

    # 串口模式
    transport = create_transport(
        baud=req.baud,
        data_bits=req.data_bits,
        parity=req.parity,
        stop_bits=req.stop_bits,
        timeout_ms=req.timeout_ms,
        proto=req.proto
    )

    # 打开串口
    if not transport.open(req.port):
        result.result = "error"
        result.error = f"无法打开串口: {req.port}"
        result.summary = "串口打开失败"
        print(format_output(result))
        sys.exit(3)

    # 确定帧查找函数
    if req.proto == "645":
        find_frame = proto_645.find_complete_frame
    else:
        find_frame = proto_698.find_complete_frame

    # 发送和接收
    try:
        serial_result = transport.send_and_receive(request_frame, find_frame)
    finally:
        transport.close()

    # 处理结果
    if not serial_result.success:
        if serial_result.timeout_occurred:
            result.result = "timeout"
            result.error = "接收超时"
            result.summary = "等待响应超时"
            if serial_result.response_received:
                result.response_hex = serial_result.response_received.hex().upper()
                result.frame_check = "partial"
        else:
            result.result = "error"
            result.error = serial_result.error
            result.summary = f"通信失败: {serial_result.error}"
        print(format_output(result))
        sys.exit(get_exit_code(result))

    # 成功收到响应
    result.response_hex = serial_result.response_received.hex().upper()

    # 解析响应
    try:
        parsed = parse_response(req, serial_result.response_received)
    except Exception as e:
        result.result = "error"
        result.frame_check = "fail"
        result.decode_status = "fail"
        result.error = f"解析响应失败: {e}"
        result.summary = "响应解析失败"
        print(format_output(result))
        sys.exit(5)

    # 填充解析结果
    result.frame_check = "ok" if parsed.get("frame_valid") else "fail"
    result.decode_status = "ok" if not parsed.get("error") else "partial" if parsed.get("frame_complete") else "fail"
    result.data_hex = parsed.get("data_hex", "")
    result.data_typed = parsed.get("data_typed")

    # 如果帧校验失败，设置为错误状态
    if not parsed.get("frame_valid"):
        result.result = "error"
        result.error = parsed.get("error", "帧校验失败")

    if req.proto == "645":
        result.addr_645 = parsed.get("addr", "")
        result.ctrl_645 = parsed.get("ctrl", "")
        result.di_645 = parsed.get("di", "")

    elif req.proto == "698":
        result.server_addr_698 = parsed.get("server_addr", "")
        result.client_addr_698 = parsed.get("client_addr", "")
        result.piid_698 = parsed.get("piid", "")
        result.oad_698 = parsed.get("oad", "")
        result.dar_698 = parsed.get("dar")

    # 检查断言
    if req.expect:
        assert_result, assert_reason = check_expect(req.expect, result.data_hex, result.data_typed)
        result.assert_result = assert_result
        result.assert_reason = assert_reason

    # 生成摘要
    if result.assert_result == "pass":
        result.summary = f"断言通过: {result.assert_reason}"
    elif result.assert_result == "fail":
        result.summary = f"断言失败: {result.assert_reason}"
    elif result.frame_check == "fail":
        result.summary = f"帧校验失败: {result.error}"
    elif result.decode_status == "ok":
        if result.data_typed is not None:
            result.summary = f"通信成功，数据: {result.data_typed}"
        else:
            result.summary = f"通信成功，数据: {result.data_hex[:32]}..." if len(result.data_hex) > 32 else f"通信成功，数据: {result.data_hex}"
    else:
        result.summary = f"通信完成，解析状态: {result.decode_status}"

    # 输出结果
    print(format_output(result))

    # 返回退出码
    sys.exit(get_exit_code(result))


if __name__ == "__main__":
    main()
