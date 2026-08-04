"""Cross-version and cross-platform tests for zc-bug-fix helpers."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import bugfix_flow  # noqa: E402
import check_config  # noqa: E402


def test_load_config_accepts_utf8_bom_and_crlf(tmp_path):
    """Windows-style UTF-8 BOM and CRLF config files must load cleanly."""
    config_path = tmp_path / "zc-bug-fix.config"
    config_path.write_bytes(
        b"\xef\xbb\xbfZENTAO_URL=http://example.test\r\n"
        b"ZENTAO_ACCOUNT=tester\r\n"
    )

    config = check_config.load_config(str(config_path))

    assert config["ZENTAO_URL"] == "http://example.test"
    assert config["ZENTAO_ACCOUNT"] == "tester"


def test_initialize_config_copies_without_overwriting(tmp_path, monkeypatch):
    """Initialization creates parent folders and refuses to replace credentials."""
    source = tmp_path / "zc-bug-fix.config.example"
    source.write_text("KEY=value\n", encoding="utf-8")
    target = tmp_path / "project" / "zc-bug-fix.config"
    monkeypatch.setattr(bugfix_flow, "get_example_path", lambda: str(source))
    monkeypatch.setattr(
        bugfix_flow, "get_preferred_config_path", lambda: str(target)
    )

    result = bugfix_flow.initialize_config()

    assert result == str(target)
    assert target.read_text(encoding="utf-8") == "KEY=value\n"
    with pytest.raises(FileExistsError, match="拒绝覆盖"):
        bugfix_flow.initialize_config()


@pytest.mark.parametrize(
    ("kind", "template_name"),
    [
        ("issue", "issue_6d_template.md"),
        ("mr", "mr_template.md"),
    ],
)
def test_prepare_description_uses_system_temp(
    kind, template_name, tmp_path, monkeypatch
):
    """Description templates are copied to an absolute system-temp path."""
    template = tmp_path / template_name
    template.write_text("template\n", encoding="utf-8")
    monkeypatch.setattr(
        bugfix_flow, "DESCRIPTION_TEMPLATES", {kind: template}
    )

    result = Path(bugfix_flow.prepare_description(kind, "5495"))

    try:
        assert result.is_absolute()
        assert result.read_text(encoding="utf-8") == "template\n"
        assert "5495" in result.name
    finally:
        result.unlink()


def test_prepare_description_rejects_unknown_kind():
    """Only the two bundled templates are accepted."""
    with pytest.raises(ValueError, match="issue 或 mr"):
        bugfix_flow.prepare_description("other", "5495")


def test_prepare_description_requires_bug_id():
    """Temporary filenames must include a non-empty Bug ID."""
    with pytest.raises(ValueError, match="bug_id"):
        bugfix_flow.prepare_description("issue", "")
