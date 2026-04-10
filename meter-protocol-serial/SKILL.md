---
name: meter-protocol-serial
description: 698/645 电表协议串口发帧与解析 Skill，支持组帧、发送、接收、解析和断言验证，用于修bug后快速回归验证
triggers:
  - "698"
  - "645"
  - "DL/T698"
  - "DL/T645"
  - "OAD"
  - "DI"
  - "串口发帧"
  - "组帧"
  - "COM口"
  - "协议调试"
  - "回归测试"
---

# meter-protocol-serial

698/645 电表协议串口发帧与解析 Skill

## 触发时机

当用户需求涉及以下任一关键词时触发本 skill：
- `698`、`645`、`DL/T698`、`DL/T645`
- `OAD`、`DI`
- `串口发帧`、`组帧`、`COM口`
- `协议调试`、`回归测试`
- `发帧验证`、`读电表数据`、`写电表参数`

## 功能概述

本 skill 提供统一的 698/645 电表协议组帧、发送、接收和解析能力：

1. **只组帧模式**（无 port 参数）：输出组好的请求帧十六进制
2. **串口闭环模式**（有 port 参数）：发送请求、接收响应、解析结果

## 使用方法

### 快速调用

#### Linux / macOS / 原生Python

```bash
# 645读数据（只组帧）
python3 $SKILL_DIR/scripts/protocol_cli.py proto=645 op=read di=00010000

# 645读数据（串口发送）
python3 $SKILL_DIR/scripts/protocol_cli.py port=/dev/ttyUSB0 proto=645 op=read di=00010000

# 698读数据
python3 $SKILL_DIR/scripts/protocol_cli.py proto=698 op=read oad=40010200

# 698设置参数
python3 $SKILL_DIR/scripts/protocol_cli.py proto=698 op=set oad=43000300 value=bool:true
```

#### Windows / WSL (重要差异)

**WSL中使用Windows串口时，必须用 `python.exe` 而不是 `python3`：**

```bash
# WSL中访问Windows COM口（推荐方式：使用便利脚本）
$SKILL_DIR/meter-cmd.sh port=COM10 proto=645 op=read di=04000401

# 或者手动转换路径
SKILL_PATH=$(wslpath -w /home/xx/.agents/skills/meter-protocol-serial/scripts/protocol_cli.py)
python.exe "$SKILL_PATH" port=COM10 proto=645 op=read di=04000401
```

**常见错误：**
```bash
# 错误方式1（WSL Python无法访问Windows串口）
python3 protocol_cli.py port=COM10 ...  # 会报错: No such file or directory

# 错误方式2（Windows Python无法直接访问WSL路径）
python.exe /home/xx/.../protocol_cli.py  # 会报错: can't open file
```

**WSL串口映射关系：**
| Windows | WSL设备 |
|---------|---------|
| COM1 | /dev/ttyS1 |
| COM10 | /dev/ttyS10 |

**Windows原生PowerShell/CMD：**
```powershell
# Windows直接运行（PowerShell）
python.exe C:\path\to\scripts\protocol_cli.py port=COM10 proto=645 op=read di=04000401

# Windows直接运行（CMD）
python C:\path\to\scripts\protocol_cli.py port=COM10 proto=645 op=read di=04000401
```

#### 带断言的回归测试

```bash
# Linux/WSL通用（只组帧，无串口）
python3 $SKILL_DIR/scripts/protocol_cli.py proto=645 op=read di=00010000 expect=ack

# WSL+Windows串口（用python.exe）
python.exe $SKILL_DIR/scripts/protocol_cli.py port=COM3 proto=645 op=read di=00010000 expect=ack
```

### 支持的协议

| 协议 | 操作 | 说明 |
|------|------|------|
| DL/T645-2007 | read | 读数据 |
| DL/T645-2007 | write | 写数据 |
| DL/T698.45 | read | GET.request.normal |
| DL/T698.45 | set | SET.request.normal |

### 输入参数

#### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| proto | 协议类型 | 645 或 698 |
| op | 操作类型 | read / write / set |
| port | 串口（可选） | /dev/ttyUSB0 或 COM3 |
| timeout_ms | 超时时间 | 2000 |
| baud | 波特率 | 2400（645默认）、9600（698默认） |
| data_bits | 数据位 | 8 |
| parity | 校验位 | even / odd / none |
| stop_bits | 停止位 | 1 |
| expect | 断言条件 | ack / hex:0102 / bool:true / int:1 |
| decode_hint | 解码提示 | hex / ascii / uint16_le / uint32_le / bcd |
| note | 备注 | 任意文本 |

