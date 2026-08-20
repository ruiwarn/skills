#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class HostSpec(NamedTuple):
    alias: str
    hostname: str
    user: str
    fingerprint: str


DEFAULT_SPEC = HostSpec(
    alias="WRLinuxServer",
    hostname="172.17.0.252",
    user="wr",
    fingerprint="SHA256:4nyiQgTx8HN9npfnznf70lo+wPnNiGrMLx7OpOlcE4Y",
)
MANAGED_BEGIN = "# BEGIN maintain-ai-dashboard"
MANAGED_END = "# END maintain-ai-dashboard"


def run(
    command: list[str],
    *,
    input_text: str | None = None,
    timeout: int = 30,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode != 0:
        message = (result.stderr or result.stdout or "command failed").strip()
        raise RuntimeError(message[-1200:])
    return result


def require_commands(names: list[str]) -> None:
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise RuntimeError(f"缺少 OpenSSH 命令：{', '.join(missing)}")


def fingerprint_from_keyscan(keyscan_text: str) -> str:
    lines = [line for line in keyscan_text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise ValueError("没有读取到服务器 ED25519 公钥")
    result = run(["ssh-keygen", "-lf", "-"], input_text="\n".join(lines) + "\n", check=True)
    match = re.search(r"\b(SHA256:[A-Za-z0-9+/]+={0,2})\b", result.stdout)
    if not match:
        raise ValueError("无法解析服务器公钥指纹")
    return match.group(1)


def ed25519_entries(lookup_text: str) -> str:
    return "\n".join(
        line
        for line in lookup_text.splitlines()
        if not line.startswith("#") and len(line.split()) >= 3 and line.split()[1] == "ssh-ed25519"
    )


def has_host_alias(config_text: str, alias: str) -> bool:
    for line in config_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if parts and parts[0].lower() == "host" and alias in parts[1:]:
            return True
    return False


def render_host_block(spec: HostSpec, identity_file: Path | None) -> str:
    lines = [
        f"Host {spec.alias}",
        f"  HostName {spec.hostname}",
        f"  User {spec.user}",
        "  ForwardAgent yes",
        "  ServerAliveInterval 30",
        "  ServerAliveCountMax 3",
    ]
    if identity_file is not None:
        lines.extend([f"  IdentityFile {identity_file}", "  IdentitiesOnly yes"])
    return "\n".join(lines)


def upsert_managed_block(config_text: str, host_block: str) -> str:
    pattern = re.compile(
        rf"(?:^|\n){re.escape(MANAGED_BEGIN)}\n.*?\n{re.escape(MANAGED_END)}(?:\n|$)",
        re.DOTALL,
    )
    cleaned = pattern.sub("\n", config_text).strip()
    managed = f"{MANAGED_BEGIN}\n{host_block.rstrip()}\n{MANAGED_END}"
    return f"{cleaned}\n\n{managed}\n" if cleaned else f"{managed}\n"


def write_config(path: Path, content: str) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if path.exists():
        current = path.read_text(encoding="utf-8")
        if current == content:
            return None
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = path.with_name(f"{path.name}.bak.{timestamp}")
        shutil.copy2(path, backup)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        try:
            os.chmod(temporary_name, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)
    return backup


def batch_login(target: str, identity_file: Path | None = None) -> bool:
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        "-o",
        "StrictHostKeyChecking=yes",
    ]
    if identity_file is not None:
        command += ["-i", str(identity_file), "-o", "IdentitiesOnly=yes"]
    command += [target, "printf ssh-key-ready"]
    result = run(command, timeout=15)
    return result.returncode == 0 and result.stdout == "ssh-key-ready"


def fetch_server_key(spec: HostSpec) -> str:
    result = run(["ssh-keyscan", "-T", "8", "-t", "ed25519", spec.hostname], timeout=12, check=True)
    fingerprint = fingerprint_from_keyscan(result.stdout)
    if fingerprint != spec.fingerprint:
        raise RuntimeError(
            f"服务器指纹不一致，已停止。期望 {spec.fingerprint}，实际 {fingerprint}。请通过可信渠道确认。"
        )
    return next(line for line in result.stdout.splitlines() if line.strip() and not line.startswith("#"))


def install_known_host(known_hosts: Path, server_key: str, spec: HostSpec) -> None:
    known_hosts.parent.mkdir(parents=True, exist_ok=True)
    existing = known_hosts.read_text(encoding="utf-8") if known_hosts.exists() else ""
    lookup = run(["ssh-keygen", "-F", spec.hostname, "-f", str(known_hosts)]) if known_hosts.exists() else None
    if lookup and lookup.returncode == 0:
        entries = ed25519_entries(lookup.stdout)
        if entries and fingerprint_from_keyscan(entries) != spec.fingerprint:
            raise RuntimeError("known_hosts 中已有不同的服务器 ED25519 指纹，已停止")
    if server_key not in existing.splitlines():
        write_config(known_hosts, f"{existing.rstrip()}\n{server_key}\n".lstrip("\n"))


def generate_identity(identity_file: Path, spec: HostSpec) -> None:
    if identity_file.exists() and identity_file.with_suffix(identity_file.suffix + ".pub").exists():
        return
    identity_file.parent.mkdir(parents=True, exist_ok=True)
    comment = f"maintain-ai-dashboard@{socket.gethostname()}"
    run(
        ["ssh-keygen", "-t", "ed25519", "-f", str(identity_file), "-N", "", "-C", comment],
        timeout=30,
        check=True,
    )


def install_public_key(identity_file: Path, spec: HostSpec) -> None:
    public_key_path = Path(f"{identity_file}.pub")
    public_key = public_key_path.read_text(encoding="utf-8").strip()
    target = f"{spec.user}@{spec.hostname}"
    ssh_copy_id = shutil.which("ssh-copy-id")
    if ssh_copy_id:
        command = [
            ssh_copy_id,
            "-i",
            str(public_key_path),
            "-o",
            "StrictHostKeyChecking=yes",
            target,
        ]
        result = subprocess.run(command, check=False)
    else:
        remote = (
            "umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; "
            "key=$(cat); grep -qxF -- \"$key\" ~/.ssh/authorized_keys || "
            "printf '%s\\n' \"$key\" >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys"
        )
        command = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            "PubkeyAuthentication=no",
            "-o",
            "PreferredAuthentications=password,keyboard-interactive",
            target,
            remote,
        ]
        result = subprocess.run(command, input=public_key + "\n", text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError("公钥安装失败。密码只应在 SSH 提示符中输入；请确认账号和密码后重试。")


def check(spec: HostSpec, ssh_dir: Path) -> int:
    require_commands(["ssh", "ssh-keygen"])
    config_path = ssh_dir / "config"
    config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    alias_ready = has_host_alias(config, spec.alias) and batch_login(spec.alias)
    direct_ready = batch_login(f"{spec.user}@{spec.hostname}")
    if alias_ready:
        print(f"READY: {spec.alias} 已通过 SSH 密钥认证")
        return 0
    if direct_ready:
        print("KEY_READY_ALIAS_MISSING: 密钥认证已可用，请运行 --setup 创建标准别名")
        return 2
    print("NOT_READY: 尚未完成 SSH 密钥认证，请运行 --setup")
    return 2


def setup(spec: HostSpec, ssh_dir: Path) -> int:
    require_commands(["ssh", "ssh-keygen", "ssh-keyscan"])
    config_path = ssh_dir / "config"
    known_hosts = ssh_dir / "known_hosts"
    server_key = fetch_server_key(spec)
    print(f"已核对服务器 ED25519 指纹：{spec.fingerprint}")
    install_known_host(known_hosts, server_key, spec)

    config = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    if has_host_alias(config, spec.alias) and batch_login(spec.alias):
        print(f"READY: {spec.alias} 已通过 SSH 密钥认证，无需修改")
        return 0

    identity_file: Path | None = None
    direct_target = f"{spec.user}@{spec.hostname}"
    if not batch_login(direct_target):
        identity_file = ssh_dir / "id_ed25519_wr_ai_dashboard"
        generate_identity(identity_file, spec)
        if not batch_login(direct_target, identity_file):
            print("请在接下来的 SSH 提示符中输入一次服务器密码，用于安装当前电脑的公钥。")
            install_public_key(identity_file, spec)
        if not batch_login(direct_target, identity_file):
            raise RuntimeError("公钥已安装但批处理密钥登录仍失败，已停止")

    if has_host_alias(config, spec.alias) and MANAGED_BEGIN not in config:
        raise RuntimeError(f"SSH config 已有非托管的 {spec.alias} 配置，未自动覆盖；请人工核对")
    updated = upsert_managed_block(config, render_host_block(spec, identity_file))
    backup = write_config(config_path, updated)
    if backup:
        print(f"原 SSH config 已备份：{backup}")
    if not batch_login(spec.alias):
        raise RuntimeError(f"已写入配置，但 {spec.alias} 批处理密钥登录验证失败")
    print(f"READY: {spec.alias} 已完成 SSH 密钥认证")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="建立并验证 AI 报销看板服务器的 SSH 密钥认证")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="只读检查，不写入 SSH 文件")
    mode.add_argument("--setup", action="store_true", help="核对指纹并完成密钥和别名配置")
    parser.add_argument("--ssh-dir", type=Path, default=Path.home() / ".ssh", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        return check(DEFAULT_SPEC, args.ssh_dir) if args.check else setup(DEFAULT_SPEC, args.ssh_dir)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
