#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bug-fix 主控脚本（严格顺序执行）- Python 版本

Replaces bugfix_flow.sh. Orchestrates the full bug-fix workflow:
  check-config → fetch → create-branch → push → create-issue →
  create-mr → zentao-writeback (confirm + set-browser + resolve).
"""

import json
import os
import re
import subprocess
import sys

# ---------------------------------------------------------------------------
# Sibling-module imports
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_paths import get_effective_config_path, get_preferred_config_path, get_example_path
from check_config import load_config, check_config
from zentao import ZentaoClient, format_zentao_clickable_links
from gitlab import GitLabClient

# ---------------------------------------------------------------------------
# URL validation helpers (module-level so tests can import them directly)
# ---------------------------------------------------------------------------

def contains_gitlab_issue_link(comment: str) -> bool:
    """Check if comment contains a GitLab issue URL."""
    return bool(re.search(r'https?://[^\s]+/-/issues/\d+', comment))


def contains_gitlab_mr_link(comment: str) -> bool:
    """Check if comment contains a GitLab MR URL."""
    return bool(re.search(r'https?://[^\s]+/-/merge_requests/\d+', comment))

# ---------------------------------------------------------------------------
# Git operations
# ---------------------------------------------------------------------------

def create_branch(bug_id: str, short_desc: str):
    """创建 bugfix 分支，自动从 origin/develop 拉取最新代码。

    分支名格式: bugfix/<bug_id>-<short_desc>
    """
    if not bug_id or not short_desc:
        print("错误: 用法 create-branch <bug_id> <short_desc>", file=sys.stderr)
        print("示例: create-branch 5245 fix-timeout", file=sys.stderr)
        sys.exit(1)

    branch_name = f"bugfix/{bug_id}-{short_desc}"

    # Get current branch
    try:
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        current = "unknown"

    if current == branch_name:
        print(f"已在目标分支: {branch_name}")
        return

    # Stash if dirty
    diff_result = subprocess.run(["git", "diff", "--quiet"], capture_output=True)
    cached_result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if diff_result.returncode != 0 or cached_result.returncode != 0:
        print("警告: 工作区有未提交的更改，将使用 stash 暂存", file=sys.stderr)
        subprocess.run(
            ["git", "stash", "push", "-m", f"auto-stash before creating {branch_name}"],
            check=True,
        )

    # Fetch and create branch
    print("正在获取最新的 develop 分支...")
    subprocess.run(["git", "fetch", "origin", "develop"], capture_output=True)

    # Check if origin/develop exists
    check = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/remotes/origin/develop"],
        capture_output=True,
    )
    if check.returncode == 0:
        subprocess.run(["git", "checkout", "-b", branch_name, "origin/develop"], check=True)
    else:
        subprocess.run(["git", "checkout", "develop"], capture_output=True)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    print(f"✅ 已创建并切换到分支: {branch_name}")
    print(f"   基于: origin/develop")


def push_branch():
    """推送当前分支到远程，拒绝在保护分支上执行。"""
    try:
        current = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        current = "unknown"

    # 保护分支黑名单
    if current in ("develop", "main", "master"):
        print(f"⛔ 错误: 禁止直接在 '{current}' 分支上推送！", file=sys.stderr)
        print("请先使用 'create-branch <bug_id> <short_desc>' 创建 bugfix 分支。", file=sys.stderr)
        sys.exit(1)

    if not current.startswith("bugfix/"):
        print(f"警告: 当前分支 '{current}' 不符合 bugfix/* 命名规范", file=sys.stderr)
        print("推荐使用 'create-branch <bug_id> <short_desc>' 创建标准分支", file=sys.stderr)

    subprocess.run(["git", "push", "-u", "origin", current], check=True)
    print(f"✅ 已推送分支: {current}")

# ---------------------------------------------------------------------------
# Zentao workflow functions
# ---------------------------------------------------------------------------

def zentao_confirm(client: ZentaoClient, bug_id: str, comment: str):
    """确认 Bug，要求评论包含 Issue 链接。"""
    if not bug_id:
        print("错误: 用法 zentao-confirm <bug_id> [comment]", file=sys.stderr)
        sys.exit(1)
    if not contains_gitlab_issue_link(comment):
        print("错误: 确认评论中必须包含 GitLab issue 链接。请先创建 issue 再回写禅道。", file=sys.stderr)
        sys.exit(1)
    comment = format_zentao_clickable_links(comment)
    client.confirm_bug(bug_id, comment)


def zentao_resolve(client: ZentaoClient, bug_id: str, comment: str,
                   assigned_to: str = "", bug_type: str = ""):
    """解决 Bug，要求评论包含 MR 链接。"""
    if not bug_id:
        print("错误: 用法 zentao-resolve <bug_id> [comment]", file=sys.stderr)
        sys.exit(1)
    if not contains_gitlab_mr_link(comment):
        print("错误: 解决评论中必须包含 GitLab MR 链接。请先创建 MR 再回写禅道。", file=sys.stderr)
        sys.exit(1)
    comment = format_zentao_clickable_links(comment)
    client.resolve_bug(bug_id, "fixed", comment, assigned_to, bug_type)


def zentao_writeback(client: ZentaoClient, bug_id: str, bug_type: str,
                     issue_url: str, mr_url: str, project_owner: str):
    """一条命令完成全部禅道回写操作：确认 + 设置 browser 字段 + 解决。"""
    # Validate all 4 params
    if not all([bug_id, bug_type, issue_url, mr_url]):
        print("错误: 用法 zentao-writeback <bug_id> <bug_type> <issue_url> <mr_url>", file=sys.stderr)
        print("四个参数缺一不可！", file=sys.stderr)
        print("  bug_id    : 禅道 Bug 编号", file=sys.stderr)
        print("  bug_type  : 中文 Bug 分类名（如 '编码_流程逻辑实现问题'）", file=sys.stderr)
        print("  issue_url : GitLab Issue URL", file=sys.stderr)
        print("  mr_url    : GitLab MR URL", file=sys.stderr)
        sys.exit(1)

    if not contains_gitlab_issue_link(issue_url):
        print(f"错误: issue_url 格式不正确: {issue_url}", file=sys.stderr)
        print("正确格式: http://172.17.0.100:8080/<group>/<project>/-/issues/<number>", file=sys.stderr)
        sys.exit(1)

    if not contains_gitlab_mr_link(mr_url):
        print(f"错误: mr_url 格式不正确: {mr_url}", file=sys.stderr)
        print("正确格式: http://172.17.0.100:8080/<group>/<project>/-/merge_requests/<number>", file=sys.stderr)
        sys.exit(1)

    print("==========================================")
    print(f"禅道回写开始: Bug #{bug_id}")
    print("==========================================")

    # Step 1/4
    print("\n>>> 步骤 1/4: 检查 Bug 当前状态...")
    client.login()
    client.fetch_bug_json(bug_id)

    # Step 2/4
    print("\n>>> 步骤 2/4: 确认 Bug（附带 Issue 链接）...")
    confirm_comment = format_zentao_clickable_links(f"已创建 GitLab issue: {issue_url}")
    client.confirm_bug(bug_id, confirm_comment)

    # Step 3/4
    print(f"\n>>> 步骤 3/4: 设置 Bug 分类到 browser 字段: {bug_type}...")
    client.update_bug_browser_type(bug_id, bug_type)

    # Step 4/4 - don't pass bug_type since already set in step 3
    print("\n>>> 步骤 4/4: 解决 Bug（附带 MR 链接）...")
    resolve_comment = format_zentao_clickable_links(f"已创建 GitLab MR: {mr_url}")
    client.resolve_bug(bug_id, "fixed", resolve_comment, project_owner, "")

    print(f"""
