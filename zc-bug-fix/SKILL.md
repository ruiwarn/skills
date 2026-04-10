---
name: zc-bug-fix
description: Use when the user asks to fix a bug, resolve an issue, or provides a bug URL/bug ID from 禅道, GitLab, GitHub, Jira, or similar systems; especially when the work needs a full workflow of reading the bug, fixing code, verifying, creating issue/MR, and writing status back to the tracker.
---

# Bug-Fix 严格顺序执行协议

> **本 skill 是一个严格的阶段制流水线。你必须按阶段编号从 0 到 8 顺序执行，每个阶段完成并验证后才能进入下一个阶段。禁止跳过、合并、或乱序执行任何阶段。**

---

## ⛔ 全局禁令（违反任何一条即为严重错误）

| 编号 | 禁令 |
|------|------|
| F1 | **禁止在 develop / main / master 分支上直接 commit 或 push** |
| F2 | **禁止跳过阶段或乱序执行** |
| F3 | **禁止在没有创建 MR 的情况下回写禅道** |
| F4 | **禁止把 bug 分类/类型写入评论 — 必须通过脚本写入 browser 字段** |
| F5 | **禁止把 issue / MR 描述内容直接拼成命令行参数 — 必须先写入文件** |
| F6 | **禁止提交与当前 bug 无关的代码改动** |
| F7 | **禁止在验证未通过的情况下宣称"已完成"** |
| F8 | **禁止不经用户确认就创建分支、推送代码、创建 MR** |

---

## 阶段 0: 检查配置

**执行：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py check-config
```

**如果输出 `CONFIG_OK`：** 进入阶段 1。
**如果输出 `MISSING_CONFIG` 或 `MISSING_FIELD`：** ⛔ 立即停止，告知用户创建配置文件：
```bash
cp $SKILL_DIR/zc-bug-fix.config.example ./zc-bug-fix.config
# 然后编辑填入实际的禅道/GitLab 信息
```

⛔ 配置不完整时，禁止执行任何后续阶段。

---

## 阶段 1: 读取禅道 Bug

**执行：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py fetch <bug_id>
```

**必须从返回的 JSON 中提取以下信息：**
- Bug 标题、严重程度、优先级
- 环境信息（版本、硬件）
- 重现步骤
- 期望结果 vs 实际结果
- 日志/报文（如有）
- 相关人员：报告人（openedBy）、定位人、验证人

**同时完成 Bug 根因分类预判：**
阅读 Bug 内容后，从下方分类表选择一个最贴近根因的**中文分类名**。低置信度时必须在阶段 4 前请用户确认。此分类将在阶段 7 通过脚本写入禅道 `browser` 字段。

**允许的分类（必须精确匹配）：**

| 分类 |
|------|
| 需求不清问题 |
| 需求错误问题 |
| 设计_系统整体设计问题 |
| 设计_功能间接口问题 |
| 设计_功能交互问题 |
| 设计_边界值设计问题 |
| 设计_流程逻辑设计问题 |
| 设计_算法设计问题 |
| 编码_流程逻辑实现问题 |
| 编码_编程规范语法问题 |
| 编码_编程规范内存问题 |
| 编码_编程规范初始化 |
| 编码_编程规范函数用错 |
| 编码_编程规范指针调用 |
| 编码_代码合并问题 |
| 编码_模块间接口问题 |
| 编码_库使用问题 |
| 编码_库修改问题 |
| 编码-内核保护机制问题 |

⛔ 禁止选择：空值、继承或历史遗留、未明确定位、非问题。
⛔ bug_type 不是评论内容 — 是一个用于写入 browser 字段的分类标签。

**检查点：** 向用户报告 Bug 摘要和预判分类，确认理解正确后进入阶段 2。

---

## 阶段 2: 分析并修复代码

**要求：**
1. 搜索定位相关代码
2. 先读文件再修改 — 禁止盲改
3. 只修改与当前 Bug 直接相关的代码
4. 所有新增/修改的函数必须补中文注释
5. 必须保证编译通过，且修改的代码静态检查无新警告

⛔ 本阶段禁止创建分支、推送代码、操作禅道。

**检查点：** 修改完成后，列出所有改动文件和修改摘要，等用户确认后进入阶段 3。

---

## 阶段 3: 自测验证

**必须按顺序执行：**

