#!/usr/bin/env bash
#
# C/C++ Static Analysis Tool
# 支持 clang-tidy 和 cppcheck 的批量静态分析工具
#
set -euo pipefail

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 获取脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
CONFIG_FILE="$SKILL_DIR/config.json"

# 默认配置
DEFAULT_CHECKS="bugprone-*,clang-analyzer-*"
DEFAULT_CPPCHECK_ENABLE="warning,performance,portability"

# 全局变量
FILES=()
COMPDB_DIR=""
CHECKS="$DEFAULT_CHECKS"
HEADER_FILTER=""
SKIP_CPPCHECK=0
SKIP_CLANG_TIDY=0
OUTPUT_FORMAT="text"  # text, json, markdown
GIT_MODE=""           # staged, modified, all
DIRECTORY=""
SEVERITY_FILTER=""    # error, warning, all
IGNORE_PATTERNS=()
QUIET=0
SUMMARY_ONLY=0
PROJECT_ROOT_SET=0

# 统计变量
TOTAL_ERRORS=0
TOTAL_WARNINGS=0
TOTAL_INFO=0
declare -A FILE_ISSUES=()
HAS_FILE_ISSUES=0

usage() {
    cat << EOF
${BOLD}C/C++ 静态分析工具${NC}

${BOLD}用法:${NC}
  $0 [选项]

${BOLD}文件选择:${NC}
  -f, --file <file>        检查单个文件
  -d, --directory <dir>    检查目录下所有 C/C++ 文件
  --git-staged             检查 git 暂存的文件
  --git-modified           检查 git 已修改的文件 (包括未暂存)
  --git-all                检查所有 git 变更的文件

${BOLD}工具配置:${NC}
  -p, --compdb <path>      compile_commands.json 路径或所在目录 (默认: 自动检测)
  --project-root <dir>     项目根目录 (建议由调用方强制传入)
  --checks <pattern>       clang-tidy 检查规则 (默认: $DEFAULT_CHECKS)
  --header-filter <regex>  clang-tidy 头文件过滤正则
  --skip-cppcheck          跳过 cppcheck
  --skip-clang-tidy        跳过 clang-tidy

${BOLD}输出控制:${NC}
  --format <type>          输出格式: text, json, markdown (默认: text)
  --severity <level>       严重程度过滤: error, warning, all (默认: all)
  --ignore <pattern>       忽略的警告类型 (可多次使用)
  --summary                只显示汇总统计
  -q, --quiet              静默模式，只输出错误

${BOLD}其他:${NC}
  -h, --help               显示帮助信息

${BOLD}示例:${NC}
  $0 --git-staged                           # 检查暂存的文件
  $0 --git-modified --format markdown       # 检查修改的文件，Markdown 输出
  $0 -f code/APP/main.c --severity error    # 只检查单文件的错误
  $0 -d code/APP --summary                  # 检查目录并只显示汇总

EOF
    exit 0
}

