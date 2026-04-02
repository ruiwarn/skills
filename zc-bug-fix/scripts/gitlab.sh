#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHECK_SCRIPT="${SCRIPT_DIR}/check_config.sh"
JSON_PAYLOAD_SCRIPT="${SCRIPT_DIR}/json_payload.py"

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/config_paths.sh"

"$CHECK_SCRIPT" >/dev/null
CONFIG_FILE="$(zc_bug_fix_get_effective_config_path)"
# shellcheck source=/dev/null
source "$CONFIG_FILE"

API_BASE="${GITLAB_URL}/api/v4/projects/${GITLAB_PROJECT_ID}"

request() {
    local method="$1"
    local endpoint="$2"
    local body_file="${3:-}"

    if [[ -n "$body_file" ]]; then
        curl -sS -X "$method" \
            -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            -H "Content-Type: application/json" \
            --data-binary "@${body_file}" \
            "${API_BASE}${endpoint}"
    else
        curl -sS -X "$method" \
            -H "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
            -H "Content-Type: application/json" \
            "${API_BASE}${endpoint}"
    fi
}

create_issue() {
    local title="$1"
    local description_file="$2"
    local labels="${3:-bug}"
    local payload_file

    if [[ -z "$title" || -z "$description_file" ]]; then
        echo "错误: 用法 issue create <title> <description_file> [labels]" >&2
        exit 1
    fi
    if [[ ! -f "$description_file" ]]; then
        echo "错误: 描述文件不存在: $description_file" >&2
        exit 1
    fi

    payload_file=$(mktemp)
    python3 <<PY > "$payload_file"
import json
from pathlib import Path
print(json.dumps({
  "title": ${title@Q},
  "description": Path(${description_file@Q}).read_text(encoding='utf-8'),
  "labels": ${labels@Q}
}, ensure_ascii=False))
PY
    request POST "/issues" "$payload_file"
    rm -f "$payload_file"
}

get_issue() {
    local issue_iid="$1"
    if [[ -z "$issue_iid" ]]; then
        echo "错误: 用法 issue get <iid>" >&2
        exit 1
    fi
    request GET "/issues/${issue_iid}"
}

create_mr() {
    local source_branch="$1"
    local title="$2"
    local description_file="$3"
    local target_branch="${4:-${TARGET_BRANCH:-develop}}"
    local payload_file

    if [[ -z "$source_branch" || -z "$title" || -z "$description_file" ]]; then
        echo "错误: 用法 mr create <source_branch> <title> <description_file> [target_branch]" >&2
        exit 1
    fi
    if [[ ! -f "$description_file" ]]; then
        echo "错误: 描述文件不存在: $description_file" >&2
        exit 1
    fi

    payload_file=$(mktemp)
    python3 <<PY > "$payload_file"
import json
from pathlib import Path
print(json.dumps({
  "source_branch": ${source_branch@Q},
  "target_branch": ${target_branch@Q},
  "title": ${title@Q},
  "description": Path(${description_file@Q}).read_text(encoding='utf-8'),
  "remove_source_branch": True
}, ensure_ascii=False))
PY
    request POST "/merge_requests" "$payload_file"
    rm -f "$payload_file"
}

usage() {
    cat <<EOF
GitLab API脚本

用法:
  $0 issue create <title> <description_file> [labels]
  $0 issue get <iid>
  $0 mr create <source_branch> <title> <description_file> [target_branch]

说明:
  - description_file 必须是 UTF-8 markdown/text 文件
  - 推荐把 6D issue / MR 描述先写入文件，再传给脚本
EOF
}

case "${1:-}" in
    issue)
        shift
        case "${1:-}" in
            create)
                shift
                create_issue "$@"
                ;;
            get)
                shift
                get_issue "$@"
                ;;
            *)
                usage
                exit 1
                ;;
        esac
        ;;
    mr)
        shift
        case "${1:-}" in
            create)
                shift
                create_mr "$@"
                ;;
            *)
                usage
                exit 1
                ;;
        esac
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        usage
        exit 1
        ;;
esac