==========================================
✅ 禅道回写完成:
   Bug #{bug_id}
   - 状态: 已确认 → 已解决
   - Browser 字段: {bug_type}
   - Issue 链接: {issue_url}
   - MR 链接: {mr_url}
   - 已转派给: {project_owner}
==========================================""")


def print_config_hint():
    """输出配置提示。"""
    preferred = get_preferred_config_path()
    example = get_example_path()
    print(f"""配置文件:
  {preferred}

初始化方式:
  cp {example} {preferred}""")

# ---------------------------------------------------------------------------
# Issue / MR creation wrappers
# ---------------------------------------------------------------------------

def create_issue(gitlab_client: GitLabClient, bug_id: str, description_file: str,
                 labels: str = "bug", title_prefix: str = "Bug"):
    if not bug_id or not description_file:
        print("错误: 用法 create-issue <bug_id> <description_file> [labels] [title_prefix]", file=sys.stderr)
        sys.exit(1)
    title = f"{title_prefix} #{bug_id}"
    result = gitlab_client.create_issue(title, description_file, labels)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def create_mr(gitlab_client: GitLabClient, bug_id: str, source_branch: str,
              description_file: str, target_branch: str = "", title_prefix: str = "Bugfix"):
    if not bug_id or not source_branch or not description_file:
        print("错误: 用法 create-mr <bug_id> <source_branch> <description_file> [target_branch] [title_prefix]", file=sys.stderr)
        sys.exit(1)
    title = f"{title_prefix} #{bug_id}"
    result = gitlab_client.create_mr(source_branch, title, description_file, target_branch)
    print(json.dumps(result, ensure_ascii=False, indent=2))

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def print_usage():
    script_name = os.path.basename(sys.argv[0])
    print(f"""bug-fix 主控脚本（严格顺序执行）- Python 版本

