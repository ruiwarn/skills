"""Tests for the meter-cmd Python wrapper."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def load_meter_cmd_module():
    """Load meter-cmd.py as a module for direct unit testing."""
    script_path = Path(__file__).resolve().parents[1] / "meter-cmd.py"
    spec = importlib.util.spec_from_file_location("meter_cmd_wrapper", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_command_uses_python_exe_in_wsl(tmp_path, monkeypatch):
    module = load_meter_cmd_module()
    cli_path = tmp_path / "scripts" / "protocol_cli.py"
    cli_path.parent.mkdir()
    cli_path.write_text("# test\n", encoding="utf-8")

    monkeypatch.setattr(module, "resolve_cli_path", lambda: cli_path)
    monkeypatch.setattr(module, "is_wsl", lambda environ=None: True)
    monkeypatch.setattr(module, "to_windows_path", lambda path: r"C:\skill\scripts\protocol_cli.py")

    command = module.build_command(["port=COM10", "proto=645"], {})
    assert command == [
        "python.exe",
        r"C:\skill\scripts\protocol_cli.py",
        "port=COM10",
        "proto=645",
    ]


def test_build_command_uses_override_interpreter(tmp_path, monkeypatch):
    module = load_meter_cmd_module()
    cli_path = tmp_path / "scripts" / "protocol_cli.py"
    cli_path.parent.mkdir()
    cli_path.write_text("# test\n", encoding="utf-8")

    monkeypatch.setattr(module, "resolve_cli_path", lambda: cli_path)
    monkeypatch.setattr(module, "is_wsl", lambda environ=None: True)
    monkeypatch.setattr(module, "to_windows_path", lambda path: r"D:\skill\protocol_cli.py")

    command = module.build_command(["help"], {"METER_CMD_PYTHON": r"D:\Python\python.exe"})
    assert command[0] == r"D:\Python\python.exe"
    assert command[1] == r"D:\skill\protocol_cli.py"
    assert command[2:] == ["help"]


def test_build_command_uses_local_python_outside_wsl(tmp_path, monkeypatch):
    module = load_meter_cmd_module()
    cli_path = tmp_path / "scripts" / "protocol_cli.py"
    cli_path.parent.mkdir()
    cli_path.write_text("# test\n", encoding="utf-8")

    monkeypatch.setattr(module, "resolve_cli_path", lambda: cli_path)
    monkeypatch.setattr(module, "is_wsl", lambda environ=None: False)

    command = module.build_command(["proto=698"], {})
    assert command == [sys.executable, str(cli_path), "proto=698"]


def test_main_returns_child_exit_code(monkeypatch):
    module = load_meter_cmd_module()

    monkeypatch.setattr(module, "build_command", lambda argv: ["python3", "protocol_cli.py", *argv])

    class DummyCompleted:
        returncode = 7

    monkeypatch.setattr(module.subprocess, "run", lambda command: DummyCompleted())

    assert module.main(["proto=645"]) == 7


def test_main_reports_wslpath_failure(monkeypatch, capsys):
    module = load_meter_cmd_module()
    error = subprocess.CalledProcessError(1, ["wslpath", "-w", "/tmp/x"])
    monkeypatch.setattr(module, "build_command", lambda argv: (_ for _ in ()).throw(error))

    assert module.main(["help"]) == 2
    captured = capsys.readouterr()
    assert "wslpath 路径转换失败" in captured.err
