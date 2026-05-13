#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一维护 zc-bug-fix 的配置命名，避免多个脚本各自硬编码路径。"""

import os
import subprocess
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────
CONFIG_NAME = "zc-bug-fix.config"
EXAMPLE_NAME = "zc-bug-fix.config.example"

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
EXAMPLE_FILE = SKILL_ROOT / EXAMPLE_NAME

# System-level config (lowest precedence)
SYSTEM_CONFIG_PATH = Path("/etc/zc-bug-fix/system.env")

# Defaults baked in code (very lowest precedence, always available)
SYSTEM_DEFAULTS: dict[str, str] = {
    "TARGET_BRANCH": "develop",
}


def get_project_root() -> str:
    """优先按 Git 仓库根目录定位项目配置；非 Git 目录下退化为当前工作目录。"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return os.getcwd()


def get_user_config_dir() -> Path:
    """返回用户级配置目录 (~/.config/zc-bug-fix/)。"""
    return Path.home() / ".config" / "zc-bug-fix"


def get_preferred_config_path() -> str:
    """
    返回主要配置路径（用于错误提示和向后兼容）。
    ZC_BUG_FIX_CONFIG 绝对路径直接返回；相对路径相对于项目根目录解析。
    否则返回 <项目根目录>/zc-bug-fix.config。
    """
    project_root = get_project_root()
    env_config = os.environ.get("ZC_BUG_FIX_CONFIG", "")

    if env_config:
        if os.path.isabs(env_config):
            return env_config
        return str(Path(project_root) / env_config)

    return str(Path(project_root) / CONFIG_NAME)


def get_default_config_candidates() -> list[str]:
    """
    返回按优先级从低到高排列的默认配置文件路径列表。
    调用者应从头到尾依次加载，后加载的键覆盖前面的同名键。

    层级（低 → 高）:
      1. /etc/zc-bug-fix/system.env          — 系统级
      2. <project_root>/zc-bug-fix.config    — 项目根（向后兼容）
      3. ~/.config/zc-bug-fix/global.env     — 用户级通用
      4. ~/.config/zc-bug-fix/secrets.env    — 用户级密钥
      5. <project_root>/.claude/zc-bug-fix.project.env  — 项
    """
    project_root = get_project_root()
    user_dir = get_user_config_dir()

    return [
        str(SYSTEM_CONFIG_PATH),
        str(Path(project_root) / CONFIG_NAME),
        str(user_dir / "global.env"),
        str(user_dir / "secrets.env"),
        str(Path(project_root) / ".claude" / "zc-bug-fix.project.env"),
    ]


def get_effective_config_paths() -> list[str]:
    """
    返回按优先级从低到高排列的所有有效配置文件路径列表（只包含实际存在的文件）。
    如果设置了 ZC_BUG_FIX_CONFIG 环境变量，它作为最高优先级的覆盖层追加到列表末尾。
    """
    candidates = get_default_config_candidates()

    env_config = os.environ.get("ZC_BUG_FIX_CONFIG", "")
    if env_config:
        project_root = get_project_root()
        if os.path.isabs(env_config):
            override_path = env_config
        else:
            override_path = str(Path(project_root) / env_config)
        if override_path not in candidates:
            candidates.append(override_path)

    return [p for p in candidates if os.path.isfile(p)]


def get_effective_config_path() -> tuple[str, bool]:
    """
    向后兼容接口：返回 (主配置路径, 是否存在)。
    主配置路径 = get_preferred_config_path() 所指向的路径。
    """
    preferred = get_preferred_config_path()
    return preferred, os.path.isfile(preferred)


def get_example_path() -> str:
    """示例文件固定使用可被 skills add 带上的非隐藏文件。"""
    return str(EXAMPLE_FILE)