# 加载项目配置
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        # 如果有 jq 则解析配置
        if command -v jq &>/dev/null; then
            local ignore_list
            ignore_list=$(jq -r '.ignore_checks[]? // empty' "$CONFIG_FILE" 2>/dev/null || true)
            while IFS= read -r pattern; do
                [[ -n "$pattern" ]] && IGNORE_PATTERNS+=("$pattern")
            done <<< "$ignore_list"

            # 加载其他配置
            local cfg_checks
            cfg_checks=$(jq -r '.clang_tidy_checks // empty' "$CONFIG_FILE" 2>/dev/null || true)
            [[ -n "$cfg_checks" ]] && CHECKS="$cfg_checks"

            local cfg_header_filter
            cfg_header_filter=$(jq -r '.header_filter // empty' "$CONFIG_FILE" 2>/dev/null || true)
            [[ -n "$cfg_header_filter" ]] && HEADER_FILTER="$cfg_header_filter"
        fi
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -f|--file)
                FILES+=("$2")
                shift 2
                ;;
            -d|--directory)
                DIRECTORY="$2"
                shift 2
                ;;
            --git-staged)
                GIT_MODE="staged"
                shift
                ;;
            --git-modified)
                GIT_MODE="modified"
                shift
                ;;
            --git-all)
                GIT_MODE="all"
                shift
                ;;
            -p|--compdb)
                COMPDB_DIR="$2"
                shift 2
                ;;
            --project-root)
                PROJECT_ROOT="$2"
                PROJECT_ROOT_SET=1
                shift 2
                ;;
            --checks)
                CHECKS="$2"
                shift 2
                ;;
            --header-filter)
                HEADER_FILTER="$2"
                shift 2
                ;;
            --skip-cppcheck)
                SKIP_CPPCHECK=1
                shift
                ;;
            --skip-clang-tidy)
                SKIP_CLANG_TIDY=1
                shift
                ;;
            --format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --severity)
                SEVERITY_FILTER="$2"
                shift 2
                ;;
            --ignore)
                IGNORE_PATTERNS+=("$2")
                shift 2
                ;;
            --summary)
                SUMMARY_ONLY=1
                shift
                ;;
            -q|--quiet)
                QUIET=1
                shift
                ;;
            -h|--help)
                usage
                ;;
            *)
                echo -e "${RED}未知参数: $1${NC}" >&2
                usage
                ;;
        esac
    done
}

# 获取 git 变更文件
get_git_files() {
    local mode="$1"
    local files=()

    cd "$PROJECT_ROOT"

    case "$mode" in
        staged)
            while IFS= read -r -d '' file; do
                files+=("$file")
            done < <(git diff --cached --name-only -z --diff-filter=ACMR -- '*.c' '*.h' '*.cpp' '*.hpp' 2>/dev/null || true)
            ;;
        modified)
            while IFS= read -r -d '' file; do
                files+=("$file")
            done < <(git diff --name-only -z --diff-filter=ACMR -- '*.c' '*.h' '*.cpp' '*.hpp' 2>/dev/null || true)
            while IFS= read -r -d '' file; do
                files+=("$file")
            done < <(git diff --cached --name-only -z --diff-filter=ACMR -- '*.c' '*.h' '*.cpp' '*.hpp' 2>/dev/null || true)
            ;;
        all)
            while IFS= read -r -d '' file; do
                files+=("$file")
            done < <(git status --porcelain -z -- '*.c' '*.h' '*.cpp' '*.hpp' 2>/dev/null | grep -z -v '^D' | cut -z -c4- || true)
            ;;
    esac

    # 去重
    printf '%s\n' "${files[@]}" | sort -u
}

# 获取目录下的 C/C++ 文件
get_directory_files() {
    local dir="$1"
    find "$dir" -type f \( -name "*.c" -o -name "*.h" -o -name "*.cpp" -o -name "*.hpp" \) 2>/dev/null | \
        grep -v "^drivers/" | sort
}

# 检测 compile_commands.json
detect_compdb() {
    if [[ -n "$COMPDB_DIR" ]]; then
        if [[ -f "$COMPDB_DIR" ]]; then
            COMPDB_DIR="$(cd "$(dirname "$COMPDB_DIR")" && pwd)"
        fi
        return
    fi

    if [[ -f "$PROJECT_ROOT/compile_commands.json" ]]; then
        COMPDB_DIR="$PROJECT_ROOT"
    elif [[ -f "$PROJECT_ROOT/env/compile_commands.json" ]]; then
        COMPDB_DIR="$PROJECT_ROOT/env"
    elif [[ -f "$PROJECT_ROOT/build/compile_commands.json" ]]; then
        COMPDB_DIR="$PROJECT_ROOT/build"
    else
        echo -e "${YELLOW}警告: 未找到 compile_commands.json，clang-tidy 可能无法正常工作${NC}" >&2
    fi
}

