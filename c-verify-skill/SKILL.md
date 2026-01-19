---
name: c-verify-skill
description: Run C/C++ static analysis on code changes using clang-tidy and cppcheck. Use when user asks to scan code, check code quality, static analysis, verify C code, check staged files, scan staged code, lint C files, find bugs in code, or review code before commit.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# C/C++ 静态分析工具

## 概述

本 Skill 提供完整的 C/C++ 静态分析能力，集成 clang-tidy 和 cppcheck 两大主流工具，支持：

- **Git 集成**: 自动检查暂存/修改的文件
- **批量分析**: 支持目录级别扫描
- **多种输出格式**: text、markdown、json
- **智能过滤**: 可配置忽略规则，减少噪音
- **汇总报告**: 清晰的问题统计和文件排名

## 快速开始

### 检查 Git 暂存的文件（推荐用于提交前检查）

```bash
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --project-root /path/to/project
```

### 检查所有已修改的文件

```bash
$SKILL_DIR/scripts/run_c_checks.sh --git-modified --project-root /path/to/project
```

### 检查单个文件

```bash
$SKILL_DIR/scripts/run_c_checks.sh -f code/APP/main.c --project-root /path/to/project
```

### 检查整个目录

```bash
$SKILL_DIR/scripts/run_c_checks.sh -d code/APP --project-root /path/to/project
```

## 完整参数说明

### 文件选择

| 参数 | 说明 |
|------|------|
| `-f, --file <file>` | 检查单个文件 |
| `-d, --directory <dir>` | 检查目录下所有 C/C++ 文件 |
| `--git-staged` | 检查 git 暂存的文件 |
| `--git-modified` | 检查 git 已修改的文件（包括未暂存） |
| `--git-all` | 检查所有 git 变更的文件 |
| `--project-root <dir>` | 项目根目录（**调用方必须传入**，用于支持 skill 不在工程内的场景） |

### 工具配置

| 参数 | 说明 |
|------|------|
| `-p, --compdb <dir>` | compile_commands.json 所在目录（默认自动检测） |
| `--checks <pattern>` | clang-tidy 检查规则（默认: `bugprone-*,clang-analyzer-*`） |
| `--header-filter <regex>` | clang-tidy 头文件过滤正则 |
| `--skip-cppcheck` | 跳过 cppcheck 检查 |
| `--skip-clang-tidy` | 跳过 clang-tidy 检查 |

### 输出控制

| 参数 | 说明 |
|------|------|
| `--format <type>` | 输出格式: `text`（默认）、`markdown`、`json` |
| `--severity <level>` | 严重程度过滤: `error`、`warning`、`all`（默认） |
| `--ignore <pattern>` | 忽略的警告类型（可多次使用） |
| `--summary` | 只显示汇总统计，不显示详细问题 |
| `-q, --quiet` | 静默模式 |

## 使用示例

### 1. 提交前检查（推荐流程）

```bash
# 只检查即将提交的代码
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --severity error --project-root /path/to/project

# 如果有错误，脚本返回非零退出码
```

### 2. 生成 Markdown 报告

```bash
$SKILL_DIR/scripts/run_c_checks.sh --git-modified --format markdown --project-root /path/to/project > report.md
```

### 3. 只看严重错误

```bash
$SKILL_DIR/scripts/run_c_checks.sh -d code/APP --severity error --project-root /path/to/project
```

### 4. 忽略特定警告

```bash
$SKILL_DIR/scripts/run_c_checks.sh --git-modified \
    --ignore "reserved-identifier" \
    --ignore "easily-swappable-parameters" \
    --project-root /path/to/project
```

### 5. 只看汇总统计

```bash
$SKILL_DIR/scripts/run_c_checks.sh -d code/ --summary --project-root /path/to/project
```

### 6. JSON 格式输出（供 CI/CD 使用）

```bash
$SKILL_DIR/scripts/run_c_checks.sh --git-all --format json --project-root /path/to/project > results.json
```

## 配置文件

工具支持通过 `config.json` 进行项目级配置：

