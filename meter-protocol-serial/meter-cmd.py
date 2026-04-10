#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WSL/Windows convenience wrapper for protocol_cli.py.

在 WSL 下自动把 `protocol_cli.py` 转成 Windows 路径并交给 `python.exe`，
避免直接用 shell 包装脚本带来的环境兼容问题。非 WSL 环境下会退化为使用当前
Python 解释器执行本地路径，便于本地测试和统一调用方式。
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence


def resolve_script_dir() -> Path:
    """返回包装脚本所在目录。"""
    return Path(__file__).resolve().parent


def resolve_cli_path() -> Path:
    """返回 protocol_cli.py 的绝对路径。"""
    return resolve_script_dir() / "scripts" / "protocol_cli.py"


def is_wsl(environ: Mapping[str, str] | None = None) -> bool:
    """判断当前是否运行在 WSL 环境。"""
    env = os.environ if environ is None else environ
    if env.get("WSL_INTEROP") or env.get("WSL_DISTRO_NAME"):
        return True
    return "microsoft" in platform.release().lower()


def to_windows_path(path: Path) -> str:
    """把 WSL 路径转换成 Windows 路径。"""
    result = subprocess.run(
        ["wslpath", "-w", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def build_command(argv: Sequence[str], environ: Mapping[str, str] | None = None) -> list[str]:
    """构造最终要执行的命令。"""
    env = os.environ if environ is None else environ
    cli_path = resolve_cli_path()
    if not cli_path.is_file():
        raise RuntimeError(f"找不到 protocol_cli.py: {cli_path}")

    windows_mode = is_wsl(env)
    interpreter = env.get("METER_CMD_PYTHON")
    if not interpreter:
        interpreter = "python.exe" if windows_mode else (sys.executable or "python3")

    target_path = to_windows_path(cli_path) if windows_mode else str(cli_path)
    return [interpreter, target_path, *argv]


def main(argv: Sequence[str] | None = None) -> int:
    """执行包装命令并返回子进程退出码。"""
    args = list(sys.argv[1:] if argv is None else argv)

    try:
        command = build_command(args)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR=wslpath 路径转换失败: {exc}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 2

    try:
        completed = subprocess.run(command)
    except FileNotFoundError as exc:
        print(f"ERROR=找不到解释器: {command[0]} ({exc})", file=sys.stderr)
        return 3

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