# 检查是否应该忽略该警告
should_ignore() {
    local message="$1"
    if [[ ${#IGNORE_PATTERNS[@]} -eq 0 ]]; then
        return 1
    fi
    for pattern in "${IGNORE_PATTERNS[@]}"; do
        if [[ "$message" == *"$pattern"* ]]; then
            return 0
        fi
    done
    return 1
}

# 解析 clang-tidy 输出
parse_clang_tidy_output() {
    local output="$1"
    local current_file=""
    local issues=()

    while IFS= read -r line; do
        # 匹配警告/错误行: file:line:col: severity: message [check-name]
        if [[ "$line" =~ ^(.+):([0-9]+):([0-9]+):\ (warning|error|note):\ (.+)\ \[(.+)\]$ ]]; then
            local file="${BASH_REMATCH[1]}"
            local line_num="${BASH_REMATCH[2]}"
            local col="${BASH_REMATCH[3]}"
            local severity="${BASH_REMATCH[4]}"
            local message="${BASH_REMATCH[5]}"
            local check="${BASH_REMATCH[6]}"

            # 检查是否忽略
            if should_ignore "$check"; then
                continue
            fi

            # 严重程度过滤
            if [[ "$SEVERITY_FILTER" == "error" && "$severity" != "error" ]]; then
                continue
            fi

            # 统计
            case "$severity" in
                error) ((TOTAL_ERRORS++)) || true ;;
                warning) ((TOTAL_WARNINGS++)) || true ;;
                note) ((TOTAL_INFO++)) || true ;;
            esac

            # 记录到文件统计
            FILE_ISSUES["$file"]=$((${FILE_ISSUES["$file"]:-0} + 1))
            HAS_FILE_ISSUES=1

            # 输出
            if [[ $SUMMARY_ONLY -eq 0 ]]; then
                case "$OUTPUT_FORMAT" in
                    text)
                        case "$severity" in
                            error) echo -e "${RED}[ERROR]${NC} $file:$line_num: $message [$check]" ;;
                            warning) echo -e "${YELLOW}[WARN]${NC} $file:$line_num: $message [$check]" ;;
                            note) echo -e "${BLUE}[NOTE]${NC} $file:$line_num: $message [$check]" ;;
                        esac
                        ;;
                    markdown)
                        local icon=""
                        case "$severity" in
                            error) icon="🔴" ;;
                            warning) icon="🟡" ;;
                            note) icon="🔵" ;;
                        esac
                        echo "| $icon | \`$file\` | $line_num | $message | \`$check\` |"
                        ;;
                    json)
                        echo "{\"file\":\"$file\",\"line\":$line_num,\"severity\":\"$severity\",\"message\":\"$message\",\"check\":\"$check\"}"
                        ;;
                esac
            fi
        fi
    done <<< "$output"
}

# 解析 cppcheck 输出
parse_cppcheck_output() {
    local output="$1"

    while IFS= read -r line; do
        # cppcheck 格式: file:line:col: severity: message [id]
        if [[ "$line" =~ ^(.+):([0-9]+):([0-9]+):\ (error|warning|style|performance|portability|information):\ (.+)\ \[(.+)\]$ ]]; then
            local file="${BASH_REMATCH[1]}"
            local line_num="${BASH_REMATCH[2]}"
            local severity="${BASH_REMATCH[4]}"
            local message="${BASH_REMATCH[5]}"
            local check="${BASH_REMATCH[6]}"

            # 检查是否忽略
            if should_ignore "$check"; then
                continue
            fi

            # 映射 cppcheck 严重程度
            local mapped_severity="warning"
            case "$severity" in
                error) mapped_severity="error" ;;
                warning|style|performance|portability) mapped_severity="warning" ;;
                information) mapped_severity="info" ;;
            esac

            # 严重程度过滤
            if [[ "$SEVERITY_FILTER" == "error" && "$mapped_severity" != "error" ]]; then
                continue
            fi

            # 统计
            case "$mapped_severity" in
                error) ((TOTAL_ERRORS++)) || true ;;
                warning) ((TOTAL_WARNINGS++)) || true ;;
                info) ((TOTAL_INFO++)) || true ;;
            esac

            FILE_ISSUES["$file"]=$((${FILE_ISSUES["$file"]:-0} + 1))
            HAS_FILE_ISSUES=1

            if [[ $SUMMARY_ONLY -eq 0 ]]; then
                case "$OUTPUT_FORMAT" in
                    text)
                        case "$mapped_severity" in
                            error) echo -e "${RED}[ERROR]${NC} $file:$line_num: $message [$check]" ;;
                            warning) echo -e "${YELLOW}[WARN]${NC} $file:$line_num: $message [$check]" ;;
                            info) echo -e "${CYAN}[INFO]${NC} $file:$line_num: $message [$check]" ;;
                        esac
                        ;;
                    markdown)
                        local icon=""
                        case "$mapped_severity" in
                            error) icon="🔴" ;;
                            warning) icon="🟡" ;;
                            info) icon="🔵" ;;
                        esac
                        echo "| $icon | \`$file\` | $line_num | $message | \`$check\` |"
                        ;;
                    json)
                        echo "{\"file\":\"$file\",\"line\":$line_num,\"severity\":\"$mapped_severity\",\"message\":\"$message\",\"check\":\"$check\"}"
                        ;;
                esac
            fi
        fi
    done <<< "$output"
}

