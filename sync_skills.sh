#!/bin/bash

# ========================================
# Skills 同步脚本
# ========================================
# 功能：将当前目录下的所有 skill 文件夹同步到指定的目标目录
# 用法：./sync_skills.sh
# ========================================

# 不使用 set -e，手动处理错误以更好地控制流程

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取脚本所在目录（源目录）
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 目标目录列表（方便添加或删除）
TARGET_DIRS=(
    "/mnt/c/Users/candy/.claude/skills"
    "/mnt/c/Users/candy/.codex/skills"
    "$HOME/.codex/skills"
)

# 排除列表（不复制这些文件/目录）
EXCLUDE_PATTERNS=(
    ".git"
    ".gitignore"
    ".DS_Store"
    "node_modules"
    "__pycache__"
    "*.pyc"
    ".vscode"
    ".idea"
    ".claude"
    ".system"
    "sync_skills.sh"  # 排除脚本自身
)

# ========================================
# 函数：打印带颜色的消息
# ========================================
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ========================================
# 函数：构建 rsync 排除参数
# ========================================
build_exclude_args() {
    local exclude_args=""
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        exclude_args="$exclude_args --exclude=$pattern"
    done
    echo "$exclude_args"
}

# ========================================
# 函数：同步到单个目标目录
# ========================================
sync_to_target() {
    local target_dir="$1"

    echo ""
    echo "========================================"
    print_info "处理目标目录 $((current_index))/${#TARGET_DIRS[@]}: $target_dir"
    echo "========================================"

    # 创建目标目录（如果不存在）
    if [ ! -d "$target_dir" ]; then
        print_warn "目标目录不存在，正在创建: $target_dir"
        mkdir -p "$target_dir"
    fi

    # 检查目标目录是否有内容
    if [ "$(ls -A "$target_dir" 2>/dev/null)" ]; then
        echo ""
        print_warn "目标目录中现有内容:"
        echo "----------------------------------------"
        # 显示所有文件和目录，包括隐藏的
        ls -1A "$target_dir" 2>/dev/null || echo "  (空目录)"
        echo "----------------------------------------"
        echo ""

        # 询问是否删除，默认为 Y
        # 使用 </dev/tty 确保从终端读取输入
        read -p "确认删除以上所有内容？[Y/n] " -r </dev/tty
        echo ""

        # 如果用户输入 n 或 N，则跳过这个目录
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            print_warn "跳过目录: $target_dir"
            return 1
        fi

        # 清空目标目录
        print_info "清空目标目录..."
        rm -rf "$target_dir"/*
        rm -rf "$target_dir"/.[!.]*  # 删除隐藏文件，但保留 . 和 ..
    else
        print_info "目标目录为空，无需清空"
    fi

    # 使用 rsync 同步
    local exclude_args=$(build_exclude_args)
    print_info "复制 skills..."

    # 使用 eval 来正确处理排除参数
    # 使用临时文件捕获输出，避免管道问题
    local temp_output=$(mktemp)
    eval rsync -a --delete \
        $exclude_args \
        "$SOURCE_DIR/" \
        "$target_dir/" > "$temp_output" 2>&1

    local rsync_exit_code=$?

    # 显示简要信息
    if [ -s "$temp_output" ]; then
        grep -E "(sending|sent|total)" "$temp_output" 2>/dev/null || true
    fi
    rm -f "$temp_output"

    if [ $rsync_exit_code -eq 0 ]; then
        print_info "✓ 同步完成: $target_dir"
        echo ""
        return 0
    else
        print_error "✗ 同步失败: $target_dir (退出码: $rsync_exit_code)"
        echo ""
        return 1
    fi
}

# ========================================
# 主程序
# ========================================
main() {
    echo "========================================"
    echo "       Skills 同步工具"
    echo "========================================"
    echo ""

    print_info "源目录: $SOURCE_DIR"
    echo ""

    # 确认源目录中有 skill 文件夹
    skill_count=$(find "$SOURCE_DIR" -maxdepth 1 -type d ! -name ".*" ! -path "$SOURCE_DIR" | wc -l)
    print_info "找到 $skill_count 个 skill 目录"
    echo ""

    # 显示将要同步的目标目录
    print_info "目标目录:"
    for target_dir in "${TARGET_DIRS[@]}"; do
        echo "  - $target_dir"
    done
    echo ""

    # 询问用户确认（默认为 Y）
    read -p "确认开始同步？[Y/n] " -r
    echo ""

    # 如果用户输入 n 或 N，则取消；其他情况（包括空回车）都继续
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_warn "用户取消操作"
        exit 0
    fi

    echo ""

    # 执行同步
    success_count=0
    fail_count=0
    current_index=1

    print_info "开始处理 ${#TARGET_DIRS[@]} 个目标目录..."

    for target_dir in "${TARGET_DIRS[@]}"; do
        if sync_to_target "$target_dir"; then
            success_count=$((success_count + 1))
            print_info ">>> 已完成 $current_index/${#TARGET_DIRS[@]} 个目录"
        else
            fail_count=$((fail_count + 1))
            print_warn ">>> 已处理 $current_index/${#TARGET_DIRS[@]} 个目录 (本次失败)"
        fi
        current_index=$((current_index + 1))
    done

    print_info "所有目录处理完毕"

    # 显示总结
    echo "========================================"
    echo "              同步完成"
    echo "========================================"
    print_info "成功: $success_count 个目录"

    if [ $fail_count -gt 0 ]; then
        print_error "失败: $fail_count 个目录"
        exit 1
    fi

    echo ""
    print_info "所有 skills 已同步完成！"
}

# 运行主程序
main
