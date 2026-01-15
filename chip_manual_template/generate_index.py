#!/usr/bin/env python3
"""
芯片手册 Skill 索引生成脚本

用法:
    python3 generate_index.py [manual.md路径] [模块名称映射文件(可选)]

功能:
    1. 从 manual.md 提取所有寄存器定义（地址、名称、行号）
    2. 生成 register_index.md 寄存器快速索引
    3. 提取章节目录

示例:
    cd /path/to/your_chip_skill/references
    python3 ../generate_index.py manual.md
"""

import re
import sys
from collections import defaultdict
from pathlib import Path


def extract_registers(lines):
    """提取寄存器信息"""
    registers = []
    # 匹配模式: 章节号 + 寄存器名 + (0x地址)
    pattern = r'^#*\s*(\d+\.\d+\.?\d*\.?\d*)\s+(.+?)[（(](0x[0-9A-Fa-f]+)'

    for i, line in enumerate(lines, 1):
        match = re.search(pattern, line)
        if match:
            section = match.group(1)
            name = match.group(2).strip()
            addr = match.group(3).upper()
            # 清理名称
            name = re.sub(r'\s+', ' ', name)
            name = name.replace('.....', '').replace('...', '').strip()
            registers.append({
                'line': i,
                'section': section,
                'name': name,
                'addr': addr,
                'module': section.split('.')[0]
            })

    return registers


def extract_chapters(lines):
    """提取章节信息"""
    chapters = []
    chapter_pattern = r'^#\s+(\d+)\s+(.+?)(?:\s*\.{3,}.*)?$'

    for i, line in enumerate(lines, 1):
        match = re.search(chapter_pattern, line)
        if match:
            num = match.group(1)
            title = match.group(2).strip()
            try:
                if int(num) <= 50:  # 只取主要章节
                    chapters.append({
                        'line': i,
                        'num': num,
                        'title': title
                    })
            except ValueError:
                pass

    return chapters


def generate_index(registers, chapters, module_names=None):
    """生成索引内容"""
    if module_names is None:
        module_names = {}

    output = []
    output.append("# 寄存器快速索引")
    output.append("")
    output.append(f"> 自动生成，共 {len(registers)} 个寄存器定义")
    output.append("> 使用方法：找到寄存器行号后，用 `Read(offset=行号-10, limit=80)` 读取详细信息")
    output.append("")
    output.append("---")
    output.append("")

    # 章节目录
    if chapters:
        output.append("## 📑 章节目录")
        output.append("")
        output.append("| 章节 | 标题 | 行号 |")
        output.append("|------|------|------|")
        for ch in chapters[:35]:
            output.append(f"| {ch['num']} | {ch['title'][:35]} | {ch['line']} |")
        output.append("")

    # 按模块分组
    modules = defaultdict(list)
    for reg in registers:
        modules[reg['module']].append(reg)

    output.append("---")
    output.append("")
    output.append("## 📋 寄存器索引（按模块）")
    output.append("")

    sorted_modules = sorted(modules.keys(), key=lambda x: int(x) if x.isdigit() else 999)

    for mod in sorted_modules:
        mod_name = module_names.get(mod, f'模块 {mod}')
        regs = modules[mod]
        if regs:
            output.append(f"### {mod}. {mod_name}")
            output.append("")
            output.append("| 地址 | 寄存器名 | 行号 |")
            output.append("|------|----------|------|")
            for reg in regs[:60]:
                name = reg['name'][:40] if len(reg['name']) > 40 else reg['name']
                output.append(f"| {reg['addr']} | {name} | {reg['line']} |")
            if len(regs) > 60:
                output.append(f"| ... | （共 {len(regs)} 个） | ... |")
            output.append("")

    # 地址快查表
    output.append("---")
    output.append("")
    output.append("## 🔍 地址快查表（前100个）")
    output.append("")
    output.append("| 地址 | 寄存器 | 模块 | 行号 |")
    output.append("|------|--------|------|------|")

    def addr_to_int(addr):
        try:
            return int(addr, 16)
        except:
            return 0

    sorted_regs = sorted(registers, key=lambda x: addr_to_int(x['addr']))
    for reg in sorted_regs[:100]:
        mod_name = module_names.get(reg['module'], reg['module'])[:12]
        name = reg['name'][:25] if len(reg['name']) > 25 else reg['name']
        output.append(f"| {reg['addr']} | {name} | {mod_name} | {reg['line']} |")

    output.append("")
    output.append(f"> 完整列表共 {len(registers)} 个寄存器")

    return '\n'.join(output)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 generate_index.py <manual.md路径>")
        print("示例: python3 generate_index.py references/manual.md")
        sys.exit(1)

    manual_path = Path(sys.argv[1])
    if not manual_path.exists():
        print(f"错误: 文件不存在 - {manual_path}")
        sys.exit(1)

    print(f"正在处理: {manual_path}")

    # 读取文件
    with open(manual_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"  文件行数: {len(lines)}")

    # 提取信息
    registers = extract_registers(lines)
    chapters = extract_chapters(lines)

    print(f"  找到寄存器: {len(registers)} 个")
    print(f"  找到章节: {len(chapters)} 个")

    # 生成索引
    content = generate_index(registers, chapters)

    # 写入文件
    output_path = manual_path.parent / 'register_index.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已生成: {output_path}")


if __name__ == '__main__':
    main()