# 运行 clang-tidy
run_clang_tidy() {
    local file="$1"

    if [[ $SKIP_CLANG_TIDY -eq 1 ]]; then
        return
    fi

    if ! command -v clang-tidy &>/dev/null; then
        [[ $QUIET -eq 0 ]] && echo -e "${YELLOW}警告: clang-tidy 未安装${NC}" >&2
        return
    fi

    local cmd="clang-tidy"
    [[ -n "$COMPDB_DIR" ]] && cmd="$cmd -p $COMPDB_DIR"
    cmd="$cmd --checks=$CHECKS"
    [[ -n "$HEADER_FILTER" ]] && cmd="$cmd -header-filter=$HEADER_FILTER"
    cmd="$cmd $file"

    local output
    output=$($cmd 2>&1 || true)
    parse_clang_tidy_output "$output"
}

# 运行 cppcheck
run_cppcheck() {
    local file="$1"

    if [[ $SKIP_CPPCHECK -eq 1 ]]; then
        return
    fi

    if ! command -v cppcheck &>/dev/null; then
        [[ $QUIET -eq 0 ]] && echo -e "${YELLOW}警告: cppcheck 未安装${NC}" >&2
        return
    fi

    local output
    output=$(cppcheck --enable="$DEFAULT_CPPCHECK_ENABLE" \
        --suppress=missingIncludeSystem \
        --template='{file}:{line}:{column}: {severity}: {message} [{id}]' \
        --quiet "$file" 2>&1 || true)
    parse_cppcheck_output "$output"
}

# 输出汇总
print_summary() {
    local total=$((TOTAL_ERRORS + TOTAL_WARNINGS + TOTAL_INFO))

    case "$OUTPUT_FORMAT" in
        text)
            echo ""
            echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
            echo -e "${BOLD}                    静态分析汇总报告${NC}"
            echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
            echo ""
            echo -e "  ${RED}错误 (Errors):${NC}    $TOTAL_ERRORS"
            echo -e "  ${YELLOW}警告 (Warnings):${NC}  $TOTAL_WARNINGS"
            echo -e "  ${BLUE}提示 (Info):${NC}      $TOTAL_INFO"
            echo -e "  ${BOLD}总计:${NC}             $total"
            echo ""

            if [[ $HAS_FILE_ISSUES -eq 1 ]]; then
                echo -e "${BOLD}问题文件统计:${NC}"
                for file in "${!FILE_ISSUES[@]}"; do
                    echo "  - $file: ${FILE_ISSUES[$file]} 个问题"
                done | sort -t: -k2 -nr | head -10
                echo ""
            fi

            if [[ $TOTAL_ERRORS -gt 0 ]]; then
                echo -e "${RED}✗ 发现严重错误，请立即修复！${NC}"
            elif [[ $TOTAL_WARNINGS -gt 0 ]]; then
                echo -e "${YELLOW}⚠ 存在警告，建议检查${NC}"
            else
                echo -e "${GREEN}✓ 未发现问题${NC}"
            fi
            ;;
        markdown)
            echo ""
            echo "## 静态分析汇总"
            echo ""
            echo "| 类型 | 数量 |"
            echo "|------|------|"
            echo "| 🔴 错误 | $TOTAL_ERRORS |"
            echo "| 🟡 警告 | $TOTAL_WARNINGS |"
            echo "| 🔵 提示 | $TOTAL_INFO |"
            echo "| **总计** | **$total** |"
            echo ""

            if [[ $HAS_FILE_ISSUES -eq 1 ]]; then
                echo "### 问题文件 Top 10"
                echo ""
                echo "| 文件 | 问题数 |"
                echo "|------|--------|"
                for file in "${!FILE_ISSUES[@]}"; do
                    echo "| \`$file\` | ${FILE_ISSUES[$file]} |"
                done | sort -t'|' -k3 -nr | head -10
            fi
            ;;
        json)
            echo "{"
            echo "  \"summary\": {"
            echo "    \"errors\": $TOTAL_ERRORS,"
            echo "    \"warnings\": $TOTAL_WARNINGS,"
            echo "    \"info\": $TOTAL_INFO,"
            echo "    \"total\": $total"
            echo "  },"
            echo "  \"files\": {"
            local first=1
            if [[ $HAS_FILE_ISSUES -eq 1 ]]; then
                for file in "${!FILE_ISSUES[@]}"; do
                    [[ $first -eq 0 ]] && echo ","
                    echo -n "    \"$file\": ${FILE_ISSUES[$file]}"
                    first=0
                done
            fi
            echo ""
            echo "  }"
            echo "}"
            ;;
    esac
}

