---
name: zc-bug-fix
description: Use when the user asks to fix a bug, resolve an issue, or provides a bug URL/bug ID from 禅道, GitLab, GitHub, Jira, or similar systems; especially when the work needs a full workflow of reading the bug, fixing code, verifying, creating issue/MR, and writing status back to the tracker.
---

# Bug-Fix 用户优先分阶段执行协议

> **本 skill 采用“用户指定优先、前置条件按需补齐”的分阶段流程。** 如果用户明确要求“从阶段 4 开始”或“从某个阶段继续”，就从该阶段执行；不要因为固定流程强制退回阶段 0。真正的安全前置条件（保护分支、MR 前禁止回写禅道、bug_type 通过 browser 字段写入等）仍然必须满足。

---

## ⛔ 全局禁令（违反任何一条即为严重错误）

| 编号 | 禁令 |
|------|------|
| F1 | **禁止在 develop / main / master 分支上直接 commit 或 push** |
| F2 | **禁止无视用户明确指定的起点；缺少当前阶段必需信息时必须先补齐，不能盲目执行** |
| F3 | **禁止在没有创建 MR 的情况下回写禅道** |
| F4 | **禁止把 bug 分类/类型写入评论 — 必须通过脚本写入 browser 字段** |
| F5 | **禁止把 issue / MR 描述内容直接拼成命令行参数 — 必须先写入文件** |
| F6 | **禁止提交与当前 bug 无关的代码改动** |
| F7 | **禁止在验证未通过的情况下宣称"已完成"** |
| F8 | **禁止不经用户确认就创建分支、推送代码、创建 MR** |

---

## 启动总则（用户优先）

1. **用户明确说“从阶段 N 开始 / 从阶段 N 继续” → 直接从阶段 N 开始。** 前面阶段只做必要补位，不做仪式化重跑。
2. **用户说明“代码已经改好了 / bug 已经处理了”但没说阶段 → 先分析当前工作区修改、已暂存内容、分支状态、已有 Issue/MR/禅道信息，再从最接近的阶段继续。** 这类场景通常优先考虑阶段 4。
3. **只在当前阶段缺少关键信息时再提问。** 例如当前阶段需要 `bug_id` / 禅道链接，而上下文里没有时，再向用户索要；不要一上来把阶段 0→3 全部重跑。
4. **用户明确要求进入阶段 4 / 5 / 6 / 7，可视为对该阶段动作的授权。** 不要针对同一动作重复索要“是否允许创建分支 / 提交 / 推送 / 建 MR”。
5. **真正的硬前置条件不能跳过。** 尤其阶段 7 之前，必须有验证结果、远程分支、`ISSUE_URL`、`MR_URL`。

---

## 阶段 0: 按需检查配置

**只有当当前或下一步需要访问禅道 / GitLab 时才执行本阶段。**

- `fetch`
- `create-issue`
- `create-mr`
- `zentao-writeback`
- 备用的 `zentao-confirm` / `zentao-set-browser-type` / `zentao-resolve`

如果用户从阶段 4 开始，且当前只需要分析现有改动、创建分支、提交、推送，可暂不执行本阶段。

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

⛔ 配置不完整时，禁止执行**依赖配置的后续阶段**。

---

## 阶段 1: 读取禅道 Bug

**仅在需要补齐 Bug 背景或缺少 `bug_id` / 禅道链接时执行。**

- 如果用户已经提供了足够的 Bug 信息，或当前从阶段 4 / 5 / 6 / 7 继续且所需信息已齐，可以不回头强制执行本阶段。
- 如果当前阶段需要引用禅道 Bug，但上下文里没有 `bug_id` 或禅道链接，先向用户索要，再继续。

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
阅读 Bug 内容后，从下方分类表选择一个最贴近根因的**中文分类名**。低置信度且准备进入阶段 7 前，才需要向用户补确认。此分类将在阶段 7 通过脚本写入禅道 `browser` 字段。

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

**如果用户已经改好了代码并要求从阶段 4 或更后阶段继续：**

1. 不要强制回到“重新修复代码”的流程。
2. 先分析当前工作区 / 已暂存改动（`git status`、`git diff`、`git diff --cached`）。
3. 提炼修改文件、根因、修复思路、潜在影响，作为阶段 4 / 5 / 6 的输入。
4. 如果发现明显与当前 Bug 无关的改动，提醒用户并在阶段 4 只提交相关文件。

⛔ 本阶段禁止创建分支、推送代码、操作禅道。

**检查点：** 修改完成后，列出所有改动文件和修改摘要；如果用户已经明确要求继续推进，不必在这里停住等待。

---

## 阶段 3: 按需自测验证

如果用户明确要求从阶段 4 开始，不要机械退回阶段 0；优先利用用户已提供的验证结果。只有在准备进入阶段 7 / 8，或你无法说明验证结果时，才补做必要自测。

**建议按以下顺序补齐验证证据：**

1. 扫描代码库(包含.test等隐藏目录)，运行相关测试用例（如果有）
```bash
# 参考命令，实际命令可能根据项目测试框架不同而不同
make -C .test 2>/dev/null || true
```
2. 如果有类似 meter-protocol-serial 的串口通讯skill，必须根据修改的内容，发送、读取相关协议报文进行自测验证，后续把自测的相关报文附加到议题中。

⛔ 如果当前目标是进入阶段 7 / 8，验证未全部通过时必须返回阶段 2 修复。

**检查点：** 向用户报告自测验证结果；如果用户已经明确要求继续推进，可直接进入阶段 4，但进入阶段 7 / 8 前必须能说明验证结果。

---

## 阶段 4: 创建分支 + 提交 + 推送

> ⛔ **必须有用户明确意图才能执行本阶段。** 用户直接说“从阶段 4 开始”或“帮我提交并推送”或“BUG已经改完了，从后面的阶段开始”即可视为已授权且从该阶段直接开始，不要重复追问。

**4.0 如果代码已经存在，先分析当前修改：**
1. 查看 `git status --short`
2. 查看 `git diff --stat`、`git diff`、`git diff --cached`
3. 提炼修改文件、根因、修复思路、验证摘要
4. 确认本次提交只包含与当前 Bug 直接相关的改动

**如果缺少 `bug_id` 或禅道链接：** 先向用户索要。分支名、提交信息、Issue/MR 模板都依赖它。

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

如果用户明确要求从阶段 5 开始，即视为允许创建 Issue；不要再重复询问。若缺少禅道链接 / `bug_id`，先向用户索要，因为模板必须引用它。

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

如果用户明确要求从阶段 6 开始，即视为允许创建 MR；不要再重复询问。MR 描述中的修复内容、根因、修改文件、验证结果应优先复用前面已分析好的信息，而不是重新回退到阶段 0。

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

如果用户直接要求从阶段 7 开始，可以直接准备本阶段；但只补齐本阶段缺少的关键信息，不要为了“走流程”回头重跑无关阶段。

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
├── SKILL.md                          ← 本文件（用户优先协议）
├── zc-bug-fix.config.example         ← 配置模板
├── scripts/
│   ├── bugfix_flow.py                ← 主控脚本（优先使用）
│   ├── check_config.py               ← 配置检查
│   ├── config_paths.py               ← 路径解析
│   ├── zentao.py                     ← 禅道 API
│   └── gitlab.py                     ← GitLab API
├── templates/
│   ├── issue_6d_template.md          ← Issue 6D 模板
│   └── mr_template.md                ← MR 描述模板
└── tests/
    └── test_config_paths.py          ← Python 测试（pytest）
```
