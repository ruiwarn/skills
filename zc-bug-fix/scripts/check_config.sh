#!/bin/bash
set -e

CONFIG_FILE="$(dirname "$0")/../.config"
EXAMPLE_FILE="$(dirname "$0")/../.config.example"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "MISSING_CONFIG"
    echo "请先创建配置文件: .claude/skills/bug-fix/.config"
    echo "可直接复制示例文件:"
    echo "cp .claude/skills/bug-fix/.config.example .claude/skills/bug-fix/.config"
    echo
    echo "示例内容:"
    cat "$EXAMPLE_FILE"
    exit 1
fi

# shellcheck source=/dev/null
source "$CONFIG_FILE"

missing=0
for key in ZENTAO_URL ZENTAO_ACCOUNT ZENTAO_PASSWORD GITLAB_URL GITLAB_TOKEN GITLAB_PROJECT_ID PROJECT_OWNER; do
    value="${!key}"
    if [[ -z "$value" ]]; then
        echo "MISSING_FIELD: $key"
        missing=1
    fi
done

if [[ $missing -ne 0 ]]; then
    exit 1
fi

echo "CONFIG_OK"
