#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


REMOTE_PROBE = r'''
import json
import os
import re
import sqlite3
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlsplit


def http_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def http_status(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status


def service_status(container):
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", container],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "missing"


def remote_key(value):
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname.lower()
        if parsed.port:
            host += f":{parsed.port}"
        path = parsed.path
    else:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", value)
        host, path = (match.group(1).lower(), match.group(2)) if match else ("", value)
    path = unquote(path).strip("/")
    if path.lower().endswith(".git"):
        path = path[:-4]
    return f"{host}/{path}" if host else path


app = Path("/home/wr/ai-dashboard/app")
database = Path("/home/wr/ai-dashboard/data/dashboard.sqlite3")
source_root = Path("/home/wr/git")
backup_dir = Path("/home/wr/ai-dashboard/backups")
report = {
    "hostname": os.uname().nodename,
    "paths": {
        "app": (app / "docker-compose.yml").is_file(),
        "database": database.is_file(),
        "source_root": source_root.is_dir(),
    },
    "api_health": http_json("http://172.17.0.252:18089/api/health"),
    "web_status": http_status("http://172.17.0.252:18088"),
    "services": {
        "api": service_status("ai-reimbursement-api"),
        "web": service_status("ai-reimbursement-web"),
    },
    "project_count": 0,
    "duplicate_remote_count": 0,
    "database_quick_check": "missing",
    "backup_directory_writable": backup_dir.is_dir() and os.access(backup_dir, os.W_OK),
}

if database.is_file():
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True, timeout=10)
    connection.execute("PRAGMA query_only = ON")
    report["database_quick_check"] = connection.execute("PRAGMA quick_check").fetchone()[0]
    remotes = [row[0] for row in connection.execute("SELECT remote_url FROM projects")]
    report["project_count"] = len(remotes)
    keys = [remote_key(value) for value in remotes]
    report["duplicate_remote_count"] = len(keys) - len(set(keys))
    connection.close()

print(json.dumps(report, ensure_ascii=False))
'''


def run_preflight(alias: str = "WRLinuxServer", timeout: int = 30) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=8",
            alias,
            "python3",
            "-",
        ],
        input=REMOTE_PROBE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "SSH preflight failed").strip()
        raise RuntimeError(message[-1200:])
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("服务器预检没有返回有效 JSON") from exc


def evaluate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for name, ready in report.get("paths", {}).items():
        if not ready:
            errors.append(f"required path is missing: {name}")
    if not report.get("api_health", {}).get("ok"):
        errors.append("API health check failed")
    if report.get("api_health", {}).get("sync", {}).get("running"):
        errors.append("dashboard sync is running")
    if report.get("web_status") != 200:
        errors.append(f"web status is not 200: {report.get('web_status')}")
    for name in ("api", "web"):
        if report.get("services", {}).get(name) != "running":
            errors.append(f"service {name} is not running")
    duplicate_count = int(report.get("duplicate_remote_count", 0))
    if duplicate_count:
        errors.append(f"duplicate project remotes found: {duplicate_count}")
    if report.get("database_quick_check") != "ok":
        errors.append("database quick_check failed")
    if not report.get("backup_directory_writable"):
        errors.append("backup directory is not writable")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="只读检查 AI 编程报销看板服务器")
    parser.add_argument("--alias", default="WRLinuxServer")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    try:
        report = run_preflight(args.alias, args.timeout)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        errors = evaluate_report(report)
        if errors:
            print("BLOCKED:", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 2
        print("READY: SSH、服务、数据库和备份条件均正常")
        return 0
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
