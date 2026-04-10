"""Tests for the zc-bug-fix Python modules.

Replaces the bash-based config_resolution_test.sh with pytest tests that
validate config_paths, check_config, zentao, and bugfix_flow modules.
"""

import os
import sys
import textwrap

import pytest

# ---------------------------------------------------------------------------
# Path setup – allow imports from the sibling ``scripts/`` package.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import config_paths  # noqa: E402
import check_config  # noqa: E402
import zentao  # noqa: E402
import bugfix_flow  # noqa: E402

# ---------------------------------------------------------------------------
# Shared fixtures & helpers
# ---------------------------------------------------------------------------

VALID_CONFIG = textwrap.dedent("""\
    ZENTAO_URL=http://127.0.0.1:9191/zentao
    ZENTAO_ACCOUNT=tester
    ZENTAO_PASSWORD=secret
    GITLAB_URL=http://127.0.0.1:8080
    GITLAB_TOKEN=test-token
    GITLAB_PROJECT_ID=123
    TARGET_BRANCH=develop
    PROJECT_OWNER=test-owner
""")


def _write_config(path, content=VALID_CONFIG):
    """Write *content* to *path*, creating parent directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _fake_git_project_root(monkeypatch, project_dir):
    """Make ``get_project_root()`` return *project_dir* without a real repo."""
    monkeypatch.setattr(config_paths, "get_project_root", lambda: str(project_dir))


# =========================================================================
# 1. Config path resolution
# =========================================================================


class TestConfigPathResolution:
    """Verify preferred / effective config path logic."""

    def test_project_default_config(self, tmp_path, monkeypatch):
        """Config at <project_root>/zc-bug-fix.config → CONFIG_OK."""
        project_dir = tmp_path / "project-default"
        project_dir.mkdir()
        _write_config(str(project_dir / config_paths.CONFIG_NAME))

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, messages = check_config.check_config()
        assert status == "CONFIG_OK", f"Expected CONFIG_OK, got {status}: {messages}"

    def test_relative_env_override(self, tmp_path, monkeypatch):
        """ZC_BUG_FIX_CONFIG with a relative path resolves against project root."""
        project_dir = tmp_path / "project-env"
        project_dir.mkdir()
        configs_dir = project_dir / "configs"
        configs_dir.mkdir()
        _write_config(str(configs_dir / "custom.config"))

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.setenv("ZC_BUG_FIX_CONFIG", "configs/custom.config")

        preferred = config_paths.get_preferred_config_path()
        assert preferred == str(project_dir / "configs" / "custom.config")

        status, messages = check_config.check_config()
        assert status == "CONFIG_OK", f"Expected CONFIG_OK, got {status}: {messages}"

    def test_absolute_env_override(self, tmp_path, monkeypatch):
        """ZC_BUG_FIX_CONFIG with an absolute path is used as-is."""
        project_dir = tmp_path / "project-abs"
        project_dir.mkdir()
        abs_config = tmp_path / "elsewhere" / "my.config"
        _write_config(str(abs_config))

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.setenv("ZC_BUG_FIX_CONFIG", str(abs_config))

        preferred = config_paths.get_preferred_config_path()
        assert preferred == str(abs_config)

        status, _ = check_config.check_config()
        assert status == "CONFIG_OK"

    def test_non_target_config_ignored(self, tmp_path, monkeypatch):
        """Config placed in the wrong location must NOT be picked up."""
        project_dir = tmp_path / "project-non-target"
        project_dir.mkdir()

        # Put config in a location that is *not* the expected path
        wrong_dir = tmp_path / "skill-copy"
        wrong_dir.mkdir()
        _write_config(str(wrong_dir / ".config"))

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, messages = check_config.check_config()
        assert status == "MISSING_CONFIG"
        # Hint must reference the project-level path
        full_hint = "\n".join(messages)
        assert str(project_dir / config_paths.CONFIG_NAME) in full_hint


# =========================================================================
# 2. Missing config & hint messages
# =========================================================================


class TestMissingConfigHints:
    """When no config file exists, the user receives actionable hints."""

    def test_missing_config_hint(self, tmp_path, monkeypatch):
        """Missing config returns MISSING_CONFIG with project path in message."""
        project_dir = tmp_path / "project-missing"
        project_dir.mkdir()

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, messages = check_config.check_config()
        assert status == "MISSING_CONFIG"

        full_hint = "\n".join(messages)
        expected_path = str(project_dir / config_paths.CONFIG_NAME)
        assert expected_path in full_hint, (
            f"Hint should mention '{expected_path}', got: {full_hint}"
        )
        assert config_paths.EXAMPLE_NAME in full_hint, (
            f"Hint should mention example file '{config_paths.EXAMPLE_NAME}'"
        )

    def test_config_hint_output(self, tmp_path, monkeypatch):
        """config_hint text contains project-level config path and example name."""
        project_dir = tmp_path / "project-hint"
        project_dir.mkdir()

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        preferred = config_paths.get_preferred_config_path()
        example = config_paths.get_example_path()

        assert str(project_dir) in preferred
        assert config_paths.CONFIG_NAME in preferred
        assert config_paths.EXAMPLE_NAME in example


# =========================================================================
# 3. Field validation
# =========================================================================


class TestFieldValidation:
    """check_config must reject configs that are missing required fields."""

    REQUIRED_FIELDS = [
        "ZENTAO_URL",
        "ZENTAO_ACCOUNT",
        "ZENTAO_PASSWORD",
        "GITLAB_URL",
        "GITLAB_TOKEN",
        "GITLAB_PROJECT_ID",
        "PROJECT_OWNER",
    ]

    def test_missing_fields(self, tmp_path, monkeypatch):
        """Config with only a subset of fields returns MISSING_FIELD errors."""
        project_dir = tmp_path / "project-fields"
        project_dir.mkdir()

        partial_config = textwrap.dedent("""\
            ZENTAO_URL=http://127.0.0.1:9191/zentao
            ZENTAO_ACCOUNT=tester
            # ZENTAO_PASSWORD intentionally missing
            GITLAB_URL=http://127.0.0.1:8080
            # GITLAB_TOKEN intentionally missing
            GITLAB_PROJECT_ID=123
            PROJECT_OWNER=test-owner
        """)
        _write_config(str(project_dir / config_paths.CONFIG_NAME), partial_config)

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, messages = check_config.check_config()
        assert status == "MISSING_FIELD"

        joined = "\n".join(messages)
        assert "ZENTAO_PASSWORD" in joined
        assert "GITLAB_TOKEN" in joined

    def test_all_fields_present(self, tmp_path, monkeypatch):
        """Config with every required field returns CONFIG_OK."""
        project_dir = tmp_path / "project-full"
        project_dir.mkdir()
        _write_config(str(project_dir / config_paths.CONFIG_NAME))

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, _ = check_config.check_config()
        assert status == "CONFIG_OK"

    def test_empty_value_counts_as_missing(self, tmp_path, monkeypatch):
        """A key with an empty value (e.g. ``KEY=``) is treated as missing."""
        project_dir = tmp_path / "project-empty-val"
        project_dir.mkdir()

        config_with_empty = textwrap.dedent("""\
            ZENTAO_URL=http://127.0.0.1:9191/zentao
            ZENTAO_ACCOUNT=tester
            ZENTAO_PASSWORD=
            GITLAB_URL=http://127.0.0.1:8080
            GITLAB_TOKEN=test-token
            GITLAB_PROJECT_ID=123
            PROJECT_OWNER=test-owner
        """)
        _write_config(str(project_dir / config_paths.CONFIG_NAME), config_with_empty)

        _fake_git_project_root(monkeypatch, project_dir)
        monkeypatch.delenv("ZC_BUG_FIX_CONFIG", raising=False)

        status, messages = check_config.check_config()
        assert status == "MISSING_FIELD"
        assert any("ZENTAO_PASSWORD" in m for m in messages)


# =========================================================================
# 4. Zentao helpers
# =========================================================================


class TestZentaoBugTypeMapping:
    """Validate map_bug_type_to_browser_code against the full mapping table."""

    KNOWN_MAPPINGS = [
        ("需求不清问题", "ie"),
        ("需求错误问题", "ie11"),
        ("设计_系统整体设计问题", "ie10"),
        ("设计_功能间接口问题", "ie9"),
        ("设计_功能交互问题", "ie8"),
        ("设计_边界值设计问题", "ie7"),
        ("设计_流程逻辑设计问题", "ie6"),
        ("设计_算法设计问题", "chrome"),
        ("编码_流程逻辑实现问题", "firefox"),
        ("编码_编程规范语法问题", "firefox3"),
        ("编码_编程规范内存问题", "firefox2"),
        ("编码_编程规范初始化", "opera"),
        ("编码_编程规范函数用错", "oprea11"),
        ("编码_编程规范指针调用", "oprea10"),
        ("编码_代码合并问题", "opera9"),
        ("编码_模块间接口问题", "safari"),
        ("编码_库使用问题", "maxthon"),
        ("编码_库修改问题", "uc"),
        ("编码-内核保护机制问题", "firefox4"),
    ]

    @pytest.mark.parametrize("bug_type,expected_code", KNOWN_MAPPINGS)
    def test_zentao_bug_type_mapping(self, bug_type, expected_code):
        result = zentao.map_bug_type_to_browser_code(bug_type)
        assert result == expected_code, (
            f"map_bug_type_to_browser_code({bug_type!r}) → {result!r}, "
            f"expected {expected_code!r}"
        )

    def test_unknown_type_returns_empty(self):
        assert zentao.map_bug_type_to_browser_code("完全未知类型") == ""

    def test_empty_string_returns_empty(self):
        assert zentao.map_bug_type_to_browser_code("") == ""


class TestZentaoBlacklistedTypes:
    """is_blacklisted_bug_type rejects known non-actionable categories."""

    BLACKLISTED = ["", "继承或历史遗留", "未明确定位", "非问题"]
    ALLOWED = [
        "需求不清问题",
        "编码_流程逻辑实现问题",
        "设计_算法设计问题",
    ]

    @pytest.mark.parametrize("bug_type", BLACKLISTED)
    def test_zentao_blacklisted_types(self, bug_type):
        assert zentao.is_blacklisted_bug_type(bug_type) is True, (
            f"{bug_type!r} should be blacklisted"
        )

    @pytest.mark.parametrize("bug_type", ALLOWED)
    def test_allowed_types_not_blacklisted(self, bug_type):
        assert zentao.is_blacklisted_bug_type(bug_type) is False, (
            f"{bug_type!r} should NOT be blacklisted"
        )


class TestFormatClickableLinks:
    """format_zentao_clickable_links wraps bare URLs in HTML anchors."""

    def test_issue_link_wrapped(self):
        comment = "已创建 GitLab issue: http://172.17.0.100:8080/group/proj/-/issues/42"
        result = zentao.format_zentao_clickable_links(comment)
        assert '<a href="http://172.17.0.100:8080/group/proj/-/issues/42">Issue #42</a>' in result

    def test_mr_link_wrapped(self):
        comment = "已创建 MR: http://172.17.0.100:8080/group/proj/-/merge_requests/7"
        result = zentao.format_zentao_clickable_links(comment)
        assert '<a href="http://172.17.0.100:8080/group/proj/-/merge_requests/7">MR !7</a>' in result

    def test_existing_html_not_double_wrapped(self):
        comment = '<a href="http://x/-/issues/1">Issue #1</a>'
        result = zentao.format_zentao_clickable_links(comment)
        assert result == comment, "Already-HTML links must not be modified"

    def test_plain_text_unchanged(self):
        comment = "这是一段纯文本，不含链接"
        result = zentao.format_zentao_clickable_links(comment)
        assert result == comment

    def test_multiple_links(self):
        comment = (
            "Issue: http://172.17.0.100:8080/g/p/-/issues/10 "
            "MR: http://172.17.0.100:8080/g/p/-/merge_requests/20"
        )
        result = zentao.format_zentao_clickable_links(comment)
        assert "Issue #10" in result
        assert "MR !20" in result


# =========================================================================
# 5. URL validation (bugfix_flow)
# =========================================================================


class TestUrlValidation:
    """Validate GitLab issue / MR URL detection used by bugfix_flow."""

    VALID_ISSUE_URLS = [
        "http://172.17.0.100:8080/group/project/-/issues/1",
        "https://gitlab.example.com/org/repo/-/issues/999",
        "http://localhost:8080/a/b/-/issues/42",
    ]

    INVALID_ISSUE_URLS = [
        "",
        "not a url",
        "http://172.17.0.100:8080/group/project/-/merge_requests/1",
        "http://172.17.0.100:8080/group/project/issues/1",  # missing /-/
    ]

    VALID_MR_URLS = [
        "http://172.17.0.100:8080/group/project/-/merge_requests/1",
        "https://gitlab.example.com/org/repo/-/merge_requests/55",
    ]

    INVALID_MR_URLS = [
        "",
        "not a url",
        "http://172.17.0.100:8080/group/project/-/issues/1",
        "http://172.17.0.100:8080/group/project/merge_requests/1",  # missing /-/
    ]

    @pytest.mark.parametrize("url", VALID_ISSUE_URLS)
    def test_valid_issue_links(self, url):
        assert bugfix_flow.contains_gitlab_issue_link(url) is True

    @pytest.mark.parametrize("url", INVALID_ISSUE_URLS)
    def test_invalid_issue_links(self, url):
        assert bugfix_flow.contains_gitlab_issue_link(url) is False

    @pytest.mark.parametrize("url", VALID_MR_URLS)
    def test_valid_mr_links(self, url):
        assert bugfix_flow.contains_gitlab_mr_link(url) is True

    @pytest.mark.parametrize("url", INVALID_MR_URLS)
    def test_invalid_mr_links(self, url):
        assert bugfix_flow.contains_gitlab_mr_link(url) is False

    def test_issue_link_embedded_in_text(self):
        text = "已创建 GitLab issue: http://host:8080/g/p/-/issues/5 请确认"
        assert bugfix_flow.contains_gitlab_issue_link(text) is True

    def test_mr_link_embedded_in_text(self):
        text = "MR 链接: https://gitlab.local/o/r/-/merge_requests/12 done"
        assert bugfix_flow.contains_gitlab_mr_link(text) is True
