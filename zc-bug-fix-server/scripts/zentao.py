#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""禅道 API 操作脚本 - Python 版本。

使用 Python 标准库实现禅道 REST API 操作，基于 cookie 认证，无需外部依赖。
"""

import sys
import os
import json
import re
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar

# Add scripts dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_paths import get_effective_config_path
from check_config import load_config, load_effective_config, check_config


# ---------------------------------------------------------------------------
# Bug 类型映射表：bug 类型中文名 -> 禅道 browser 字段编码
# ---------------------------------------------------------------------------
BUG_TYPE_MAP = {
    "需求不清问题": "ie",
    "需求错误问题": "ie11",
    "设计_系统整体设计问题": "ie10",
    "设计_功能间接口问题": "ie9",
    "设计_功能交互问题": "ie8",
    "设计_边界值设计问题": "ie7",
    "设计_流程逻辑设计问题": "ie6",
    "设计_算法设计问题": "chrome",
    "编码_流程逻辑实现问题": "firefox",
    "编码_编程规范语法问题": "firefox3",
    "编码_编程规范内存问题": "firefox2",
    "编码_编程规范初始化": "opera",
    "编码_编程规范函数用错": "oprea11",
    "编码_编程规范指针调用": "oprea10",
    "编码_代码合并问题": "opera9",
    "编码_模块间接口问题": "safari",
    "编码_库使用问题": "maxthon",
    "编码_库修改问题": "uc",
    "编码-内核保护机制问题": "firefox4",
}

# 黑名单：这些类型禁止自动提交
BLACKLISTED_BUG_TYPES = {"", "继承或历史遗留", "未明确定位", "非问题"}


def map_bug_type_to_browser_code(bug_type: str) -> str:
    """将 bug 类型中文名映射为禅道 browser 字段编码。"""
    return BUG_TYPE_MAP.get(bug_type, "")


def is_blacklisted_bug_type(bug_type: str) -> bool:
    """判断 bug 类型是否在黑名单中。"""
    return bug_type in BLACKLISTED_BUG_TYPES


def format_zentao_clickable_links(comment: str) -> str:
    """将评论中的 GitLab issue/MR URL 转换为可点击的 HTML 链接。"""
    if "<a " in comment.lower():
        return comment

    pattern = re.compile(
        r'https?://[^\s<>"\']+/-/(?P<kind>issues|merge_requests)/(?P<iid>\d+)'
    )

    def replace_link(match):
        url = match.group(0)
        kind = match.group("kind")
        iid = match.group("iid")
        label = f"Issue #{iid}" if kind == "issues" else f"MR !{iid}"
        return f'<a href="{url}">{label}</a>'

    return pattern.sub(replace_link, comment)


# ---------------------------------------------------------------------------
# ZentaoClient - 禅道 API 客户端
# ---------------------------------------------------------------------------
class ZentaoClient:
    """禅道 REST API 客户端，使用 cookie 认证。"""

    def __init__(self, config: dict):
        self.base_url = config["ZENTAO_URL"]
        self.account = config["ZENTAO_ACCOUNT"]
        self.password = config["ZENTAO_PASSWORD"]
        self.project_owner = config.get("PROJECT_OWNER", "")
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def login(self):
        """登录禅道，将会话 cookie 存储在 opener 中。"""
        data = urllib.parse.urlencode({
            "account": self.account,
            "password": self.password,
        }).encode()
        url = f"{self.base_url}/user-login.json"
        req = urllib.request.Request(url, data=data, method="POST")
        resp = self.opener.open(req)
        body = json.loads(resp.read().decode())
        if not isinstance(body, dict) or body.get("status") != "success":
            raise RuntimeError(f"禅道登录失败: {body}")

    def fetch_bug_json(self, bug_id: str) -> dict:
        """获取 bug 原始 JSON 数据。"""
        url = f"{self.base_url}/bug-view-{bug_id}.json"
        req = urllib.request.Request(url)
        resp = self.opener.open(req)
        return json.loads(resp.read().decode())

    def extract_bug_field(self, payload: dict, field: str) -> str:
        """从禅道 bug JSON 中提取指定字段。

        兼容 data 为对象或 JSON 字符串两种格式。
        """
        bug = None
        if isinstance(payload, dict):
            if isinstance(payload.get("bug"), dict):
                bug = payload["bug"]
            else:
                data = payload.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        data = {}
                if isinstance(data, dict):
                    bug = data.get("bug", data)

        if not isinstance(bug, dict):
            bug = {}

        value = bug.get(field, "")
        if value is None:
            value = ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    # ---- 高层操作 ----

    def get_bug(self, bug_id: str) -> str:
        """获取 bug 并输出 Claude 可直读的干净 JSON。

        处理：
        1. 解嵌套：ZenTao API 的 data 字段是 JSON 字符串，自动展开
        2. 绝对图片 URL：将 /zentao/file-read-*.png 转换为完整 URL
        3. 输出格式：{"status":"success","bug":{...},"zentao_url":"..."}
        """
        self.login()
        raw = self.fetch_bug_json(bug_id)

        # -- 展开 data 嵌套 JSON 字符串 --
        bug = None
        try:
            data = raw.get("data", {})
            if isinstance(data, str):
                data = json.loads(data)
            bug = data.get("bug", data) if isinstance(data, dict) else {}
        except Exception:
            bug = {}

        if not isinstance(bug, dict):
            # 降级：返回原始结构
            return json.dumps(raw, ensure_ascii=False, indent=2)

        # -- 将相对图片路径替换为绝对 URL --
        base = self.base_url.rstrip("/")
        # base_url 通常是 http://host/zentao，取协议+主机部分
        origin = re.match(r"(https?://[^/]+)", base)
        origin = origin.group(1) if origin else base

        def abs_url(m: "re.Match") -> str:
            src = m.group(1)
            if src.startswith("http"):
                return m.group(0)
            return m.group(0).replace(src, origin + src)

        for field in ("steps", "description", "comment"):
            if field in bug and bug[field]:
                bug[field] = re.sub(r'src=["\']([^"\']+)["\']', abs_url, str(bug[field]))

        result = {
            "status": "success",
            "zentao_url": self.base_url,
            "bug": bug,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def get_bug_status(self, bug_id: str) -> str:
        """获取 bug 当前状态。"""
        payload = self.fetch_bug_json(bug_id)
        return self.extract_bug_field(payload, "status")

    def get_bug_confirmed(self, bug_id: str) -> str:
        """获取 bug 是否已确认。"""
        payload = self.fetch_bug_json(bug_id)
        return self.extract_bug_field(payload, "confirmed")

    def confirm_bug(self, bug_id: str, comment: str = "已确认"):
        """确认 bug。仅对 active 且未确认的 bug 执行。"""
        self.login()
        status = self.get_bug_status(bug_id)
        if not status:
            raise RuntimeError(f"无法读取 bug #{bug_id} 当前状态")
        if status != "active":
            print(f"跳过确认: bug #{bug_id} 当前状态为 '{status}'，只有 active 状态才需要 confirm")
            return
        confirmed = self.get_bug_confirmed(bug_id)
        if confirmed and confirmed != "0":
            print(f"跳过确认: bug #{bug_id} 当前 confirmed={confirmed}，无需重复 confirm")
            return

        data = urllib.parse.urlencode({"comment": comment}).encode()
        url = f"{self.base_url}/bug-confirmBug-{bug_id}.json"
        req = urllib.request.Request(url, data=data, method="POST")
        resp = self.opener.open(req)
        body = resp.read().decode()
        self._ensure_response_ok("confirm", bug_id, body)
        print(body)

    def resolve_bug(self, bug_id: str, resolution: str = "fixed",
                    comment: str = "已修复", assigned_to: str = "",
                    bug_type: str = ""):
        """解决 bug。已处于终态的 bug 会跳过。"""
        self.login()
        status = self.get_bug_status(bug_id)
        if not status:
            raise RuntimeError(f"无法读取 bug #{bug_id} 当前状态")
        if status in ("resolved", "closed"):
            print(f"跳过解决: bug #{bug_id} 当前状态为 '{status}'，已经是终态")
            return

        if not assigned_to:
            assigned_to = self.project_owner

        data = urllib.parse.urlencode({
            "resolution": resolution,
            "comment": comment,
            "assignedTo": assigned_to,
        }).encode()
        url = f"{self.base_url}/bug-resolve-{bug_id}.json"
        req = urllib.request.Request(url, data=data, method="POST")
        resp = self.opener.open(req)
        body = resp.read().decode()
        self._ensure_response_ok("resolve", bug_id, body)
        print(body)

        if bug_type:
            self.update_bug_browser_type(bug_id, bug_type)

    def update_bug_browser_type(self, bug_id: str, bug_type: str):
        """更新 bug 的 browser 字段为 bug 类型分类编码。"""
        if not bug_id or not bug_type:
            raise ValueError("bug_id 和 bug_type 不能为空")

        if is_blacklisted_bug_type(bug_type):
            raise ValueError(f"bug 类型 '{bug_type}' 在黑名单中，禁止自动提交")

        browser_code = map_bug_type_to_browser_code(bug_type)
        if not browser_code:
            raise ValueError(f"未识别的 bug 类型 '{bug_type}'，请人工确认后再提交")

        self.login()
        bug_json = self.fetch_bug_json(bug_id)

        # 提取当前 bug 数据以保留必填字段
        bug = None
        if isinstance(bug_json, dict):
            if isinstance(bug_json.get("bug"), dict):
                bug = bug_json["bug"]
            else:
                data = bug_json.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        data = {}
                if isinstance(data, dict):
                    bug = data.get("bug", data)
        if not isinstance(bug, dict):
            bug = {}

        # openedBuild 是 bug-edit 的必填字段，缺失会导致禅道静默忽略更新
        opened_build = self.extract_bug_field(bug_json, "openedBuild") if bug_json else ""
        product = bug.get("product", "")
        project = bug.get("project", "")

        fields = {
            "title":    bug.get("title", ""),
            "severity": bug.get("severity", "3"),
            "pri":      bug.get("pri", "3"),
            "type":     bug.get("type", "codeerror"),
            "browser":  browser_code,
        }
        if opened_build:
            fields["openedBuild"] = opened_build
        if product:
            fields["product"] = product
        if project:
            fields["project"] = project
        form_data = urllib.parse.urlencode(fields).encode()

        url = f"{self.base_url}/bug-edit-{bug_id}.json"
        req = urllib.request.Request(url, data=form_data, method="POST")
        resp = self.opener.open(req)
        body = resp.read().decode()
        self._ensure_response_ok("set-browser-type", bug_id, body)
        print(body)

    def add_bug_comment(self, bug_id: str, comment: str):
        """向禅道 bug 添加评论（不改变状态）。

        bug-edit 需要所有必填字段（含 openedBuild/影响版本），
        先读取 bug 当前数据，拿到 openedBuild 后再提交。
        """
        if not bug_id or not comment:
            raise ValueError("bug_id 和 comment 不能为空")
        self.login()
        # 读取当前 bug 必填字段，避免"影响版本不能为空"报错
        opened_build = ""
        product = ""
        project = ""
        try:
            raw = self.fetch_bug_json(bug_id)
            opened_build = self.extract_bug_field(raw, "openedBuild")
            product = self.extract_bug_field(raw, "product")
            project = self.extract_bug_field(raw, "project")
        except Exception:
            pass  # 读取失败时忽略，让禅道返回错误
        fields = {"comment": comment}
        if opened_build:
            fields["openedBuild"] = opened_build
        if product:
            fields["product"] = product
        if project:
            fields["project"] = project
        data = urllib.parse.urlencode(fields).encode()
        url = f"{self.base_url}/bug-edit-{bug_id}.json"
        req = urllib.request.Request(url, data=data, method="POST")
        resp = self.opener.open(req)
        body = resp.read().decode()
        self._ensure_response_ok("add-comment", bug_id, body)
        print(body)

    def _ensure_response_ok(self, action: str, bug_id: str, response: str):
        """检查禅道响应是否包含失败标志。"""
        if '"status":"fail"' in response or '"result":"fail"' in response:
            raise RuntimeError(
                f"禅道 {action} 失败。bug #{bug_id} 返回内容: {response}"
            )


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------
def print_usage():
    print("""禅道脚本 (Python 版本)