推荐命令（按阶段顺序使用）:
  {script_name} check-config                                          # 阶段 0: 检查配置
  {script_name} fetch <bug_id>                                        # 阶段 1: 读取禅道 Bug
  {script_name} create-branch <bug_id> <short_desc>                   # 阶段 4: 创建 bugfix 分支
  {script_name} push-branch                                           # 阶段 4: 推送分支（拒绝保护分支）
  {script_name} create-issue <bug_id> <desc_file> [labels]            # 阶段 5: 创建 GitLab Issue
  {script_name} create-mr <bug_id> <branch> <desc_file> [target]      # 阶段 6: 创建 GitLab MR
  {script_name} zentao-writeback <bug_id> <type> <issue_url> <mr_url> # 阶段 7: 一键回写禅道

备用命令（仅在 zentao-writeback 失败时逐步使用）:
  {script_name} zentao-confirm <bug_id> [comment]
  {script_name} zentao-set-browser-type <bug_id> <bug_type>
  {script_name} zentao-resolve <bug_id> [comment] [assigned_to] [bug_type]
  {script_name} config-hint

说明:
  1. 按阶段编号 0→8 顺序执行
  2. 禁止在 develop/main/master 上直接 commit 或 push
  3. zentao-writeback 四个参数全部必填
  4. bug_type 是中文分类名，会写入禅道 browser 字段（不是评论）
  5. issue / MR 描述必须先写入文件，不要拼命令行
  6. resolve 默认转派给 zc-bug-fix.config 中的 PROJECT_OWNER""")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        sys.exit(0 if sys.argv[1:] and sys.argv[1] in ("-h", "--help", "help") else 1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Commands that don't need config/API clients
    if command == "check-config":
        status, messages = check_config()
        print(status)
        for msg in messages:
            print(msg)
        sys.exit(0 if status == "CONFIG_OK" else 1)

    if command == "config-hint":
        print_config_hint()
        sys.exit(0)

    # Git-only commands (no API needed, but don't need config check)
    if command == "create-branch":
        if len(args) < 2:
            print("错误: 用法 create-branch <bug_id> <short_desc>", file=sys.stderr)
            sys.exit(1)
        create_branch(args[0], args[1])
        sys.exit(0)

    if command == "push-branch":
        push_branch()
        sys.exit(0)

    # All remaining commands need config + API clients
    status, messages = check_config()
    if status != "CONFIG_OK":
        print(status)
        for msg in messages:
            print(msg, file=sys.stderr)
        sys.exit(1)

    config_path, _ = get_effective_config_path()
    config = load_config(config_path)
    project_owner = config.get("PROJECT_OWNER", "")

    zentao_client = ZentaoClient(config)
    gitlab_client = GitLabClient(config)

    try:
        if command == "fetch":
            if not args:
                print("错误: 用法 fetch <bug_id>", file=sys.stderr)
                sys.exit(1)
            print(zentao_client.get_bug(args[0]))

        elif command == "create-issue":
            if len(args) < 2:
                print("错误: 用法 create-issue <bug_id> <description_file> [labels] [title_prefix]", file=sys.stderr)
                sys.exit(1)
            labels = args[2] if len(args) > 2 else "bug"
            title_prefix = args[3] if len(args) > 3 else "Bug"
            create_issue(gitlab_client, args[0], args[1], labels, title_prefix)

        elif command == "create-mr":
            if len(args) < 3:
                print("错误: 用法 create-mr <bug_id> <source_branch> <description_file> [target_branch] [title_prefix]", file=sys.stderr)
                sys.exit(1)
            target = args[3] if len(args) > 3 else ""
            title_prefix = args[4] if len(args) > 4 else "Bugfix"
            create_mr(gitlab_client, args[0], args[1], args[2], target, title_prefix)

        elif command == "zentao-writeback":
            if len(args) < 4:
                print("错误: 用法 zentao-writeback <bug_id> <bug_type> <issue_url> <mr_url>", file=sys.stderr)
                sys.exit(1)
            zentao_writeback(zentao_client, args[0], args[1], args[2], args[3], project_owner)

        elif command == "zentao-confirm":
            if not args:
                print("错误: 用法 zentao-confirm <bug_id> [comment]", file=sys.stderr)
                sys.exit(1)
            comment = args[1] if len(args) > 1 else ""
            zentao_confirm(zentao_client, args[0], comment)

        elif command == "zentao-set-browser-type":
            if len(args) < 2:
                print("错误: 用法 zentao-set-browser-type <bug_id> <bug_type>", file=sys.stderr)
                sys.exit(1)
            zentao_client.login()
            zentao_client.update_bug_browser_type(args[0], args[1])

        elif command == "zentao-resolve":
            if not args:
                print("错误: 用法 zentao-resolve <bug_id> [comment] [assigned_to] [bug_type]", file=sys.stderr)
                sys.exit(1)
            comment = args[1] if len(args) > 1 else ""
            assigned_to = args[2] if len(args) > 2 else ""
            bug_type = args[3] if len(args) > 3 else ""
            zentao_resolve(zentao_client, args[0], comment, assigned_to, bug_type)

        else:
            print_usage()
            sys.exit(1)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