1. 扫描代码库(包含.test等隐藏目录)，运行相关测试用例（如果有）
```bash
# 参考命令，实际命令可能根据项目测试框架不同而不同
make -C .test 2>/dev/null || true
```
2. 如果有类似 meter-protocol-serial 的串口通讯skill，必须根据修改的内容，发送、读取相关协议报文进行自测验证，后续把自测的相关报文附加到议题中。

⛔ 验证未全部通过时，禁止进入阶段 4 — 必须返回阶段 2 修复。

**检查点：** 向用户报告自测验证结果。用户确认全部通过后进入阶段 4。

---

## 阶段 4: 创建分支 + 提交 + 推送

> ⛔ **必须先获得用户明确确认后，才能执行本阶段。** 未得到确认前在此等待。

**4.1 创建 bugfix 分支（脚本自动从 develop 创建）：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py create-branch <bug_id> <short-desc>
```
分支名格式：`bugfix/<bug_id>-<short-desc>`

**4.2 提交代码（只提交相关文件）：**
```bash
git add <file1> <file2> ...
git commit -m "fix(bug#<bug_id>): <简要描述问题和修复方案>"
```

⛔ 禁止 `git add .` 或 `git add -A`。只添加与本次修复相关的文件。
⛔ 禁止在 develop/main/master 上 commit。脚本会拒绝。

**4.3 推送分支（脚本自动拒绝推送到保护分支）：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py push-branch
```

**检查点：** 确认远程分支已创建。记住分支名，阶段 6 需要用。

---

## 阶段 5: 创建 GitLab Issue

**5.1 准备 Issue 内容：**
参考模板 `$SKILL_DIR/templates/issue_6d_template.md`，将完整 6D 内容写入文件：
```bash
# 把 issue 内容写入文件，不要直接拼命令行
cat > /tmp/issue_<bug_id>.md << 'EOF'
... 6D 内容 ...
EOF
```

Issue 必须至少包含：
1. 禅道链接
2. Bug 描述（环境、步骤、期望、实际、日志）
3. 根因分析（根因、直接原因、代码位置、为什么没发现、检讨）
4. 解决方案（思路、修改点、理由、副作用评估）
5. 验证结果
6. 黑盒测试建议
7. 后续改进
8. 责任人

**5.2 创建 Issue：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py create-issue <bug_id> /tmp/issue_<bug_id>.md "bug,<标签>"
```

**检查点：** 从脚本输出的 JSON 中提取 `web_url` 字段，保存为 `ISSUE_URL`。阶段 7 必须使用。
格式形如：`http://172.17.0.100:8080/<group>/<project>/-/issues/<number>`

---

## 阶段 6: 创建 GitLab MR

**6.1 准备 MR 描述：**
参考模板 `$SKILL_DIR/templates/mr_template.md`，将 MR 描述写入文件：
```bash
cat > /tmp/mr_<bug_id>.md << 'EOF'
... MR 描述 ...
EOF
```

MR 描述必须包含：修复内容、根因、修改文件、验证结果、禅道链接、Issue 链接、责任人。

**6.2 创建 MR：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py create-mr <bug_id> "bugfix/<bug_id>-<short-desc>" /tmp/mr_<bug_id>.md
```

**检查点：** 从脚本输出的 JSON 中提取 `web_url` 字段，保存为 `MR_URL`。阶段 7 必须使用。
格式形如：`http://172.17.0.100:8080/<group>/<project>/-/merge_requests/<number>`

---

## 阶段 7: 回写禅道（一条命令完成全部操作）

> ⛔ **前置条件（全部满足才能执行）：**
> - ✅ 阶段 3 验证已通过
> - ✅ 阶段 4 代码已 push 到远程
> - ✅ 阶段 5 已创建 Issue，有 ISSUE_URL
> - ✅ 阶段 6 已创建 MR，有 MR_URL
> - 缺少任何一项，⛔ 禁止执行本阶段

**使用一条命令完成全部禅道回写：**
```bash
python3 $SKILL_DIR/scripts/bugfix_flow.py zentao-writeback <bug_id> "<bug_type>" "<ISSUE_URL>" "<MR_URL>"
```

这条命令会**自动**完成以下四步：
1. ✅ 检查 Bug 当前状态（避免重复操作）
2. ✅ 确认 Bug — 评论自动附带 Issue 可点击链接
3. ✅ 设置 Bug 分类到 `browser` 字段（**不是评论**！）
4. ✅ 解决 Bug — 评论自动附带 MR 可点击链接，自动转派给项目负责人

