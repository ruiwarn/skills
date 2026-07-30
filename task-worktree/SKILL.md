---
name: task-worktree
description: Use when a user provides a bug link or ID, requirement, or change request and asks to create or prepare an isolated Git worktree, sibling workspace, working directory, or task branch before implementation.
---

# 创建任务工作树

## 目标

先理解任务，再从本次刷新后的 `origin/develop` 创建隔离分支和相邻工作树。职责到返回工作树链接为止，不修改业务代码，不提交、不推送，也不创建 Issue 或 MR。

## 输入分析

1. 判断任务类型并提取简短英文 `slug`：
   - Bug：已有行为不符合预期。
   - Feature：需求、新功能或明确要求改变现有行为。
2. `slug` 使用小写 kebab-case，保留 2～6 个有业务含义的英文词；避免只有 `fix`、`update`、`change` 等空泛词。
3. 用户给出合法名称时优先采用，不擅自改名。显式分支仍须使用与任务类型一致的 `bugfix/` 或 `feature/` 前缀。
4. 信息足以生成稳定名称时直接执行；只有任务类型或核心业务含义确实无法判断时才询问。

输入是禅道链接或 Bug ID 时，**REQUIRED SUB-SKILL：使用 `zc-bug-fix`**，但只执行阶段 0/1 读取 Bug 并提取编号、标题和业务背景。不得进入修复、提交、推送、Issue、MR 或禅道回写阶段。

用户明确要求创建工作树时，即已授权刷新远程引用、创建本地分支和工作树，不要重复索要确认；该授权不包含修改代码、提交或推送。

## 命名规则

先根据任务分析结果计算下表中的标准目录名和分支名。用户明确指定其中一项时，只覆盖该项，未指定项仍使用标准名称。

| 类型 | 本地分支 | 相邻工作树 |
|---|---|---|
| 有编号的 Bug | `bugfix/<id>-<slug>` | `../<project>-bug-<id>` |
| 无编号的 Bug | `bugfix/<slug>` | `../<project>-bug-<slug>` |
| 需求或行为变更 | `feature/<slug>` | `../<project>-feature-<slug>` |

不要为冲突名称自动添加时间戳、序号或随机后缀。静默换名会让任务和目录失去稳定对应关系。

显式目录名必须是单个普通目录名称，并匹配 `^[A-Za-z0-9][A-Za-z0-9._-]*$`。将它拼接为 `target_path="$repo_parent/$target_name"` 后，还要确认其直接父目录就是 `repo_parent`；拒绝绝对路径、路径分隔符、`.`、`..` 和任何越出仓库同级目录的名称。

## 创建流程

### 1. 固定仓库和基线

```bash
repo_root=$(git rev-parse --show-toplevel)
repo_parent=$(dirname "$repo_root")
repo_name=$(basename "$repo_root")

git -C "$repo_root" fetch --prune origin \
    '+refs/heads/develop:refs/remotes/origin/develop'
base_sha=$(git -C "$repo_root" rev-parse --verify \
    'refs/remotes/origin/develop^{commit}')
```

`fetch` 或 `rev-parse` 失败时立即停止；不得使用可能过期的本地 `develop` 代替。

### 2. 生成并校验名称

根据命名表设置绝对 `target_path` 和 `branch_name`，然后执行：

```bash
[[ "$target_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]
test "$(dirname "$target_path")" = "$repo_parent"
git -C "$repo_root" check-ref-format --branch "$branch_name"
git -C "$repo_root" worktree list --porcelain -z
git -C "$repo_root" show-ref --verify --quiet \
    "refs/heads/$branch_name"
remote_branch_output=$(git -C "$repo_root" ls-remote --heads origin \
    "refs/heads/$branch_name") || exit 1
```

同时用 `test -e "$target_path"` 和 `test -L "$target_path"` 检查目标路径，避免覆盖普通目录或符号链接。

按 `--porcelain -z` 的记录和字段解析注册信息，必须确认 `worktree <绝对路径>` 与 `branch refs/heads/<branch_name>` 属于同一条记录；不要用模糊字符串匹配代替。

### 3. 处理冲突

- 目标路径、同名本地分支、同名远程分支都不存在：创建新工作树。
- 同名本地分支存在但未被工作树占用：仅当目标路径不存在且未注册、本地分支精确指向 `base_sha`、`remote_branch_output` 为空时，允许复用该分支。
- 目标路径已经注册为该分支的工作树：仅当工作树干净且 `HEAD` 精确等于 `base_sha` 时，允许幂等复用并直接返回链接。远端是否已有同名分支不影响这个既有工作树的返回。
- 其他情况立即停止并报告具体冲突。

不得删除目录、强制解锁、重置分支、清理工作树、暂存用户修改或自动选择另一个名称。

### 4. 创建

新分支不存在时，从已固定的提交原子化创建分支和工作树：

```bash
git -C "$repo_root" worktree add \
    -b "$branch_name" \
    "$target_path" \
    "$base_sha"
```

允许复用同基线本地分支时：

```bash
git -C "$repo_root" worktree add \
    "$target_path" \
    "$branch_name"
```

不要使用下面这种形式创建一个尚不存在的分支：

```bash
git worktree add <path> <new-branch>
```

### 5. 验证

```bash
test "$(git -C "$target_path" branch --show-current)" = \
    "$branch_name"
test "$(git -C "$target_path" rev-parse HEAD)" = \
    "$base_sha"
test -z "$(git -C "$target_path" status --porcelain)"
```

任一验证失败都不能宣称创建成功。

如果创建命令已经产生部分状态但验证失败，保留现场并报告失败；不得为了回滚而擅自删除工作树或分支。

## 输出

成功后，最终回复严格只包含一个使用绝对路径的 Markdown 链接：

```markdown
[<目录名>](/absolute/path/to/<目录名>)
```

例如：

```markdown
[project-bug-101](/workspace/project-bug-101)
```

失败时不要输出虚假链接，只用一句话说明未创建的具体原因。不要在最终回复重复业务分析、命令、分支名或验证过程。

## 常见错误

| 错误 | 正确做法 |
|---|---|
| 从本地 `develop` 创建 | 先刷新并固定 `origin/develop` 的提交 |
| 先建分支再用不带 `-b` 的示例命令 | 用 `worktree add -b ... <base_sha>` 原子创建 |
| 名称冲突后自动加后缀 | 停止并报告冲突 |
| 顺手修代码、提交或推送 | 创建并验证工作树后立即返回链接 |
| 成功后输出长篇总结 | 最终只输出可点击的绝对路径链接 |
