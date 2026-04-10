#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一维护 zc-bug-fix 的配置命名，避免多个脚本各自硬编码路径。
"""

import os
import subprocess
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────
CONFIG_NAME = "zc-bug-fix.config"
EXAMPLE_NAME = "zc-bug-fix.config.example"

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
EXAMPLE_FILE = SKILL_ROOT / EXAMPLE_NAME


def get_project_root() -> str:
    """优先按 Git 仓库根目录定位项目配置；非 Git 目录下退化为当前工作目录。"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.getcwd()


def get_preferred_config_path() -> str:
    """
    环境变量允许用户为当前项目显式指定其它配置文件，相对路径按项目根目录解释。

    如果 ZC_BUG_FIX_CONFIG 环境变量已设置：
      - 绝对路径：直接返回
      - 相对路径：相对于项目根目录解析
    否则：返回 项目根目录 / CONFIG_NAME
    """
    project_root = get_project_root()
    env_config = os.environ.get("ZC_BUG_FIX_CONFIG", "")

    if env_config:
        if os.path.isabs(env_config):
            return env_config
        return str(Path(project_root) / env_config)

    return str(Path(project_root) / CONFIG_NAME)


def get_effective_config_path() -> tuple[str, bool]:
    """
    只读取项目级配置；显式覆盖时也只接受用户指定的那一份文件。

    Returns:
        (path, exists) — path 为首选配置路径，exists 表示该文件是否存在。
    """
    preferred = get_preferred_config_path()
    return preferred, os.path.isfile(preferred)


def get_example_path() -> str:
    """示例文件固定使用可被 skills add 带上的非隐藏文件。"""
    return str(EXAMPLE_FILE)
