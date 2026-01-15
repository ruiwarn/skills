#!/bin/bash
#
# 芯片手册 Skill 创建脚本
#
# 用法:
#   ./setup_skill.sh <芯片名称> <芯片描述> <PDF路径>
#
# 示例:
#   ./setup_skill.sh STM32F103 "ARM Cortex-M3 MCU" ~/docs/stm32f103_rm.pdf
#
# 前提条件:
#   1. 安装 marker 或其他 PDF 转 MD 工具
#   2. Python3

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -lt 3 ]; then
    echo -e "${RED}用法: $0 <芯片名称> <芯片描述> <PDF路径>${NC}"
    echo ""
    echo "示例:"
    echo "  $0 STM32F103 'ARM Cortex-M3 MCU' ~/docs/stm32f103_rm.pdf"
    echo "  $0 ESP32 'WiFi+BT SoC' ~/docs/esp32_trm.pdf"
    exit 1
fi

CHIP_NAME="$1"
CHIP_DESC="$2"
PDF_PATH="$3"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")"

# 目标目录
TARGET_DIR="${SKILLS_DIR}/${CHIP_NAME,,}_manual"

echo -e "${GREEN}=== 芯片手册 Skill 创建工具 ===${NC}"
echo ""
echo "芯片名称: $CHIP_NAME"
echo "芯片描述: $CHIP_DESC"
echo "PDF路径: $PDF_PATH"
echo "目标目录: $TARGET_DIR"
echo ""

# 检查 PDF 文件
if [ ! -f "$PDF_PATH" ]; then
    echo -e "${RED}错误: PDF 文件不存在 - $PDF_PATH${NC}"
    exit 1
fi

# 创建目录
echo -e "${YELLOW}[1/5] 创建目录结构...${NC}"
mkdir -p "$TARGET_DIR/references"

# 复制 PDF
echo -e "${YELLOW}[2/5] 复制 PDF 文件...${NC}"
cp "$PDF_PATH" "$TARGET_DIR/references/manual.pdf"

# 转换 PDF 到 MD
echo -e "${YELLOW}[3/5] 转换 PDF 到 Markdown...${NC}"
echo "  (这一步可能需要较长时间...)"

# 检查是否安装了 marker
if command -v marker &> /dev/null; then
    marker "$TARGET_DIR/references/manual.pdf" "$TARGET_DIR/references/" --output_format md
    # marker 输出文件名可能不同，需要重命名
    if [ -f "$TARGET_DIR/references/manual/manual.md" ]; then
        mv "$TARGET_DIR/references/manual/manual.md" "$TARGET_DIR/references/manual.md"
        rm -rf "$TARGET_DIR/references/manual"
    fi
elif command -v pdftotext &> /dev/null; then
    echo "  使用 pdftotext 转换（质量可能较低）"
    pdftotext -layout "$TARGET_DIR/references/manual.pdf" "$TARGET_DIR/references/manual.md"
else
    echo -e "${RED}警告: 未找到 PDF 转换工具${NC}"
    echo "  请手动将 PDF 转换为 manual.md"
    echo "  推荐工具: marker, pdftotext, 或在线转换工具"
    touch "$TARGET_DIR/references/manual.md"
fi

# 生成寄存器索引
echo -e "${YELLOW}[4/5] 生成寄存器索引...${NC}"
if [ -s "$TARGET_DIR/references/manual.md" ]; then
    python3 "$SCRIPT_DIR/generate_index.py" "$TARGET_DIR/references/manual.md"
else
    echo "  跳过（manual.md 为空）"
    touch "$TARGET_DIR/references/register_index.md"
fi

# 生成 SKILL.md
echo -e "${YELLOW}[5/5] 生成 SKILL.md...${NC}"
SKILL_NAME="${CHIP_NAME,,}-manual"  # 转换为小写并添加 -manual 后缀
sed -e "s/{{CHIP_NAME}}/$CHIP_NAME/g" \
    -e "s/{{SKILL_NAME}}/$SKILL_NAME/g" \
    -e "s/{{CHIP_DESC}}/$CHIP_DESC/g" \
    -e "s/{{MAIN_FEATURE}}/核心功能/g" \
    -e "s/{{CHIP_KEYWORDS}}/$CHIP_NAME/g" \
    -e "s/{{TRIGGER_KEYWORDS}}/功能特性/g" \
    "$SCRIPT_DIR/SKILL.md.template" > "$TARGET_DIR/SKILL.md"

# 生成 index.md
sed -e "s/{{CHIP_NAME}}/$CHIP_NAME/g" \
    "$SCRIPT_DIR/references/index.md.template" > "$TARGET_DIR/references/index.md"

echo ""
echo -e "${GREEN}=== 完成 ===${NC}"
echo ""
echo "已创建 Skill 目录: $TARGET_DIR"
echo ""
echo "文件列表:"
ls -la "$TARGET_DIR"
echo ""
ls -la "$TARGET_DIR/references"
echo ""
echo -e "${YELLOW}后续步骤:${NC}"
echo "1. 检查 manual.md 转换质量"
echo "2. 编辑 SKILL.md 调整触发关键词"
echo "3. 编辑 index.md 添加常用寄存器速查"
echo "4. 测试 skill 是否正常工作"