用法:
  zentao.py get <bug_id>
  zentao.py confirm <bug_id> [comment]
  zentao.py set-browser-type <bug_id> <bug_type>
  zentao.py resolve <bug_id> [resolution] [comment] [assigned_to] [bug_type]

说明:
  resolve 默认会在解决后转派给 zc-bug-fix.config 中的 PROJECT_OWNER
  set-browser-type / resolve 只允许提交白名单中的明确 bug 类型
  黑名单禁止项：继承或历史遗留、未明确定位、非问题、空值""")


def main():
    """CLI 入口，兼容旧命令行接口。"""
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print_usage()
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    # 检查配置
    status, messages = check_config()
    if status != "CONFIG_OK":
        for msg in messages:
            print(msg, file=sys.stderr)
        sys.exit(1)

    config = load_effective_config()
    client = ZentaoClient(config)

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "get":
        if not args:
            print("错误: 用法 get <bug_id>", file=sys.stderr)
            sys.exit(1)
        print(client.get_bug(args[0]))
    elif command == "confirm":
        if not args:
            print("错误: 用法 confirm <bug_id> [comment]", file=sys.stderr)
            sys.exit(1)
        comment = args[1] if len(args) > 1 else "已确认"
        client.confirm_bug(args[0], comment)
    elif command == "set-browser-type":
        if len(args) < 2:
            print("错误: 用法 set-browser-type <bug_id> <bug_type>", file=sys.stderr)
            sys.exit(1)
        client.update_bug_browser_type(args[0], args[1])
    elif command == "resolve":
        if not args:
            print("错误: 用法 resolve <bug_id> [resolution] [comment] [assigned_to] [bug_type]", file=sys.stderr)
            sys.exit(1)
        resolution = args[1] if len(args) > 1 else "fixed"
        comment = args[2] if len(args) > 2 else "已修复"
        assigned_to = args[3] if len(args) > 3 else ""
        bug_type = args[4] if len(args) > 4 else ""
        client.resolve_bug(args[0], resolution, comment, assigned_to, bug_type)
    else:
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
