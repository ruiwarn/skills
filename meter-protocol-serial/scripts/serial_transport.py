# serial_transport.py
# 串口传输模块
# 负责串口的打开、发送、接收和帧完整性判定

import time
import sys
from typing import Optional, Callable, Tuple
from dataclasses import dataclass

from profiles import SerialConfig, parse_parity, parse_stop_bits


@dataclass
class SerialResult:
    """串口操作结果"""
    success: bool
    request_sent: bytes = b""
    response_received: bytes = b""
    error: str = ""
    timeout_occurred: bool = False


def parity_to_pyserial(parity: str) -> str:
    """将内部校验位表示转为pyserial格式"""
    p = parity.lower()
    if p in ("even", "偶"):
        return "E"
    elif p in ("odd", "奇"):
        return "O"
    elif p in ("none", "无"):
        return "N"
    return "E"


def stop_bits_to_pyserial(stop_bits: int) -> float:
    """将停止位转为pyserial格式"""
    if stop_bits == 1:
        return 1
    elif stop_bits == 2:
        return 2
    return 1


class SerialTransport:
    """串口传输类"""

    def __init__(self, config: SerialConfig):
        self.config = config
        self.serial = None

    def open(self, port: str) -> bool:
        """打开串口"""
        try:
            import serial

            self.serial = serial.Serial(
                port=port,
                baudrate=self.config.baud,
                bytesize=self.config.data_bits,
                parity=parity_to_pyserial(self.config.parity),
                stopbits=stop_bits_to_pyserial(self.config.stop_bits),
                timeout=self.config.timeout_ms / 1000.0,
                write_timeout=self.config.timeout_ms / 1000.0
            )
            return True
        except ImportError:
            # 尝试用pyserial的替代方法
            try:
                # 某些环境下可能需要用其他方式
                import serial
                self.serial = serial.Serial()
                self.serial.port = port
                self.serial.baudrate = self.config.baud
                self.serial.bytesize = self.config.data_bits
                self.serial.parity = parity_to_pyserial(self.config.parity)
                self.serial.stopbits = stop_bits_to_pyserial(self.config.stop_bits)
                self.serial.timeout = self.config.timeout_ms / 1000.0
                self.serial.write_timeout = self.config.timeout_ms / 1000.0
                self.serial.open()
                return True
            except Exception as e:
                print(f"ERROR=串口打开失败: {e}", file=sys.stderr)
                return False
        except Exception as e:
            print(f"ERROR=串口打开失败: {e}", file=sys.stderr)
            return False

    def close(self):
        """关闭串口"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.close()
            except Exception:
                pass

    def send_and_receive(self, data: bytes, find_frame: Callable[[bytes], Optional[bytes]]) -> SerialResult:
        """
        发送数据并接收响应

        参数:
            data: 要发送的数据
            find_frame: 从接收缓冲区提取完整帧的函数

        返回:
            SerialResult对象
        """
        result = SerialResult(success=False)
        result.request_sent = data

        if not self.serial or not self.serial.is_open:
            result.error = "串口未打开"
            return result

        try:
            # 清空缓冲区
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()

            # 发送数据
            bytes_written = self.serial.write(data)
            if bytes_written != len(data):
                result.error = f"发送不完整，期望{len(data)}字节，实际发送{bytes_written}字节"
                return result

            self.serial.flush()

            # 等待并接收响应
            # 策略: 循环读取直到找到完整帧或超时
            response_buffer = b""
            start_time = time.time()
            timeout_sec = self.config.timeout_ms / 1000.0

            while True:
                elapsed = time.time() - start_time
                if elapsed > timeout_sec:
                    result.timeout_occurred = True
                    result.error = "接收超时"
                    # 保留已收到的部分数据
                    result.response_received = response_buffer
                    break

                # 读取可用数据
                available = self.serial.in_waiting
                if available > 0:
                    chunk = self.serial.read(available)
                    response_buffer += chunk

                    # 尝试找到完整帧
                    frame = find_frame(response_buffer)
                    if frame:
                        result.success = True
                        result.response_received = frame
                        return result

                    # 防止缓冲区无限增长
                    max_buffer_size = 4096
                    if len(response_buffer) > max_buffer_size:
                        response_buffer = response_buffer[-max_buffer_size:]

                # 短暂等待更多数据
                time.sleep(0.01)

                # 如果超时且收到一些数据但没有完整帧
                if result.timeout_occurred and response_buffer:
                    result.response_received = response_buffer

            return result

        except Exception as e:
            result.error = f"串口通信异常: {e}"
            return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_transport(baud: Optional[int] = None,
                    data_bits: Optional[int] = None,
                    parity: Optional[str] = None,
                    stop_bits: Optional[int] = None,
                    timeout_ms: Optional[int] = None,
                    proto: str = "645") -> SerialTransport:
    """
    创建串口传输实例，使用默认配置并允许覆盖

    参数:
        proto: 协议类型，用于选择默认配置
    """
    from profiles import get_profile_645, get_profile_698

    if proto == "645":
        profile = get_profile_645()
    else:
        profile = get_profile_698()

    config = SerialConfig(
        baud=baud if baud is not None else profile.serial.baud,
        data_bits=data_bits if data_bits is not None else profile.serial.data_bits,
        parity=parity if parity is not None else profile.serial.parity,
        stop_bits=stop_bits if stop_bits is not None else profile.serial.stop_bits,
        timeout_ms=timeout_ms if timeout_ms is not None else profile.serial.timeout_ms
    )

    return SerialTransport(config)
