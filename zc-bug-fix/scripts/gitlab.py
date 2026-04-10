#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitLab API 操作脚本 - Python 版本"""

import sys
import os
import json
import urllib.request
import urllib.error

# 支持从 scripts 目录直接导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_paths import get_effective_config_path
from check_config import load_config, check_config


class GitLabClient:
    """GitLab API 客户端，使用 Private Token 认证。"""

    def __init__(self, config: dict):
        self.base_url = config["GITLAB_URL"]
        self.token = config["GITLAB_TOKEN"]
        self.project_id = config["GITLAB_PROJECT_ID"]
        self.target_branch = config.get("TARGET_BRANCH", "develop")
        self.api_base = f"{self.base_url}/api/v4/projects/{self.project_id}"

    def _request(self, method: str, endpoint: str, body: dict = None) -> dict:
        """发送 GitLab API 请求。"""
        url = f"{self.api_base}{endpoint}"
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("PRIVATE-TOKEN", self.token)
        req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(req)
            return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"GitLab API 错误 ({e.code}): {body_text}"
            ) from e

    def create_issue(self, title: str, description_file: str, labels: str = "bug") -> dict:
        """创建 GitLab Issue。

        Args:
            title: Issue 标题
            description_file: 描述内容文件路径（UTF-8 markdown/text）
            labels: 标签，逗号分隔（默认 "bug"）
        """
        if not title or not description_file:
            raise ValueError("title 和 description_file 不能为空")
        if not os.path.isfile(description_file):
            raise FileNotFoundError(f"描述文件不存在: {description_file}")

        with open(description_file, "r", encoding="utf-8") as f:
            description = f.read()

        return self._request("POST", "/issues", {
            "title": title,
            "description": description,
            "labels": labels,
        })

    def get_issue(self, issue_iid: str) -> dict:
        """获取 GitLab Issue 详情。"""
        if not issue_iid:
            raise ValueError("issue_iid 不能为空")
        return self._request("GET", f"/issues/{issue_iid}")

    def create_mr(self, source_branch: str, title: str, description_file: str,
                  target_branch: str = "") -> dict:
        """创建 GitLab Merge Request。

        Args:
            source_branch: 源分支名
            title: MR 标题
            description_file: 描述内容文件路径（UTF-8 markdown/text）
            target_branch: 目标分支（默认使用配置中的 TARGET_BRANCH）
        """
        if not source_branch or not title or not description_file:
            raise ValueError("source_branch、title 和 description_file 不能为空")
        if not os.path.isfile(description_file):
            raise FileNotFoundError(f"描述文件不存在: {description_file}")

        if not target_branch:
            target_branch = self.target_branch

        with open(description_file, "r", encoding="utf-8") as f:
            description = f.read()

        return self._request("POST", "/merge_requests", {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": True,
        })


def print_usage():
    print("""GitLab API脚本 (Python 版本)

用法:
  gitlab.py issue create <title> <description_file> [labels]
  gitlab.py issue get <iid>
  gitlab.py mr create <source_branch> <title> <description_file> [target_branch]

说明:
  - description_file 必须是 UTF-8 markdown/text 文件
  - 推荐把 Issue / MR 描述先写入文件，再传给脚本""")


def main():
    """CLI 入口，匹配 gitlab.sh 接口。"""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        sys.exit(0 if sys.argv[1:] and sys.argv[1] in ("-h", "--help", "help") else 1)

    # 检查配置
    status, messages = check_config()
    if status != "CONFIG_OK":
        for msg in messages:
            print(msg, file=sys.stderr)
        sys.exit(1)

    config_path, _ = get_effective_config_path()
    config = load_config(config_path)
    client = GitLabClient(config)

    command = sys.argv[1]
    args = sys.argv[2:]

    try:
        if command == "issue":
            if not args:
                print_usage()
                sys.exit(1)
            sub = args[0]
            sub_args = args[1:]
            if sub == "create":
                if len(sub_args) < 2:
                    print("错误: 用法 issue create <title> <description_file> [labels]", file=sys.stderr)
                    sys.exit(1)
                title = sub_args[0]
                desc_file = sub_args[1]
                labels = sub_args[2] if len(sub_args) > 2 else "bug"
                result = client.create_issue(title, desc_file, labels)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            elif sub == "get":
                if not sub_args:
                    print("错误: 用法 issue get <iid>", file=sys.stderr)
                    sys.exit(1)
                result = client.get_issue(sub_args[0])
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_usage()
                sys.exit(1)
        elif command == "mr":
            if not args:
                print_usage()
                sys.exit(1)
            sub = args[0]
            sub_args = args[1:]
            if sub == "create":
                if len(sub_args) < 3:
                    print("错误: 用法 mr create <source_branch> <title> <description_file> [target_branch]", file=sys.stderr)
                    sys.exit(1)
                source = sub_args[0]
                title = sub_args[1]
                desc_file = sub_args[2]
                target = sub_args[3] if len(sub_args) > 3 else ""
                result = client.create_mr(source, title, desc_file, target)
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_usage()
                sys.exit(1)
        else:
            print_usage()
            sys.exit(1)
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
