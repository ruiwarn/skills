#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECK_SCRIPT="${SCRIPT_DIR}/check_config.sh"
ZENTAO_SCRIPT="${SCRIPT_DIR}/zentao.sh"
GITLAB_SCRIPT="${SCRIPT_DIR}/gitlab.sh"

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/config_paths.sh"

# 加载项目配置文件（用于获取 PROJECT_OWNER 等信息供 zentao-writeback 使用）
_ZC_CONFIG_FILE="$(zc_bug_fix_get_effective_config_path 2>/dev/null)" || true
if [[ -n "$_ZC_CONFIG_FILE" && -f "$_ZC_CONFIG_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$_ZC_CONFIG_FILE"
fi

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

# 创建 bugfix 分支，自动从 origin/develop 拉取最新代码。
# 参数: $1=bug_id, $2=short_desc（简短描述，用于分支名）
# 分支名格式: bugfix/<bug_id>-<short_desc>
create_branch() {
    local bug_id="$1"
    local short_desc="$2"

    [[ -n "$bug_id" && -n "$short_desc" ]] || {
        echo "错误: 用法 create-branch <bug_id> <short_desc>" >&2
        echo "示例: create-branch 5245 fix-timeout" >&2
        exit 1
    }

    local branch_name="bugfix/${bug_id}-${short_desc}"
    local current_branch
    current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

    # 如果已在目标分支上，直接返回
    if [[ "$current_branch" == "$branch_name" ]]; then
        echo "已在目标分支: $branch_name"
        return 0
    fi

    # 有未提交更改时自动 stash，防止切换分支丢失工作
    if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
        echo "警告: 工作区有未提交的更改，将使用 stash 暂存" >&2
        git stash push -m "auto-stash before creating $branch_name"
    fi

    # 从远程 develop 创建分支，保证基于最新代码
    echo "正在获取最新的 develop 分支..."
    git fetch origin develop 2>/dev/null || true

    if git show-ref --verify --quiet "refs/remotes/origin/develop"; then
        git checkout -b "$branch_name" origin/develop
    else
        git checkout develop 2>/dev/null || true
        git checkout -b "$branch_name"
    fi

    echo "✅ 已创建并切换到分支: $branch_name"
    echo "   基于: origin/develop"
}

# 推送当前分支到远程，拒绝在保护分支（develop/main/master）上执行。
# 这是防止弱模型直接 push 到 develop 的关键护栏。
push_branch() {
    local current_branch
    current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

    # 保护分支黑名单检查
    case "$current_branch" in
        develop|main|master)
            echo "⛔ 错误: 禁止直接在 '${current_branch}' 分支上推送！" >&2
            echo "请先使用 'create-branch <bug_id> <short_desc>' 创建 bugfix 分支。" >&2
            exit 1
            ;;
    esac

    # 分支命名规范警告
    if [[ ! "$current_branch" =~ ^bugfix/ ]]; then
        echo "警告: 当前分支 '${current_branch}' 不符合 bugfix/* 命名规范" >&2
        echo "推荐使用 'create-branch <bug_id> <short_desc>' 创建标准分支" >&2
    fi

    git push -u origin "$current_branch"
    echo "✅ 已推送分支: $current_branch"
}

# 一条命令完成全部禅道回写操作：确认 + 设置 browser 字段 + 解决。
# 四个参数全部必填，任何缺失都会被拒绝，确保弱模型不会遗漏步骤。
# 参数: $1=bug_id, $2=bug_type(中文分类名), $3=issue_url, $4=mr_url
zentao_writeback() {
    local bug_id="$1"
    local bug_type="$2"
    local issue_url="$3"
    local mr_url="$4"

    # 严格校验四个参数，缺一不可
    if [[ -z "$bug_id" || -z "$bug_type" || -z "$issue_url" || -z "$mr_url" ]]; then
        echo "错误: 用法 zentao-writeback <bug_id> <bug_type> <issue_url> <mr_url>" >&2
        echo "四个参数缺一不可！" >&2
        echo "  bug_id    : 禅道 Bug 编号" >&2
        echo "  bug_type  : 中文 Bug 分类名（如 '编码_流程逻辑实现问题'）" >&2
        echo "  issue_url : GitLab Issue URL" >&2
        echo "  mr_url    : GitLab MR URL" >&2
        exit 1
    fi

    # 校验 Issue URL 格式
    if ! printf '%s' "$issue_url" | grep -Eq 'https?://[^[:space:]]+/-/issues/[0-9]+'; then
        echo "错误: issue_url 格式不正确: $issue_url" >&2
        echo "正确格式: http://172.17.0.100:8080/<group>/<project>/-/issues/<number>" >&2
        exit 1
    fi

    # 校验 MR URL 格式
    if ! printf '%s' "$mr_url" | grep -Eq 'https?://[^[:space:]]+/-/merge_requests/[0-9]+'; then
        echo "错误: mr_url 格式不正确: $mr_url" >&2
        echo "正确格式: http://172.17.0.100:8080/<group>/<project>/-/merge_requests/<number>" >&2
        exit 1
    fi

    echo "=========================================="
    echo "禅道回写开始: Bug #${bug_id}"
    echo "=========================================="

    # 步骤 1/4: 检查 Bug 当前状态，防止重复操作
    echo ""
    echo ">>> 步骤 1/4: 检查 Bug 当前状态..."
    "$ZENTAO_SCRIPT" get "$bug_id" > /dev/null

    # 步骤 2/4: 确认 Bug，评论自动附带 Issue 可点击链接
    echo ""
    echo ">>> 步骤 2/4: 确认 Bug（附带 Issue 链接）..."
    local confirm_comment
    confirm_comment="已创建 GitLab issue: ${issue_url}"
    confirm_comment="$(format_zentao_clickable_links "$confirm_comment")"
    "$ZENTAO_SCRIPT" confirm "$bug_id" "$confirm_comment"

    # 步骤 3/4: 设置 Bug 分类到 browser 字段（不是评论！）
    echo ""
    echo ">>> 步骤 3/4: 设置 Bug 分类到 browser 字段: ${bug_type}..."
    "$ZENTAO_SCRIPT" set-browser-type "$bug_id" "$bug_type"

    # 步骤 4/4: 解决 Bug，评论自动附带 MR 可点击链接，转派给项目负责人
    # 注意：不传 bug_type 给 resolve，因为已在步骤 3 单独设置
    echo ""
    echo ">>> 步骤 4/4: 解决 Bug（附带 MR 链接）..."
    local resolve_comment
    resolve_comment="已创建 GitLab MR: ${mr_url}"
    resolve_comment="$(format_zentao_clickable_links "$resolve_comment")"
    "$ZENTAO_SCRIPT" resolve "$bug_id" fixed "$resolve_comment" "${PROJECT_OWNER}" ""

    echo ""
    echo "=========================================="
    echo "✅ 禅道回写完成:"
    echo "   Bug #${bug_id}"
    echo "   - 状态: 已确认 → 已解决"
    echo "   - Browser 字段: ${bug_type}"
    echo "   - Issue 链接: ${issue_url}"
    echo "   - MR 链接: ${mr_url}"
    echo "   - 已转派给: ${PROJECT_OWNER}"
    echo "=========================================="
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
bug-fix 主控脚本（严格顺序执行）

推荐命令（按阶段顺序使用）:
  $0 check-config                                          # 阶段 0: 检查配置
  $0 fetch <bug_id>                                        # 阶段 1: 读取禅道 Bug
  $0 create-branch <bug_id> <short_desc>                   # 阶段 4: 创建 bugfix 分支
  $0 push-branch                                           # 阶段 4: 推送分支（拒绝保护分支）
  $0 create-issue <bug_id> <desc_file> [labels]            # 阶段 5: 创建 GitLab Issue
  $0 create-mr <bug_id> <branch> <desc_file> [target]      # 阶段 6: 创建 GitLab MR
  $0 zentao-writeback <bug_id> <type> <issue_url> <mr_url> # 阶段 7: 一键回写禅道

备用命令（仅在 zentao-writeback 失败时逐步使用）:
  $0 zentao-confirm <bug_id> [comment]
  $0 zentao-set-browser-type <bug_id> <bug_type>
  $0 zentao-resolve <bug_id> [comment] [assigned_to] [bug_type]
  $0 config-hint

说明:
  1. 按阶段编号 0→8 顺序执行
  2. 禁止在 develop/main/master 上直接 commit 或 push
  3. zentao-writeback 四个参数全部必填
  4. bug_type 是中文分类名，会写入禅道 browser 字段（不是评论）
  5. issue / MR 描述必须先写入文件，不要拼命令行
  6. resolve 默认转派给 zc-bug-fix.config 中的 PROJECT_OWNER
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
    create-branch)
        shift
        create_branch "$@"
        ;;
    push-branch)
        shift
        push_branch "$@"
        ;;
    zentao-writeback)
        shift
        zentao_writeback "$@"
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
