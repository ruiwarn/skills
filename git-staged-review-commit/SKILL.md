---
name: git-staged-review-commit
description: Review staged Git changes, report issues, ask whether to fix or proceed, and if proceeding generate a Chinese commit message and commit the staged code. Use when the user wants a review of the staged diff and a commit workflow based on that review.
---

# Git Staged Review Commit

## Overview

Review staged diffs, decide whether to fix issues or proceed, and if proceeding generate a structured Chinese commit message and commit the staged changes.

## Workflow

### 1) Inspect the staged changes
- Run `git status -sb` and `git diff --staged` (or `git diff --staged --stat` first for a quick scan).
- If nothing is staged, ask the user to stage files and stop.

### 2) Review the staged diff
- Focus on bugs, behavioral regressions, missing tests, and risky changes.
- If there are findings, list them clearly with file/line references.
- If no findings, explicitly say there are none.
- Review output must be in Chinese.

### 3) Ask for a decision when issues exist
- If issues exist, ask the user: fix the issues or proceed with commit anyway.
- Wait for the user's choice before continuing.

### 4) If the user chooses to fix
- Modify the code to address the issues.
- Stage only the files you changed (e.g., `git add <paths>`), then re-review the staged diff.
- Repeat until the staged diff is clean or the user decides to proceed anyway.

### 5) If the user chooses to proceed with commit
- Generate the commit message per the rules below.
- Commit the staged changes using the generated message (do not amend unless explicitly asked).
- Confirm the commit is created and remind the user to `git push` if they want it on the remote.

## Commit Message Rules

Follow these rules exactly when generating a commit message.

### Format
1. 标题格式：`{emoji}{type}({scope}): {简洁摘要}`
2. emoji和type映射：
   - ✨feat = 新功能
   - 🐞fix = 修复bug
   - 🦄refactor = 重构代码
   - ⚙️build = 构建相关
   - 📝docs = 文档更新
   - 🎨style = 代码格式/样式调整（不影响功能）
   - ⚡perf = 性能优化
   - 🧪test = 测试相关
   - 🔧chore = 杂项维护（依赖升级、配置、工具脚本）
   - 🔁ci = CI/CD 流水线
   - ⏪revert = 回滚提交
   - 🧹cleanup = 删除/清理代码（不应引入行为变更）
3. scope：优先顶层模块/包名，其次目录名；无明显模块时使用 `core`，命名风格沿用目录/模块原样
4. 摘要：50字符以内的简洁中文描述（仅摘要文本，不含 emoji/type/scope）
5. 正文：详细列出主要变更点，每项以 `-` 开头
6. 语言：中文

### Analysis Guidance
- 仔细分析 `git diff --staged` 中的文件路径和变更内容
- 从变更内容推断功能意图和影响范围
- 选择最合适的 type 和 emoji
- 安全/依赖更新默认归类为 `chore`，流水线变更优先用 `ci`
- 无法明确归类时默认使用 `chore`
- 生成简洁但信息完整的提交消息

### Output Rule
- 当用户要求“生成提交消息”时，只输出提交消息内容本身，不要使用代码块，不要添加任何解释性文字。

## Example (for reference only)
🐞fix(print): 优化浮点数打印，提升鲁棒性

- 将 PRINTF_FLOAT 宏重构为 static inline 函数，提高类型安全和可调试性。
- 改进浮点数打印逻辑，支持负数处理及避免大数值溢出。
- 引入 int64_t 类型进行内部计算，并添加 LLONG_MAX 检查，超出范围时打印 "inf"。
- 更新 least_squares_software.c 中浮点数打印调用，使用新的 PRINTF_FLOAT 函数。
- 更新 .serena/project.yml 中的项目语言配置为 cpp。

🔧chore(deps): 升级核心依赖版本

- 升级 serde 到 1.0.197，修复已知安全问题。
- 更新 lockfile 保持版本一致性。

🔁ci(pipeline): 增加缓存与并行测试

- 为单元测试步骤增加缓存策略，缩短构建时间。
- 拆分测试为两路并行执行，提升吞吐量。

📝docs(readme): 补充本地开发说明

- 添加环境变量示例与启动步骤说明。
- 修正文档中的旧命令示例。
