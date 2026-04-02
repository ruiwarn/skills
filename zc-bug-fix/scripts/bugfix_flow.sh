#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECK_SCRIPT="${SCRIPT_DIR}/check_config.sh"
ZENTAO_SCRIPT="${SCRIPT_DIR}/zentao.sh"
GITLAB_SCRIPT="${SCRIPT_DIR}/gitlab.sh"

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/config_paths.sh"

run_check() {
    "$CHECK_SCRIPT"
}

fetch_bug() {
    local bug_id="$1"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 fetch <bug_id>" >&2; exit 1; }
    "$ZENTAO_SCRIPT" get "$bug_id"
}

create_issue() {
    local bug_id="$1"
    local description_file="$2"
    local labels="${3:-bug}"
    local title_prefix="${4:-Bug}"
    local title

    [[ -n "$bug_id" && -n "$description_file" ]] || {
        echo "错误: 用法 create-issue <bug_id> <description_file> [labels] [title_prefix]" >&2
        exit 1
    }

    title="${title_prefix} #${bug_id}"
    "$GITLAB_SCRIPT" issue create "$title" "$description_file" "$labels"
}

create_mr() {
    local bug_id="$1"
    local source_branch="$2"
    local description_file="$3"
    local target_branch="${4:-}"
    local title_prefix="${5:-Bugfix}"
    local title

    [[ -n "$bug_id" && -n "$source_branch" && -n "$description_file" ]] || {
        echo "错误: 用法 create-mr <bug_id> <source_branch> <description_file> [target_branch] [title_prefix]" >&2
        exit 1
    }

    title="${title_prefix} #${bug_id}"
    if [[ -n "$target_branch" ]]; then
        "$GITLAB_SCRIPT" mr create "$source_branch" "$title" "$description_file" "$target_branch"
    else
        "$GITLAB_SCRIPT" mr create "$source_branch" "$title" "$description_file"
    fi
}

contains_gitlab_issue_link() {
    local comment="${1:-}"
    printf '%s' "$comment" | grep -Eq 'https?://[^[:space:]]+/-/issues/[0-9]+'
}

contains_gitlab_mr_link() {
    local comment="${1:-}"
    printf '%s' "$comment" | grep -Eq 'https?://[^[:space:]]+/-/merge_requests/[0-9]+'
}

# 将 GitLab issue / MR URL 包装成禅道备注里的可点击 HTML 链接。
format_zentao_clickable_links() {
    local comment="${1:-}"

    python3 - "$comment" <<'PY'
import re
import sys

comment = sys.argv[1]

# 已经是 HTML 链接时直接透传，避免重复包裹后破坏原始格式。
if "<a " in comment.lower():
    print(comment)
    raise SystemExit(0)

pattern = re.compile(r'https?://[^\s<>"\']+/-/(?P<kind>issues|merge_requests)/(?P<iid>\d+)')

def replace_link(match):
    url = match.group(0)
    kind = match.group("kind")
    iid = match.group("iid")

    if kind == "issues":
        label = f"Issue #{iid}"
    else:
        label = f"MR !{iid}"

    return f'<a href="{url}">{label}</a>'

print(pattern.sub(replace_link, comment))
PY
}

zentao_confirm() {
    local bug_id="$1"
    local comment="${2:-}"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 zentao-confirm <bug_id> [comment]" >&2; exit 1; }

    # 回写禅道前强制要求附带 GitLab issue 链接，避免跳过 issue 直接 confirm。
    if ! contains_gitlab_issue_link "$comment"; then
        echo "错误: 确认评论中必须包含 GitLab issue 链接。请先创建 issue 再回写禅道。" >&2
        exit 1
    fi

    # 统一在回写前把 GitLab URL 包装为可点击链接，方便在禅道界面直接打开。
    comment="$(format_zentao_clickable_links "$comment")"
    "$ZENTAO_SCRIPT" confirm "$bug_id" "$comment"
}

zentao_set_browser_type() {
    local bug_id="$1"
    local bug_type="$2"
    [[ -n "$bug_id" && -n "$bug_type" ]] || { echo "错误: 用法 zentao-set-browser-type <bug_id> <bug_type>" >&2; exit 1; }
    "$ZENTAO_SCRIPT" set-browser-type "$bug_id" "$bug_type"
}

zentao_resolve() {
    local bug_id="$1"
    local comment="${2:-}"
    local assigned_to="${3:-}"
    local bug_type="${4:-}"
    [[ -n "$bug_id" ]] || { echo "错误: 用法 zentao-resolve <bug_id> [comment] [assigned_to] [bug_type]" >&2; exit 1; }

    # resolve 前必须拿到 MR 链接，确保禅道回写发生在代码和评审链路完成之后。
    if ! contains_gitlab_mr_link "$comment"; then
        echo "错误: 解决评论中必须包含 GitLab MR 链接。请先创建 MR 再回写禅道。" >&2
        exit 1
    fi

    # resolve 评论同样转成可点击链接，减少测试/研发二次复制 URL。
    comment="$(format_zentao_clickable_links "$comment")"
    "$ZENTAO_SCRIPT" resolve "$bug_id" fixed "$comment" "$assigned_to" "$bug_type"
}

print_config_hint() {
    local preferred_config
    local example_file

    preferred_config="$(zc_bug_fix_get_preferred_config_path)"
    example_file="$(zc_bug_fix_get_example_path)"

    # 统一提示项目级配置路径，避免安装 skill 时覆盖真实业务配置。
    cat <<EOF
配置文件:
  ${preferred_config}

初始化方式:
  cp ${example_file} ${preferred_config}
EOF
}

usage() {
    cat <<EOF
bug-fix 主控脚本

用法:
  $0 check-config
  $0 fetch <bug_id>
  $0 create-issue <bug_id> <description_file> [labels] [title_prefix]
  $0 create-mr <bug_id> <source_branch> <description_file> [target_branch] [title_prefix]
  $0 zentao-confirm <bug_id> [comment]
  $0 zentao-set-browser-type <bug_id> <bug_type>
  $0 zentao-resolve <bug_id> [comment] [assigned_to] [bug_type]
  $0 config-hint

说明:
  1. 先执行 check-config
  2. issue / mr 描述必须先写入 markdown 文件
  3. 本脚本只做编排，不替代人工确认
  4. zentao-resolve 默认转派给 zc-bug-fix.config 中的 PROJECT_OWNER
  5. bug_type 传中文分类名，脚本内部会自动映射到禅道 browser 字段
  6. zentao-confirm 评论里必须带 GitLab issue 链接
  7. zentao-resolve 评论里必须带 GitLab MR 链接
EOF
}

case "${1:-}" in
    check-config)
        run_check
        ;;
    fetch)
        shift
        fetch_bug "$@"
        ;;
    create-issue)
        shift
        create_issue "$@"
        ;;
    create-mr)
        shift
        create_mr "$@"
        ;;
    zentao-confirm)
        shift
        zentao_confirm "$@"
        ;;
    zentao-set-browser-type)
        shift
        zentao_set_browser_type "$@"
        ;;
    zentao-resolve)
        shift
        zentao_resolve "$@"
        ;;
    config-hint)
        print_config_hint
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
