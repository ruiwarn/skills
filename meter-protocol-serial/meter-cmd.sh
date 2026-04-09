#!/bin/bash
# WSL便利脚本：自动处理路径转换和python.exe调用

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI_PATH=$(wslpath -w "$SCRIPT_DIR/scripts/protocol_cli.py")

# 将所有参数传递给Windows Python
python.exe "$CLI_PATH" "$@"
