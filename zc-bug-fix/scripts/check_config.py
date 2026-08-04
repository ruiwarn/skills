#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
校验 zc-bug-fix 配置文件是否存在且包含所有必填字段。
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

from config_paths import get_effective_config_path, get_example_path, get_preferred_config_path

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


def load_config(config_path: str) -> Dict[str, str]:
    """
    加载 shell 风格的 KEY=VALUE 配置文件。
    以 # 开头的行视为注释，空行跳过。
    返回键值对字典。
    """
    config = {}  # type: Dict[str, str]
    path = Path(config_path)

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        # 跳过空行和注释
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        config[key.strip()] = value.strip()

    return config


def check_config() -> Tuple[str, List[str]]:
    """
    检查配置文件是否存在并包含所有必填字段。

    Returns:
        ("CONFIG_OK", [])                          — 配置有效
        ("MISSING_CONFIG", [提示信息1, 提示信息2, …]) — 配置文件不存在
        ("MISSING_FIELD", ["MISSING_FIELD: KEY1", …]) — 缺少必填字段
    """
    config_path, exists = get_effective_config_path()
    preferred_path = get_preferred_config_path()
    example_path = get_example_path()

    # ── 配置文件不存在 ────────────────────────────────────────────
    if not exists:
        # 缺少配置时统一提示项目级路径，避免继续把敏感信息写回 skill 安装目录。
        messages = [
            f"请先创建配置文件: {preferred_path}",
            "可直接复制示例文件:",
            f"cp {example_path} {preferred_path}",
            "",
            "示例内容:",
        ]
        # 追加示例文件内容
        try:
            example_content = Path(example_path).read_text(encoding="utf-8")
            messages.append(example_content)
        except FileNotFoundError:
            messages.append(f"(示例文件不存在: {example_path})")

        return "MISSING_CONFIG", messages

    # ── 加载并校验必填字段 ────────────────────────────────────────
    config = load_config(config_path)
    missing = []  # type: List[str]

    for key in REQUIRED_FIELDS:
        if not config.get(key):
            missing.append(f"MISSING_FIELD: {key}")

    if missing:
        return "MISSING_FIELD", missing

    return "CONFIG_OK", []


# ── 命令行入口 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    status, messages = check_config()
    print(status)
    for msg in messages:
        print(msg)
    sys.exit(0 if status == "CONFIG_OK" else 1)
