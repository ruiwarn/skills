---
name: task-worktree
description: Use when a user provides a bug link or ID, requirement, or change request and asks to create or prepare an isolated Git worktree, sibling workspace, working directory, or task branch before implementation, or to delete/remove an existing worktree when explicitly asked.
---

# 任务工作树

## 目标

处理任务工作树的两类操作：**创建**（默认）与**删除**（用户明确要求时）。创建时从本次刷新后的 `origin/develop` 生成隔离分支和相邻工作树，并把主仓库根目录被 `.gitignore` 忽略的 `zc-bug-fix.config` 凭证文件拷入工作树，职责到返回工作树链接为止。两类操作都不修改业务代码、不提交、不推送，也不创建 Issue 或 MR；删除时不得擅自销毁用户未提交的改动或未合并的分支。

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
| 有编号的 Bug | `bugfix/<id>-<slug>` | `../wt-bug-<id>` |
| 无编号的 Bug | `bugfix/<slug>` | `../wt-bug-<slug>` |
| 需求或行为变更 | `feature/<slug>` | `../wt-feat-<slug>` |

目录名统一以 `wt-` 前缀开头（worktree 缩写），一眼区分工作树与主仓库；不再拼接 `<project>` 前缀，避免目录名过长触发 Windows 260 字符路径上限。分支名仍保持 `bugfix/` 或 `feature/` 前缀不变。

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

### 6. 拷贝凭证配置

每次创建工作树都必须把主仓库根目录的 `zc-bug-fix.config` 拷入工作树根目录，这是创建流程的必做步骤，而非等出问题再补。该文件含禅道、GitLab 凭证，已被 `.gitignore` 忽略、不在 git 跟踪内容中，从 `origin/develop` 建出的工作树里不会有它；不拷贝则工作树中 `zc-bug-fix` 等操作找不到凭证：

```bash
src="$repo_root/zc-bug-fix.config"
dst="$target_path/zc-bug-fix.config"
if [ -f "$src" ]; then
    cp "$src" "$dst"
fi
```

主仓库根目录存在该文件时必须拷贝；仅当主仓库根本没有该文件——说明此仓库不用 `zc-bug-fix`——时才跳过，且不视为错误。该文件是未跟踪的本地凭证，拷贝不涉及任何提交或推送。

### 7. 相对化工作树 git 指针（WSL 环境必做）

WSL 的 `git worktree add` 会把 WSL 绝对路径（`/mnt/...`）写进工作树 `.git` 指针和 admin 目录的 `gitdir` 回指文件。Windows 原生 IDE（Cursor、非 WSL 远程的 VS Code 等）读不懂 `/mnt/...`，打开工作树会报"没有 git 仓库"（主仓库因 `.git` 是真实目录而不受影响）。创建后立即把这两个指针改写为相对路径，WSL 与 Windows 便都能识别。本技能保证工作树与主仓库同处 `repo_parent` 下互为同级，故相对路径固定：

```bash
admin_dir="$repo_root/.git/worktrees/$target_name"
# 工作树 .git -> admin 目录
printf 'gitdir: ../%s/.git/worktrees/%s\n' "$repo_name" "$target_name" > "$target_path/.git"
# admin gitdir -> 工作树 .git
printf '../../../../%s/.git\n' "$target_name" > "$admin_dir/gitdir"
# commondir 通常已是 ../..，若被写成绝对路径则一并相对化
grep -q '^/' "$admin_dir/commondir" 2>/dev/null && printf '../..\n' > "$admin_dir/commondir"
```

改写后复查 git 仍可解析；失败则用变量重新还原绝对路径并报告，不留半 broken 状态：

```bash
git -C "$target_path" rev-parse --show-toplevel
git -C "$target_path" rev-parse --git-common-dir
test "$(git -C "$target_path" branch --show-current)" = "$branch_name"
```

## 输出

成功后，最终回复严格只包含一个使用绝对路径的 Markdown 链接：

```markdown
[<目录名>](/absolute/path/to/<目录名>)
```

例如：

```markdown
[wt-bug-101](/workspace/wt-bug-101)
```

失败时不要输出虚假链接，只用一句话说明未创建的具体原因。不要在最终回复重复业务分析、命令、分支名或验证过程。

## 删除工作树

用户明确要求删除某个工作树时执行。删除不可逆，必须先检查再动手，绝不擅自销毁用户未提交的改动或未合并的分支。

### 1. 定位工作树

用 `git worktree list` 确认目标已注册，解析出工作树绝对路径 `wt_path` 与分支名 `branch_name`：

```bash
git -C "$repo_root" worktree list --porcelain -z
```

用户给出目录名、路径或分支名时，按 `--porcelain` 记录精确匹配 `worktree <绝对路径>` 与 `branch refs/heads/<branch>` 字段；找不到则停止并报告。

### 2. 检查状态

```bash
git -C "$repo_root" fetch --prune origin '+refs/heads/develop:refs/remotes/origin/develop' || true
# 工作树是否有未提交改动
git -C "$wt_path" status --porcelain
# 分支是否已合并进 origin/develop（输出 MERGED 表示已合并）
git -C "$repo_root" merge-base --is-ancestor "$branch_name" origin/develop && echo MERGED || echo NOT_MERGED
# 分支是否已推送到远端（非空表示已推送）
git -C "$repo_root" ls-remote --heads origin "refs/heads/$branch_name"
```

- 工作树有未提交改动：停止，列出改动文件，让用户先处理；仅当用户**显式要求强制删除**时才进入第 3 步的 `--force` 路径。
- 分支未合并且未推送：删除分支前必须经用户显式确认（见第 4 步）。

### 3. 删除工作树

```bash
# 干净工作树
git -C "$repo_root" worktree remove "$wt_path"
# 有改动且用户显式强制
git -C "$repo_root" worktree remove --force "$wt_path"
```

`worktree remove` 失败（如文件被外部占用）时保留现场并报告，不要再用 `--force` 兜底。

### 4. 删除本地分支（可选，需用户明确要求）

默认只删工作树，不删分支。仅当用户要求删分支时：

```bash
# 已合并或已推送：安全删除
git -C "$repo_root" branch -d "$branch_name"
# 未合并且用户显式确认丢弃：不可逆
git -C "$repo_root" branch -D "$branch_name"
```

未合并/未推送的分支默认保留；用户显式确认后才用 `-D`，并提示该分支的提交将被丢弃。

### 5. 验证与清理

```bash
git -C "$repo_root" worktree prune
git -C "$repo_root" worktree list
```

确认目标工作树已不在列表中；若用户要求删分支，再确认 `refs/heads/$branch_name` 已不存在。

### 输出

一句话报告删除结果：工作树路径、是否一并删除分支。不输出长篇总结。

## 常见错误

| 错误 | 正确做法 |
|---|---|
| 从本地 `develop` 创建 | 先刷新并固定 `origin/develop` 的提交 |
| 先建分支再用不带 `-b` 的示例命令 | 用 `worktree add -b ... <base_sha>` 原子创建 |
| 名称冲突后自动加后缀 | 停止并报告冲突 |
| 顺手修代码、提交或推送 | 创建并验证工作树后立即返回链接 |
| 成功后输出长篇总结 | 最终只输出可点击的绝对路径链接 |
| 工作树中 `zc-bug-fix` 找不到凭证 | 执行第 6 步把主仓库的 `zc-bug-fix.config` 拷入工作树根目录 |
| WSL 建的工作树在 Windows IDE 报"没有 git 仓库" | 执行第 7 步把 `.git`/`gitdir` 指针改相对路径 |
