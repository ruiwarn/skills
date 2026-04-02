#!/bin/bash
set -e

# shellcheck source=/dev/null
source "$(cd "$(dirname "$0")" && pwd)/config_paths.sh"

CONFIG_FILE="$(zc_bug_fix_get_effective_config_path)" || true
PREFERRED_CONFIG_FILE="$(zc_bug_fix_get_preferred_config_path)"
EXAMPLE_FILE="$(zc_bug_fix_get_example_path)"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "MISSING_CONFIG"
    # 缺少配置时统一提示项目级路径，避免继续把敏感信息写回 skill 安装目录。
    echo "请先创建配置文件: ${PREFERRED_CONFIG_FILE}"
    echo "可直接复制示例文件:"
    echo "cp ${EXAMPLE_FILE} ${PREFERRED_CONFIG_FILE}"
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
