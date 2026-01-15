# 芯片手册 Skill 模板

用于快速创建芯片手册查询 Skill，让 AI 能准确查询寄存器位定义、接口时序等技术信息。

## 快速开始

### 方法一：使用脚本自动创建

```bash
cd ~/.claude/skills/chip_manual_template

# 创建新的芯片 Skill
./setup_skill.sh <芯片名称> <芯片描述> <PDF路径>

# 示例
./setup_skill.sh STM32F103 "ARM Cortex-M3 MCU" ~/docs/stm32f103_rm.pdf
./setup_skill.sh ESP32 "WiFi+BT SoC" ~/docs/esp32_trm.pdf
```

### 方法二：手动创建

1. **复制模板目录**
   ```bash
   cp -r chip_manual_template my_chip_manual
   ```

2. **放入手册文件**
   ```bash
   cp your_chip_manual.pdf my_chip_manual/references/manual.pdf
   ```

3. **转换 PDF 为 Markdown**
   ```bash
   # 推荐使用 marker（效果最好）
   pip install marker-pdf
   marker manual.pdf ./ --output_format md

   # 或使用 pdftotext
   pdftotext -layout manual.pdf manual.md
   ```

4. **生成寄存器索引**
   ```bash
   python3 generate_index.py references/manual.md
   ```

5. **编辑 SKILL.md**
   - 替换 `{{CHIP_NAME}}` 为芯片名称
   - 替换 `{{CHIP_DESC}}` 为芯片描述
   - 调整触发关键词

---

## 文件结构

```
your_chip_manual/
├── SKILL.md                    # Skill 定义文件
└── references/
    ├── index.md                # 主索引（章节目录）
    ├── register_index.md       # 寄存器快速索引（自动生成）
    ├── manual.md               # 手册正文（从PDF转换）
    └── manual.pdf              # 原始PDF
```

---

## 模板文件说明

| 文件 | 说明 |
|------|------|
| `SKILL.md.template` | Skill 定义模板 |
| `references/index.md.template` | 索引模板 |
| `generate_index.py` | 寄存器索引生成脚本 |
| `setup_skill.sh` | 一键创建脚本 |

---

## 占位符说明

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{{CHIP_NAME}}` | 芯片名称 | STM32F103, ESP32 |
| `{{CHIP_DESC}}` | 芯片描述 | ARM Cortex-M3 MCU |
| `{{MAIN_FEATURE}}` | 主要功能 | 计量算法、无线通信 |
| `{{CHIP_KEYWORDS}}` | 触发关键词 | STM32, F103 |
| `{{TRIGGER_KEYWORDS}}` | 功能关键词 | ADC、定时器、DMA |

---

## PDF 转换工具推荐

| 工具 | 优点 | 缺点 |
|------|------|------|
| [marker](https://github.com/VikParuchuri/marker) | 表格识别好，保留结构 | 需要 GPU 效果更好 |
| pdftotext | 简单快速 | 表格支持差 |
| [pdf2md](https://github.com/jzillmann/pdf-to-markdown) | 开源免费 | 复杂布局可能有问题 |
| Adobe Acrobat | 效果好 | 需付费 |

---

## 注意事项

1. **PDF 质量很重要** - 扫描版 PDF 效果会比较差
2. **表格转换** - 确保寄存器表格正确转换，否则需要手动调整
3. **编码问题** - 确保 markdown 文件为 UTF-8 编码
4. **文件大小** - 如果 manual.md 超过 1MB，建议用增强索引方案