# 主函数
main() {
    load_config
    parse_args "$@"

    if [[ $PROJECT_ROOT_SET -ne 1 ]]; then
        echo -e "${RED}错误: 必须传入 --project-root <dir>（用于支持 skill 不在工程内的场景）${NC}" >&2
        exit 2
    fi
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        echo -e "${RED}错误: --project-root 不是有效目录: $PROJECT_ROOT${NC}" >&2
        exit 2
    fi

    cd "$PROJECT_ROOT"

    # 收集要检查的文件
    if [[ -n "$GIT_MODE" ]]; then
        while IFS= read -r file; do
            [[ -n "$file" && -f "$file" ]] && FILES+=("$file")
        done < <(get_git_files "$GIT_MODE")
    fi

    if [[ -n "$DIRECTORY" ]]; then
        while IFS= read -r file; do
            [[ -n "$file" ]] && FILES+=("$file")
        done < <(get_directory_files "$DIRECTORY")
    fi

    # 去重
    if [[ ${#FILES[@]} -gt 0 ]]; then
        readarray -t FILES < <(printf '%s\n' "${FILES[@]}" | sort -u)
    fi

    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo -e "${YELLOW}没有找到要检查的文件${NC}" >&2
        exit 0
    fi

    detect_compdb

    # 输出头部
    if [[ $QUIET -eq 0 ]]; then
        case "$OUTPUT_FORMAT" in
            text)
                echo -e "${BOLD}C/C++ 静态分析${NC}"
                echo -e "检查 ${#FILES[@]} 个文件..."
                echo ""
                ;;
            markdown)
                echo "# C/C++ 静态分析报告"
                echo ""
                echo "检查文件数: ${#FILES[@]}"
                echo ""
                if [[ $SUMMARY_ONLY -eq 0 ]]; then
                    echo "## 详细问题列表"
                    echo ""
                    echo "| 级别 | 文件 | 行号 | 描述 | 检查项 |"
                    echo "|------|------|------|------|--------|"
                fi
                ;;
            json)
                echo "{\"issues\":["
                ;;
        esac
    fi

    # 运行检查
    local first_json=1
    for file in "${FILES[@]}"; do
        [[ $QUIET -eq 0 && "$OUTPUT_FORMAT" == "text" && $SUMMARY_ONLY -eq 0 ]] && \
            echo -e "${CYAN}检查: $file${NC}"

        run_clang_tidy "$file"
        run_cppcheck "$file"
    done

    # 输出尾部
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        echo "],"
    fi

    print_summary

    # 返回码
    if [[ $TOTAL_ERRORS -gt 0 ]]; then
        exit 1
    fi
    exit 0
}

main "$@"
