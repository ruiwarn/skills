---
name: bug-fix
description: Use when the user asks to fix a bug, resolve an issue, or provides a bug URL/bug ID from 禅道, GitLab, GitHub, Jira, or similar systems; especially when the work needs a full workflow of reading the bug, fixing code, verifying, creating issue/MR, and writing status back to the tracker.
---

# Bug Fix Workflow

## Goal

Use this skill for a full bug-repair workflow, not just code changes.
It is for cases where the user wants some or all of these steps:
- 获取缺陷单内容
- 分析原因并修复代码
- 运行校验和构建
- 创建 GitLab issue / MR
- 回写禅道状态

## Before doing anything

First run:

```bash
.claude/skills/bug-fix/scripts/check_config.sh
```

If config is missing or incomplete, stop immediately and tell the user to create:

```bash
.claude/skills/bug-fix/.config
```

They can start from:

```bash
cp .claude/skills/bug-fix/.config.example .claude/skills/bug-fix/.config
```

Do not continue with API actions until config is valid.

## Files in this skill

```text
.claude/skills/bug-fix/
├── SKILL.md
├── .config.example
├── scripts/
│   ├── bugfix_flow.sh
│   ├── check_config.sh
│   ├── zentao.sh
│   └── gitlab.sh
└── templates/
    ├── issue_6d_template.md
    └── mr_template.md
```

## Scripts

### 推荐入口：主控脚本

优先使用主控脚本，减少模型自己拼步骤的机会：

```bash
.claude/skills/bug-fix/scripts/bugfix_flow.sh check-config
.claude/skills/bug-fix/scripts/bugfix_flow.sh fetch <bug_id>
.claude/skills/bug-fix/scripts/bugfix_flow.sh create-issue <bug_id> <description_file> [labels]
.claude/skills/bug-fix/scripts/bugfix_flow.sh create-mr <bug_id> <source_branch> <description_file> [target_branch]
.claude/skills/bug-fix/scripts/bugfix_flow.sh zentao-confirm <bug_id> [comment]
.claude/skills/bug-fix/scripts/bugfix_flow.sh zentao-resolve <bug_id> [comment] [assigned_to]
```

### 底层脚本

```bash
.claude/skills/bug-fix/scripts/zentao.sh get <bug_id>
.claude/skills/bug-fix/scripts/zentao.sh confirm <bug_id> [comment]
.claude/skills/bug-fix/scripts/zentao.sh resolve <bug_id> [resolution] [comment] [assigned_to]

.claude/skills/bug-fix/scripts/gitlab.sh issue create <title> <description_file> [labels]
.claude/skills/bug-fix/scripts/gitlab.sh issue get <iid>
.claude/skills/bug-fix/scripts/gitlab.sh mr create <source_branch> <title> <description_file> [target_branch]
```

Important:
- `description_file` 必须是 UTF-8 文本文件
- 不要把长 markdown 直接塞进命令行参数
- 6D issue 和 MR 描述先写文件，再调用脚本
- issue 优先参考 `templates/issue_6d_template.md`
- MR 优先参考 `templates/mr_template.md`
- `.config` 中必须配置 `PROJECT_OWNER`，用于 bug 解决后自动转派项目负责人

## Standard workflow

### 1. 读取缺陷单

优先用脚本读取禅道：

```bash
.claude/skills/bug-fix/scripts/zentao.sh get 5245
```

需要提取这些信息：
- bug 标题
- 环境信息
- 重现步骤
- 期望结果 / 实际结果
- 日志 / 报文
- 定位人 / 报告人 / 验证人

如果 bug 系统无法访问，再向用户要内容。

### 1.1 AI 自动选择 bug 根因分类

读取禅道 bug 后，AI 需要先判断一个用于回写 `browser` 字段的中文根因分类。

要求：
- 只输出**中文分类名**，不要直接输出禅道内部 code
- 优先选择最具体、最贴近实际根因的类型
- 低置信度时不要自动提交，改为让用户确认

禁止自动选择：
- 继承或历史遗留
- 未明确定位
- 非问题
- 空值

### 2. 修复代码

- 搜索相关代码
- 先读文件再改
- 只改与 bug 直接相关的内容
- 所有新增或修改的函数，按项目要求补中文注释

### 3. 验证

必须先验证再宣称完成：

```bash
# C检查
c-verify-skill

# 构建
ninja.exe -C build || ninja -C build
```

### 4. 创建 GitLab issue

Issue 内容使用 6D 风格，优先按 `templates/issue_6d_template.md` 填写，至少包含：

1. 禅道链接
2. Bug描述（环境、步骤、期望、实际、日志）
3. Bug原因分析（根因、直接原因、问题代码位置、为什么之前没发现、责任检讨）
4. 解决方案（修复思路、修改点、为什么这样修、副作用评估）
5. 验证结果（静态检查、构建、自测）
6. 给测试人员的黑盒测试建议（前置条件、操作步骤、预期结果、判定标准、边界项、回归项）
7. 后续改进方案
8. 责任人（报告人、定位人、修复人、验证人、项目负责人）

先把内容写到 markdown 文件，再创建：

```bash
.claude/skills/bug-fix/scripts/gitlab.sh issue create \
  "Bug #5245: 标题" \
  /tmp/issue_5245.md \
  "bug,645协议,拓扑识别"
```

### 5. Git 分支与提交

只有在用户确认后，才创建分支 / MR。

推荐流程：

```bash
git checkout -b bugfix/<bug_id>-short-desc develop
git add <modified files>
git commit

git push -u origin bugfix/<bug_id>-short-desc
```

提交时：
- 只提交本次修复相关文件
- 不要顺手带入无关修改
- commit message 要能说明 bug、原因、方案

### 6. 创建 MR

同样先把 MR 描述写入 markdown 文件，再创建：

```bash
.claude/skills/bug-fix/scripts/gitlab.sh mr create \
  "bugfix/5245-short-desc" \
  "Bugfix #5245: 标题" \
  /tmp/mr_5245.md \
  develop
```

MR 描述至少包含：
- 修复内容
- 修改文件
- 验证结果
- 禅道链接
- GitLab issue 链接
- 责任人

### 7. 回写禅道

```bash
.claude/skills/bug-fix/scripts/zentao.sh confirm <bug_id> "附 issue 链接的说明"
.claude/skills/bug-fix/scripts/zentao.sh set-browser-type <bug_id> "设计_边界值设计问题"
.claude/skills/bug-fix/scripts/zentao.sh resolve <bug_id> fixed "附 MR 链接的说明" "" "设计_边界值设计问题"
```

说明：
- `resolve` 默认会把 Bug 转派给 `.config` 中的 `PROJECT_OWNER`
- 如需临时覆盖负责人，可追加第四个参数 `assigned_to`
- 第五个参数 `bug_type` 传 AI 判断出的中文分类名，脚本会自动映射到禅道 `browser` 字段；命中黑名单会直接拒绝提交
- `set-browser-type` 可单独补写 bug 分类
- 不要再默认转回 Bug 提出人

## Hard rules

1. 没有有效 `.config`，不要继续 API 操作
2. 没有用户确认，不要创建分支、推送、MR
3. 没有验证通过，不要说“已完成”
4. issue / MR 长描述必须走文件，不要直接拼命令行字符串
5. 只提交与当前 bug 相关的改动
6. 禅道回写内容要带 GitLab issue / MR 链接
