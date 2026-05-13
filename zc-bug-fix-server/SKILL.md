---
name: zc-bug-fix
description: Server-side automated bug fix triggered by n8n. Analyzes ZenTao bug, fixes code, commits, writes Issue/MR description files.
---

# zc-bug-fix — 服务器无人值守修复

n8n 触发，不交互，不提问，不等待确认。

## 执行步骤（严格顺序）

1. 读取 `/tmp/bug-{id}.json` — 格式：`{"status","zentao_url","bug":{...}}`，`bug.steps` 含图片绝对 URL 可直接 WebFetch
2. 分析代码，定位根因，修复代码
3. 自测验证（扫描项目内相关测试并运行）
4. `git add <相关文件>` — 禁止 `git add .`
5. `git commit -m "fix(bug#<id>): <简要描述>"`
6. 读取模板 `cat $SKILL_DIR/templates/issue_6d_template.md`，严格按格式写入 `/tmp/issue-desc-{id}.md`，将所有 `{{占位符}}` 替换为实际内容（必须包含全6个章节，禁止留空占位符）
7. 读取模板 `cat $SKILL_DIR/templates/mr_template.md`，严格按格式写入 `/tmp/mr-desc-{id}.md`，将所有 `{{占位符}}` 替换为实际内容

**n8n 自动接管后续：push → 创建 Issue → 创建 MR → 禅道回写**

## 输出格式（末尾，每项独占一行）

```
SUMMARY=<一句话总结>
```

## 禁令

- 禁止在 develop/main/master 直接 commit 或 push
- 禁止 `git add .`，只提交 bug 相关文件
- 禁止调用 `bugfix_flow.py` 命令（n8n 全权负责）
- 验证失败时立即停止，输出 `STATUS=FAIL`
