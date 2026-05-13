#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 zc-bug-fix 配置文件是否存在且包含所有必填字段。"""

import sys
from pathlib import Path

from config_paths import (
    get_effective_config_path,
    get_effective_config_paths,
    get_example_path,
    get_preferred_config_path,
    SYSTEM_DEFAULTS,
)

# ── 必填字段 ──────────────────────────────────────────────────────────
REQUIRED_FIELDS = [
    "ZENTAO_URL",
    "ZENTAO_ACCOUNT",
    "ZENTAO_PASSWORD",
    "GITLAB_URL",
    "GITLAB_TOKEN",
    "GITLAB_PROJECT_ID",
    "PROJECT_OWNER",
]


def load_config_file(config_path: str) -> dict:
    """加载单个 shell 风格的 KEY=VALUE 配置文件。以 # 开头的行视为注释，空行跳过。"""
    config: dict[str, str] = {}
    path = Path(config_path)
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        config[key.strip()] = value.strip()
    return config


def load_config(config_path: str) -> dict:
    """向后兼容接口：加载单个配置文件。"""
    return load_config_file(config_path)


def load_effective_config() -> dict:
    """按分层优先级加载所有配置文件，合并为一个字典。后加载的同名键覆盖前面的值。

    优先级从低到高：
      SYSTEM_DEFAULTS -> /etc/zc-bug-fix/system.env -> <project>/zc-bug-fix.config
      -> ~/.config/zc-bug-fix/global.env -> ~/.config/zc-bug-fix/secrets.env
      -> <project>/.claude/zc-bug-fix.project.env -> ZC_BUG_FIX_CONFIG (if set)
    """
    merged: dict[str, str] = dict(SYSTEM_DEFAULTS)

    for path in get_effective_config_paths():
        try:
            layer = load_config_file(path)
            merged.update(layer)
        except (OSError, UnicodeDecodeError):
            pass  # silently skip unreadable layers

    return merged


def check_config() -> tuple[str, list[str]]:
    """检查配置是否完整（通过分层加载合并后验证必填字段）。

    Returns:
        ("CONFIG_OK", [])                             -- 配置有效
        ("MISSING_CONFIG", [hint1, ...])              -- 没有找到任何配置文件
        ("MISSING_FIELD", ["MISSING_FIELD: KEY1"...]) -- 缺少必填字段
    """
    searched_paths = get_effective_config_paths()
    preferred_path = get_preferred_config_path()
    example_path = get_example_path()

    if not searched_paths:
        messages = [
            f"请先创建配置文件: {preferred_path}",
            "可直接复制示例文件:",
            f"cp {example_path} {preferred_path}",
            "",
            "示例内容:",
        ]
        try:
            example_content = Path(example_path).read_text(encoding="utf-8")
            messages.append(example_content)
        except FileNotFoundError:
            messages.append(f"(示例文件不存在: {example_path})")
        return "MISSING_CONFIG", messages

    config = load_effective_config()
    missing: list[str] = []
    for key in REQUIRED_FIELDS:
        if not config.get(key):
            missing.append(f"MISSING_FIELD: {key}")

    if missing:
        return "MISSING_FIELD", missing

    return "CONFIG_OK", []


if __name__ == "__main__":
    status, messages = check_config()
    print(status)
    for msg in messages:
        print(msg)
    sys.exit(0 if status == "CONFIG_OK" else 1)