```json
{
    "clang_tidy_checks": "bugprone-*,clang-analyzer-*",
    "header_filter": "^.*/code/.*",
    "ignore_checks": [
        "bugprone-reserved-identifier",
        "bugprone-easily-swappable-parameters"
    ],
    "exclude_directories": [
        "drivers/",
        "Output/"
    ]
}
```

配置文件位于: `$SKILL_DIR/config.json`

### 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `clang_tidy_checks` | string | clang-tidy 检查规则 |
| `header_filter` | string | 头文件过滤正则 |
| `ignore_checks` | array | 忽略的检查项（部分匹配） |
| `exclude_directories` | array | 排除的目录 |

## 输出格式示例

### Text 格式（默认）

```
C/C++ 静态分析
检查 5 个文件...

检查: code/APP/main.c
[ERROR] code/APP/main.c:48: | has lower precedence than == [clang-diagnostic-parentheses]
[WARN] code/APP/main.c:33: 2 adjacent parameters easily swapped [bugprone-easily-swappable-parameters]

═══════════════════════════════════════════════════════════
                    静态分析汇总报告
═══════════════════════════════════════════════════════════

  错误 (Errors):    1
  警告 (Warnings):  15
  提示 (Info):      3
  总计:             19

问题文件统计:
  - code/APP/main.c: 5 个问题
  - code/APP/rn7326_app.c: 8 个问题

✗ 发现严重错误，请立即修复！
```

### Markdown 格式

适合生成报告或嵌入文档：

```markdown
# C/C++ 静态分析报告

检查文件数: 5

## 详细问题列表

| 级别 | 文件 | 行号 | 描述 | 检查项 |
|------|------|------|------|--------|
| 🔴 | `main.c` | 48 | precedence issue | `clang-diagnostic-parentheses` |
| 🟡 | `main.c` | 33 | swappable params | `bugprone-easily-swappable-parameters` |

## 静态分析汇总

| 类型 | 数量 |
|------|------|
| 🔴 错误 | 1 |
| 🟡 警告 | 15 |
| 🔵 提示 | 3 |
| **总计** | **19** |
```

### JSON 格式

适合 CI/CD 集成和程序化处理。

## 前置要求

### 必需工具

- **clang-tidy**: LLVM 静态分析工具
- **cppcheck**: C/C++ 静态分析工具
- **jq**: JSON 处理工具（用于读取配置文件，可选）

### 安装方法

Ubuntu/Debian:
```bash
sudo apt install clang-tidy cppcheck jq
```

macOS:
```bash
brew install llvm cppcheck jq
```

### compile_commands.json

clang-tidy 需要编译数据库。本项目使用 Keil，需运行生成脚本：

```bash
./env/generate_compile_commands.sh
```

工具会自动在以下位置查找：
1. `./compile_commands.json`
2. `./env/compile_commands.json`
3. `./build/compile_commands.json`

## 常见问题

### Q: 为什么有很多 "reserved-identifier" 警告？

A: 这是因为头文件保护宏使用了下划线开头的命名（如 `_APP_H`）。在 C 标准中这是保留标识符。可以通过配置忽略：

```bash
--ignore "reserved-identifier"
```

或在 `config.json` 中添加到 `ignore_checks`。

### Q: 如何只检查项目代码，不检查第三方库？

A: 使用 `--header-filter` 限制头文件范围：

```bash
--header-filter '^.*/code/.*'
```

### Q: clang-tidy 报告缺少头文件？

A: 确保 `compile_commands.json` 是最新的：

```bash
./env/generate_compile_commands.sh
```

### Q: 如何集成到 Git Hook？

A: 在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/bash
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --severity error
```

## 目录结构

```
$SKILL_DIR/
├── SKILL.md              # 本文档
├── config.json           # 项目配置
├── config.schema.json    # 配置文件 Schema
└── scripts/
    └── run_c_checks.sh   # 主脚本
```

## 更新日志

### v2.0.0

- 新增 Git 集成（`--git-staged`, `--git-modified`, `--git-all`）
- 新增目录批量检查（`-d`）
- 新增多种输出格式（text, markdown, json）
- 新增配置文件支持
- 新增严重程度过滤
- 新增汇总报告
- 优化 cppcheck 参数，减少噪音
- 修复路径问题

### v1.0.0

- 初始版本，支持单文件检查