#### 645专用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| di | 数据标识（8位十六进制） | 00010000 |
| addr | 表地址（12位BCD） | 000000000001 |
| value | 写数据值 | hex:010203 / ascii:abc |
| fe_count | 前导FE个数 | 4 |
| raw_prefix | 前置数据 | hex:041234 |
| raw_suffix | 后置数据 | hex:0000 |

#### 698专用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| oad | 对象属性描述符（8位十六进制） | 40010200 |
| server_addr | 服务器地址 | 000000000000 |
| client_addr | 客户机地址 | 00 |
| ca | 客户机地址（缩写） | 00 |
| value | 写数据值 | bool:true / int32:123 / string:abc |

#### Value格式

**645协议：**
- `hex:01020304` - 原始十六进制数据
- `ascii:abc` - ASCII字符串

**698协议：**
- `bool:true|false` - 布尔值
- `int8:1`, `int16:1`, `int32:1` - 有符号整数
- `uint8:1`, `uint16:1`, `uint32:1` - 无符号整数
- `enum:1` - 枚举值
- `octet:112233` - 八位串（带长度前缀）
- `string:abc` - 可见字符串（带长度前缀）
- `hex:010203` - 原始十六进制（直接作为Data）

### 输出格式

```
MODE=frame_only|serial_roundtrip
PROTO=645|698
OP=read|write|set
TARGET=di:xxx|oad:xxx
REQUEST_HEX=68 AA AA ... CS 16
RESPONSE_HEX=68 BB BB ... CS 16  (串口模式)
FRAME_CHECK=ok|fail|partial
DECODE_STATUS=ok|partial|fail
RESULT=success|error|timeout
DATA_HEX=01020304
DATA_TYPED=typed_value  (如果有)
ASSERT_RESULT=pass|fail|skipped
ASSERT_REASON=...  (如果有)
SUMMARY=简短中文总结
```

#### 645特有输出

```
645_ADDR=000000000001
645_CTRL=91
645_DI=00010000
```

#### 698特有输出

```
698_SERVER_ADDR=000000000000
698_CLIENT_ADDR=00
698_PIID=00
698_OAD=40010200
698_DAR=00  (数据访问结果，00=成功)
```

### 退出码

| 码值 | 含义 |
|------|------|
| 0 | 成功 |
| 2 | 输入参数错误 |
| 3 | 串口打开或发送失败 |
| 4 | 超时无响应 |
| 5 | 收到响应但解析失败 |
| 6 | 断言失败 |

## AI 使用建议

### 回复顺序

当用户使用本 skill 时，AI 应按以下顺序回复：

1. **执行命令**：给出实际执行的 CLI 命令
2. **关键输出**：摘出 REQUEST_HEX、RESULT、ASSERT_RESULT 等关键字段
3. **简短解释**：说明结果含义和下一步建议

### 示例场景

**场景1：用户说"帮我组一个645读数据的帧"**

```
执行命令：
python3 $SKILL_DIR/scripts/protocol_cli.py proto=645 op=read di=00010000

输出：
MODE=frame_only
PROTO=645
OP=read
TARGET=di:00010000
REQUEST_HEX=FEFEFEFE6800000000000068110433333333AD16
...
SUMMARY=组帧成功: FEFEFEFE6800000000000068110433...
```

**场景2：用户说"验证COM3口能否读到数据"**

```
执行命令：
python3 $SKILL_DIR/scripts/protocol_cli.py port=COM3 proto=645 op=read di=00010000 expect=ack

输出：
MODE=serial_roundtrip
PROTO=645
OP=read
...
ASSERT_RESULT=pass
SUMMARY=断言通过: 收到响应
```

### 注意事项

1. **port 参数可选**：无 port 时进入只组帧模式，不会打开串口
2. **地址默认值**：645默认地址000000000000，698默认服务器地址AAAAAAAAAAAA（全AA通配地址）、客户机地址00
3. **波特率默认**：645默认2400bps，698默认9600bps
4. **超时处理**：默认超时2000ms，可通过timeout_ms调整
5. **断言失败**：assert_result=fail时进程返回非零退出码，可用于脚本自动化

## 模块结构

```
scripts/
├── protocol_cli.py      # CLI主入口
├── request_parser.py    # 请求解析
├── profiles.py          # 默认配置
├── serial_transport.py  # 串口收发
├── proto_645.py         # 645协议处理
├── proto_698.py         # 698协议处理
├── value_codec.py       # 值编解码
└── result_formatter.py  # 结果格式化
```

## 第一版限制

- 698：不支持登录、链路建立、安全认证、安全传输
- 698：不支持 ACTION 和 ROAD
- 645：不做各类业务DI的专用语义解析
- 两个协议：仅支持标准明文读写，不支持厂商私有扩展
