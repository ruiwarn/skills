#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/../.config"
CHECK_SCRIPT="${SCRIPT_DIR}/check_config.sh"
COOKIE_FILE="/tmp/zentao_cookies_$$.txt"

cleanup() {
    rm -f "$COOKIE_FILE"
}
trap cleanup EXIT

"$CHECK_SCRIPT" >/dev/null
# shellcheck source=/dev/null
source "$CONFIG_FILE"

login() {
    local response
    response=$(curl -sS -c "$COOKIE_FILE" -X POST "${ZENTAO_URL}/user-login.json" \
        -d "account=${ZENTAO_ACCOUNT}&password=${ZENTAO_PASSWORD}")

    if ! printf '%s' "$response" | grep -q '"status":"success"'; then
        echo "错误: 禅道登录失败" >&2
        echo "$response" >&2
        exit 1
    fi
}

get_bug() {
    local bug_id="$1"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 get <bug_id>" >&2; exit 1; }
    login
    curl -sS -b "$COOKIE_FILE" "${ZENTAO_URL}/bug-view-${bug_id}.json"
}

confirm_bug() {
    local bug_id="$1"
    local comment="${2:-已确认}"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 confirm <bug_id> [comment]" >&2; exit 1; }
    login
    curl -sS -b "$COOKIE_FILE" -X POST "${ZENTAO_URL}/bug-confirmBug-${bug_id}.json" \
        --data-urlencode "comment=${comment}"
}

map_bug_type_to_browser_code() {
    local bug_type="$1"

    case "$bug_type" in
        "需求不清问题") echo "ie" ;;
        "需求错误问题") echo "ie11" ;;
        "设计_系统整体设计问题") echo "ie10" ;;
        "设计_功能间接口问题") echo "ie9" ;;
        "设计_功能交互问题") echo "ie8" ;;
        "设计_边界值设计问题") echo "ie7" ;;
        "设计_流程逻辑设计问题") echo "ie6" ;;
        "设计_算法设计问题") echo "chrome" ;;
        "编码_流程逻辑实现问题") echo "firefox" ;;
        "编码_编程规范语法问题") echo "firefox3" ;;
        "编码_编程规范内存问题") echo "firefox2" ;;
        "编码_编程规范初始化") echo "opera" ;;
        "编码_编程规范函数用错") echo "oprea11" ;;
        "编码_编程规范指针调用") echo "oprea10" ;;
        "编码_代码合并问题") echo "opera9" ;;
        "编码_模块间接口问题") echo "safari" ;;
        "编码_库使用问题") echo "maxthon" ;;
        "编码_库修改问题") echo "uc" ;;
        "编码-内核保护机制问题") echo "firefox4" ;;
        *) echo "" ;;
    esac
}

is_blacklisted_bug_type() {
    local bug_type="$1"

    case "$bug_type" in
        ""|"继承或历史遗留"|"未明确定位"|"非问题")
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

update_bug_browser_type() {
    local bug_id="$1"
    local bug_type="$2"
    local browser_code

    [[ -n "$bug_id" ]] || { echo "错误: 用法 set-browser-type <bug_id> <bug_type>" >&2; exit 1; }
    [[ -n "$bug_type" ]] || { echo "错误: bug_type 不能为空" >&2; exit 1; }

    if is_blacklisted_bug_type "$bug_type"; then
        echo "错误: bug 类型 '$bug_type' 在黑名单中，禁止自动提交" >&2
        exit 1
    fi

    browser_code="$(map_bug_type_to_browser_code "$bug_type")"
    if [[ -z "$browser_code" ]]; then
        echo "错误: 未识别的 bug 类型 '$bug_type'，请人工确认后再提交" >&2
        exit 1
    fi

    login
    curl -sS -b "$COOKIE_FILE" -X POST "${ZENTAO_URL}/bug-edit-${bug_id}.json" \
        --data-urlencode "browser=${browser_code}"
}

resolve_bug() {
    local bug_id="$1"
    local resolution="${2:-fixed}"
    local comment="${3:-已修复}"
    local assigned_to="${4:-${PROJECT_OWNER}}"
    local bug_type="$5"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 resolve <bug_id> [resolution] [comment] [assigned_to] [bug_type]" >&2; exit 1; }
    login
    curl -sS -b "$COOKIE_FILE" -X POST "${ZENTAO_URL}/bug-resolve-${bug_id}.json" \
        --data-urlencode "resolution=${resolution}" \
        --data-urlencode "comment=${comment}" \
        --data-urlencode "assignedTo=${assigned_to}"

    if [[ -n "$bug_type" ]]; then
        update_bug_browser_type "$bug_id" "$bug_type"
    fi
}

usage() {
    cat <<EOF
禅道脚本

用法:
  $0 get <bug_id>
  $0 confirm <bug_id> [comment]
  $0 set-browser-type <bug_id> <bug_type>
  $0 resolve <bug_id> [resolution] [comment] [assigned_to] [bug_type]

说明:
  resolve 默认会在解决后转派给 .config 中的 PROJECT_OWNER
  set-browser-type / resolve 只允许提交白名单中的明确 bug 类型
  黑名单禁止项：继承或历史遗留、未明确定位、非问题、空值
EOF
}

case "${1:-}" in
    get)
        shift
        get_bug "$@"
        ;;
    confirm)
        shift
        confirm_bug "$@"
        ;;
    set-browser-type)
        shift
        update_bug_browser_type "$@"
        ;;
    resolve)
        shift
        resolve_bug "$@"
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
