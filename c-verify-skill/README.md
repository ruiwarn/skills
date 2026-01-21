---
name: c-verify-skill
description: Run C/C++ static analysis on code changes using clang-tidy and cppcheck. Use when user asks to scan code, check code quality, static analysis, verify C code, check staged files, scan staged code, lint C files, find bugs in code, or review code before commit.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# C/C++ 静态分析工具（AI优化版）

## 核心功能

本 Skill 专为 AI 使用设计，提供结构化的 C/C++ 静态分析结果。输出格式为机器友好的 JSON，便于 AI 快速解析和生成建议。

**默认行为：输出结构化 JSON**

## AI 使用指南

### 1. 典型使用场景

当用户请求以下操作时，使用本 skill：
- "检查代码质量"
- "扫描代码问题"
- "运行静态分析"
- "检查提交前的代码"
- "找出代码中的bug"

### 2. 推荐调用方式

```bash
# 检查git暂存的文件（提交前检查）
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --project-root /path/to/project

# 检查所有已修改的文件
$SKILL_DIR/scripts/run_c_checks.sh --git-modified --project-root /path/to/project

# 检查单个文件
$SKILL_DIR/scripts/run_c_checks.sh -f code/APP/main.c --project-root /path/to/project

# 检查整个目录
$SKILL_DIR/scripts/run_c_checks.sh -d code/APP --project-root /path/to/project
```

**重要**：必须传入 `--project-root` 参数，指定项目根目录。

### 3. JSON 输出格式

工具默认输出结构化 JSON，包含五个主要部分：

```json
{
  "summary": {
    "files_checked": 5,
    "errors": 1,
    "warnings": 8,
    "info": 1,
    "total": 9,
    "priority": "medium"
  },
  "issues_by_check": {
    "bugprone-macro-parentheses": {"count": 7},
    "clang-diagnostic-macro-redefined": {"count": 1}
  },
  "issues": [
    {
      "file": "code/APP/main.c",
      "line": 48,
      "severity": "error",
      "message": "| has lower precedence than ==",
      "check": "clang-diagnostic-parentheses"
    },
    {
      "file": "code/HDL/xTarget.h",
      "line": 138,
      "severity": "warning",
      "message": "macro argument should be enclosed in parentheses",
      "check": "bugprone-macro-parentheses"
    }
  ],
  "global_issues": [
    {
      "severity": "info",
      "message": "Too many #ifdef configurations - cppcheck only checks 12",
      "check": "toomanyconfigs"
    }
  ],
  "top_files": [
    {"file": "code/HDL/xTarget.h", "issue_count": 4},
    {"file": "code/APP/main.c", "issue_count": 3}
  ]
}
```

#### 字段说明

**summary**: 统计信息
- `files_checked`: 检查的文件数量
- `errors`: 严重错误数（需立即修复）
- `warnings`: 警告数（建议修复）
- `info`: 提示数（可选优化）
- `total`: 问题总数
- `priority`: 优先级 (`high` - 有错误, `medium` - 警告>5, `low` - 其他)

**issues_by_check**: 按检查项分组统计（用于快速识别相同类型问题）
- `<check-name>`: 检查项名称
  - `count`: 该类型问题的数量

**issues**: 详细问题列表
- `file`: 文件路径（**相对于项目根目录**，节省token）
- `line`: 行号
- `severity`: 严重程度（error/warning/note 或 info）
- `message`: 问题描述
- `check`: 检查规则名称

**global_issues**: 全局问题（不属于特定文件的提示，如工具配置警告）
- `severity`: 严重程度
- `message`: 问题描述
- `check`: 检查规则名称

**top_files**: 问题最多的文件（最多10个）
- `file`: 文件路径（相对路径）
- `issue_count`: 该文件的问题数量

### 4. AI 处理建议

解析 JSON 后，AI 应该：

1. **根据 priority 快速判断**：
   - `high`: 立即提示用户必须修复错误
   - `medium`: 建议修复警告
   - `low`: 可选优化

