#!/bin/bash

# 统一维护 zc-bug-fix 的配置命名，避免多个脚本各自硬编码路径。
ZC_BUG_FIX_CONFIG_NAME="zc-bug-fix.config"
ZC_BUG_FIX_EXAMPLE_NAME="zc-bug-fix.config.example"

ZC_BUG_FIX_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZC_BUG_FIX_SKILL_ROOT="$(cd "${ZC_BUG_FIX_SCRIPT_DIR}/.." && pwd)"
ZC_BUG_FIX_EXAMPLE_FILE="${ZC_BUG_FIX_SKILL_ROOT}/${ZC_BUG_FIX_EXAMPLE_NAME}"

# 优先按 Git 仓库根目录定位项目配置；非 Git 目录下退化为当前工作目录。
zc_bug_fix_get_project_root() {
    local project_root

    if project_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
        printf '%s\n' "$project_root"
        return 0
    fi

    pwd
}

# 环境变量允许用户为当前项目显式指定其它配置文件，相对路径按项目根目录解释。
zc_bug_fix_get_preferred_config_path() {
    local project_root

    project_root="$(zc_bug_fix_get_project_root)"
    if [[ -n "${ZC_BUG_FIX_CONFIG:-}" ]]; then
        if [[ "${ZC_BUG_FIX_CONFIG}" = /* ]]; then
            printf '%s\n' "${ZC_BUG_FIX_CONFIG}"
        else
            printf '%s\n' "${project_root}/${ZC_BUG_FIX_CONFIG}"
        fi
        return 0
    fi

    printf '%s\n' "${project_root}/${ZC_BUG_FIX_CONFIG_NAME}"
}

# 只读取项目级配置；显式覆盖时也只接受用户指定的那一份文件。
zc_bug_fix_get_effective_config_path() {
    local preferred_config

    preferred_config="$(zc_bug_fix_get_preferred_config_path)"

    if [[ -f "$preferred_config" ]]; then
        printf '%s\n' "$preferred_config"
        return 0
    fi

    printf '%s\n' "$preferred_config"
    return 1
}

# 示例文件固定使用可被 skills add 带上的非隐藏文件。
zc_bug_fix_get_example_path() {
    printf '%s\n' "$ZC_BUG_FIX_EXAMPLE_FILE"
}
