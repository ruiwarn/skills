"""Static regression checks for the zc-bug-fix operating contract."""

from pathlib import Path


SKILL_TEXT = (
    Path(__file__).resolve().parents[1] / "SKILL.md"
).read_text(encoding="utf-8")


def test_skill_contains_idempotency_guardrails():
    """Weak agents receive observable state rules, not optional advice."""
    assert "真实 Bug 不是测试环境" in SKILL_TEXT
    assert "browser='chrome'" in SKILL_TEXT
    assert "最终后置条件" in SKILL_TEXT
    assert "终态且分类不同" in SKILL_TEXT
    assert "停止并人工确认" in SKILL_TEXT


def test_skill_normalizes_classification_before_any_decision():
    """Agents must compare storage codes instead of code-versus-label text."""
    assert "目标中文分类 → 目标编码 → 当前 browser" in SKILL_TEXT
    assert (
        "| `设计_算法设计问题` | `chrome` | `chrome` | "
        "**已一致，跳过分类** |"
    ) in SKILL_TEXT
    assert "禁止拿 `chrome` 与中文分类名直接比较" in SKILL_TEXT


def test_skill_defines_the_only_safe_lifecycle_actions():
    """Partial and terminal states have one unambiguous next action."""
    assert (
        "| `active` | 已一致 | **只执行一次解决，然后最终回读** |"
    ) in SKILL_TEXT
    assert "不得建议“会后再自动编辑分类”" in SKILL_TEXT


def test_skill_contains_cross_platform_entrypoints():
    """The documented launch and file flow works on Windows and Linux."""
    assert "py -3" in SKILL_TEXT
    assert "python3" in SKILL_TEXT
    assert "init-config" in SKILL_TEXT
    assert "prepare-description" in SKILL_TEXT


def test_skill_has_no_unix_only_file_commands():
    """Platform-specific shell snippets cannot remain in the main workflow."""
    forbidden = (
        "python3 $SKILL_DIR",
        "cp $SKILL_DIR",
        "cat > /tmp",
        "<< 'EOF'",
        "2>/dev/null || true",
    )

    for item in forbidden:
        assert item not in SKILL_TEXT


def test_fallback_resolve_does_not_repeat_classification():
    """The fallback command must not edit classification after resolving."""
    unsafe = (
        'zentao-resolve <bug_id> "已创建 GitLab MR: <MR_URL>" '
        '"" "<bug_type>"'
    )

    assert unsafe not in SKILL_TEXT