2. **利用 issues_by_check 分组**：相同类型的问题一起展示，给出统一的修复方案
   - 例如：发现 7 处 `bugprone-macro-parentheses`，统一说明宏参数需要加括号

3. **优先处理 errors**：先展示错误级别的问题，这些必须修复

4. **关注热点文件**：使用 `top_files` 识别问题集中的文件，建议优先重构

5. **分离全局问题**：`global_issues` 通常是工具配置提示，可以最后展示或忽略

**示例响应模板**：

```
分析完成！优先级：中等 (0个错误，8个警告)

🟡 主要问题类型：
- bugprone-macro-parentheses (7处) - 宏参数缺少括号保护
- clang-diagnostic-macro-redefined (1处) - 宏重复定义

问题最多的文件：
- code/HDL/xTarget.h (4个问题) - 建议优先修复

详细建议：
1. xTarget.h 的宏定义需要为参数添加括号，避免运算符优先级问题
2. Drive_Lib.h:35 的 DL698_METER 宏重复定义，添加条件编译保护

ℹ️ 全局提示：cppcheck 配置过多，可忽略
```

### 5. 可用参数

#### 文件选择
- `--git-staged`: 检查暂存的文件（推荐用于提交前）
- `--git-modified`: 检查已修改的文件
- `--git-all`: 检查所有变更的文件
- `-f <file>`: 检查单个文件
- `-d <dir>`: 检查整个目录

#### 过滤选项
- `--severity error`: 只显示错误级别问题
- `--ignore <pattern>`: 忽略特定检查项（可多次使用）

#### 输出控制
- `--format text`: 使用人类可读格式（调试用）
- `--format markdown`: 生成 Markdown 报告（文档用）
- `--format json`: JSON 格式（默认，AI 推荐）

### 6. 错误处理

- **退出码 1**：发现严重错误（errors > 0）
- **退出码 0**：无错误或只有警告
- **退出码 2**：参数错误或工具未安装

如果遇到错误，检查：
1. `--project-root` 是否正确
2. `compile_commands.json` 是否存在
3. clang-tidy 和 cppcheck 是否已安装

### 7. 配置文件

工具从 `$SKILL_DIR/config.json` 读取默认配置：

```json
{
  "clang_tidy_checks": "bugprone-*,clang-analyzer-*",
  "header_filter": "^.*/code/.*",
  "ignore_checks": [
    "bugprone-reserved-identifier",
    "bugprone-easily-swappable-parameters"
  ],
  "exclude_directories": ["drivers/", "Output/", "boot/"]
}
```

配置会影响所有分析，AI 一般不需要关心，除非用户明确要求修改。

## 工具要求

- **clang-tidy**: LLVM 静态分析工具
- **cppcheck**: C/C++ 静态分析工具
- **compile_commands.json**: 编译数据库（clang-tidy 需要）

如果缺少工具，脚本会给出警告但继续运行可用的检查器。

## 快速参考

```bash
# 提交前检查（最常用）
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --project-root /path/to/project

# 只看错误
$SKILL_DIR/scripts/run_c_checks.sh --git-staged --severity error --project-root /path/to/project

# 忽略特定警告
$SKILL_DIR/scripts/run_c_checks.sh --git-modified \
    --ignore "reserved-identifier" \
    --ignore "easily-swappable-parameters" \
    --project-root /path/to/project

# 检查特定文件
$SKILL_DIR/scripts/run_c_checks.sh -f src/main.c --project-root /path/to/project
```

## 典型工作流程

1. 用户请求代码检查
2. AI 调用 skill，使用 `--git-staged` 或 `--git-modified`
3. 解析 JSON 输出
4. 按严重程度排序并分组展示问题
5. 提供针对性的修复建议
6. 如果有严重错误，建议用户修复后再提交

---

**设计原则**：简洁、结构化、AI友好，最小化人工解析成本。