**参数说明：**
| 参数 | 内容 | 示例 |
|------|------|------|
| `bug_id` | 禅道 Bug 编号 | `5245` |
| `bug_type` | 阶段 1 预判的中文分类名 | `"编码_流程逻辑实现问题"` |
| `ISSUE_URL` | 阶段 5 获得的 GitLab Issue URL | `"http://172.17.0.100:8080/grp/proj/-/issues/42"` |
| `MR_URL` | 阶段 6 获得的 GitLab MR URL | `"http://172.17.0.100:8080/grp/proj/-/merge_requests/9"` |

> ⛔ **四个参数全部必填 — 脚本会拒绝不完整的调用**
> ⛔ **严禁手动拼接禅道 API 调用来替代本命令**
> ⛔ **严禁把 bug_type 写入评论 — 它通过脚本写入 browser 字段**

**检查点：** 确认脚本输出 `✅ 禅道回写完成`。如果失败，查看错误信息并使用备用命令（见文末）。

---

## 阶段 8: 总结报告

向用户输出最终总结表格：

| 项目 | 内容 |
|------|------|
| 禅道 Bug | #bug_id - 标题 |
| Bug 分类 | bug_type（已写入 browser 字段） |
| 修复分支 | bugfix/bug_id-short-desc |
| GitLab Issue | ISSUE_URL |
| GitLab MR | MR_URL |
| 修改文件 | 文件列表 |
| 验证结果 | 静态检查 ✅ / 构建 ✅ |

附上需要硬件/协议人工验证的测试场景表。

---

## 备用命令（仅在 zentao-writeback 整体失败时逐步补救）

```bash
# 1. 确认 Bug（评论必须包含 Issue URL）
python3 $SKILL_DIR/scripts/bugfix_flow.py zentao-confirm <bug_id> "已创建 GitLab issue: <ISSUE_URL>"

# 2. 设置 browser 字段（传中文分类名，不是写评论！）
python3 $SKILL_DIR/scripts/bugfix_flow.py zentao-set-browser-type <bug_id> "<bug_type>"

# 3. 解决 Bug（评论必须包含 MR URL）
python3 $SKILL_DIR/scripts/bugfix_flow.py zentao-resolve <bug_id> "已创建 GitLab MR: <MR_URL>" "" "<bug_type>"
```

---

## 配置说明

配置文件位于项目根目录 `zc-bug-fix.config`。
环境变量 `ZC_BUG_FIX_CONFIG` 可覆盖路径（相对路径按项目根目录解析）。

必填字段：
| 字段 | 说明 |
|------|------|
| `ZENTAO_URL` | 禅道地址 |
| `ZENTAO_ACCOUNT` | 禅道账号 |
| `ZENTAO_PASSWORD` | 禅道密码 |
| `GITLAB_URL` | GitLab 地址 |
| `GITLAB_TOKEN` | GitLab Personal Access Token |
| `GITLAB_PROJECT_ID` | GitLab 项目 ID |
| `TARGET_BRANCH` | MR 目标分支（默认 develop） |
| `PROJECT_OWNER` | 项目负责人禅道用户名（bug 解决后转派） |

初始化：
```bash
cp $SKILL_DIR/zc-bug-fix.config.example ./zc-bug-fix.config
```

---

## 文件结构

```
$SKILL_DIR/
├── SKILL.md                          ← 本文件（严格执行协议）
├── zc-bug-fix.config.example         ← 配置模板
├── scripts/
│   ├── bugfix_flow.py                ← 主控脚本（优先使用）
│   ├── check_config.py               ← 配置检查
│   ├── config_paths.py               ← 路径解析
│   ├── zentao.py                     ← 禅道 API
│   ├── gitlab.py                     ← GitLab API
│   ├── bugfix_flow.sh                ← (旧版 shell，已废弃)
│   ├── check_config.sh               ← (旧版 shell，已废弃)
│   ├── config_paths.sh               ← (旧版 shell，已废弃)
│   ├── zentao.sh                     ← (旧版 shell，已废弃)
│   └── gitlab.sh                     ← (旧版 shell，已废弃)
├── templates/
│   ├── issue_6d_template.md          ← Issue 6D 模板
│   └── mr_template.md                ← MR 描述模板
└── tests/
    ├── test_config_paths.py          ← Python 测试（pytest）
    └── config_resolution_test.sh     ← (旧版 shell 测试，已废弃)
```
