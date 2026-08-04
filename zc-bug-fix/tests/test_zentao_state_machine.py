"""State-machine tests for safe, idempotent Zentao writeback."""

import os
import sys
import inspect
from urllib.parse import parse_qs, urlparse

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import zentao  # noqa: E402
import bugfix_flow  # noqa: E402


TYPE_NAME = "设计_算法设计问题"
TYPE_CODE = "chrome"
ISSUE_URL = "http://gitlab.example/group/project/-/issues/11"
MR_URL = "http://gitlab.example/group/project/-/merge_requests/42"


def bug_payload(status="active", browser="firefox", opened_build="trunk"):
    """Build the Zentao payload shape used by the production client."""
    return {
        "bug": {
            "title": "sample",
            "severity": "3",
            "pri": "3",
            "type": "codeerror",
            "status": status,
            "confirmed": "1",
            "browser": browser,
            "openedBuild": opened_build,
            "resolution": "fixed",
            "assignedTo": "owner",
        }
    }


class FakeResponse:
    """Minimal urllib response."""

    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body.encode("utf-8")


class RecordingOpener:
    """Record write requests and return configured response bodies."""

    def __init__(self, bodies=None, events=None):
        self.bodies = list(bodies or ["<script>parent.location='ok'</script>"])
        self.requests = []
        self.events = events

    def open(self, request):
        self.requests.append(request)
        if self.events is not None:
            path = urlparse(request.full_url).path
            if "/bug-resolve-" in path:
                self.events.append("resolve")
            elif "/bug-edit-" in path:
                self.events.append("classify")
        body = self.bodies.pop(0) if self.bodies else ""
        return FakeResponse(body)


def make_client(monkeypatch, snapshots, opener=None):
    """Create a client whose reads and writes are fully local."""
    client = zentao.ZentaoClient(
        {
            "ZENTAO_URL": "http://zentao.example",
            "ZENTAO_ACCOUNT": "tester",
            "ZENTAO_PASSWORD": "secret",
            "PROJECT_OWNER": "owner",
        }
    )
    client.opener = opener or RecordingOpener()
    monkeypatch.setattr(client, "login", lambda: None)
    queued = list(snapshots)

    def fetch(_bug_id):
        if not queued:
            raise AssertionError("unexpected extra Bug snapshot read")
        return queued.pop(0)

    monkeypatch.setattr(client, "fetch_bug_json", fetch)
    return client


def test_extract_bug_supports_json_string_data():
    """Raw Bug dictionaries are normalized from both supported payload shapes."""
    payload = {
        "data": (
            '{"bug":{"status":"resolved","browser":"chrome",'
            '"openedBuild":"trunk"}}'
        )
    }

    bug = zentao.ZentaoClient.extract_bug(payload)

    assert bug["status"] == "resolved"
    assert bug["browser"] == "chrome"


def test_terminal_bug_with_matching_type_does_not_write(monkeypatch):
    """An already-correct terminal Bug is a pure no-op."""
    opener = RecordingOpener()
    client = make_client(
        monkeypatch,
        [bug_payload(status="resolved", browser=TYPE_CODE)],
        opener,
    )

    changed = client.update_bug_browser_type("5495", TYPE_NAME)

    assert changed is False
    assert opener.requests == []


def test_terminal_bug_with_different_type_fails_closed(monkeypatch):
    """A terminal Bug must never be edited to repair classification."""
    opener = RecordingOpener()
    client = make_client(
        monkeypatch,
        [bug_payload(status="resolved", browser="firefox")],
        opener,
    )

    with pytest.raises(RuntimeError, match="终态"):
        client.update_bug_browser_type("5495", TYPE_NAME)

    assert opener.requests == []


def test_active_edit_preserves_opened_build_and_verifies_result(monkeypatch):
    """An active Bug edit preserves required fields and verifies the result."""
    opener = RecordingOpener()
    client = make_client(
        monkeypatch,
        [
            bug_payload(status="active", browser="firefox"),
            bug_payload(status="active", browser=TYPE_CODE),
        ],
        opener,
    )

    changed = client.update_bug_browser_type("5495", TYPE_NAME)

    assert changed is True
    assert len(opener.requests) == 1
    form = parse_qs(opener.requests[0].data.decode("utf-8"))
    assert form["openedBuild"] == ["trunk"]
    assert form["browser"] == [TYPE_CODE]


def test_html_alert_is_an_error():
    """Zentao form validation errors are HTML alerts, not JSON failures."""
    client = zentao.ZentaoClient(
        {
            "ZENTAO_URL": "http://zentao.example",
            "ZENTAO_ACCOUNT": "tester",
            "ZENTAO_PASSWORD": "secret",
        }
    )

    with pytest.raises(RuntimeError, match="表单校验"):
        client._ensure_response_ok(
            "set-browser-type",
            "5495",
            "<script>alert ('影响版本不能为空')</script>",
        )


def test_classification_rejects_missing_status(monkeypatch):
    """An unreadable state must stop before any write."""
    payload = bug_payload()
    payload["bug"]["status"] = ""
    opener = RecordingOpener()
    client = make_client(monkeypatch, [payload], opener)

    with pytest.raises(RuntimeError, match="状态"):
        client.update_bug_browser_type("5495", TYPE_NAME)

    assert opener.requests == []


def test_classification_rejects_missing_opened_build(monkeypatch):
    """Missing required edit fields must stop before submitting the form."""
    opener = RecordingOpener()
    client = make_client(
        monkeypatch,
        [bug_payload(status="active", opened_build="")],
        opener,
    )

    with pytest.raises(RuntimeError, match="openedBuild"):
        client.update_bug_browser_type("5495", TYPE_NAME)

    assert opener.requests == []


def test_classification_rejects_post_edit_type_mismatch(monkeypatch):
    """A success-looking response is insufficient when the field did not persist."""
    client = make_client(
        monkeypatch,
        [
            bug_payload(status="active", browser="firefox"),
            bug_payload(status="active", browser="firefox"),
        ],
    )

    with pytest.raises(RuntimeError, match="分类回读不一致"):
        client.update_bug_browser_type("5495", TYPE_NAME)


def test_classification_rejects_post_edit_status_mutation(monkeypatch):
    """Classification editing may not silently change the Bug lifecycle."""
    client = make_client(
        monkeypatch,
        [
            bug_payload(status="active", browser="firefox"),
            bug_payload(status="resolved", browser=TYPE_CODE),
        ],
    )

    with pytest.raises(RuntimeError, match="状态被意外改为"):
        client.update_bug_browser_type("5495", TYPE_NAME)


def test_resolve_sets_type_before_resolve(monkeypatch):
    """The fallback API must classify before it resolves."""
    events = []
    opener = RecordingOpener(events=events)
    client = zentao.ZentaoClient(
        {
            "ZENTAO_URL": "http://zentao.example",
            "ZENTAO_ACCOUNT": "tester",
            "ZENTAO_PASSWORD": "secret",
            "PROJECT_OWNER": "owner",
        }
    )
    client.opener = opener
    monkeypatch.setattr(client, "login", lambda: None)
    monkeypatch.setattr(
        client,
        "update_bug_browser_type",
        lambda _bug_id, _bug_type: events.append("classify"),
    )
    statuses = iter(["active", "resolved"])
    monkeypatch.setattr(client, "get_bug_status", lambda _bug_id: next(statuses))

    changed = client.resolve_bug("5495", bug_type=TYPE_NAME)

    assert changed is True
    assert events == ["classify", "resolve"]


class StatefulWritebackClient:
    """In-memory tracker used to exercise complete writeback safely."""

    def __init__(self, final_override=None):
        self.state = {
            "status": "active",
            "confirmed": "0",
            "browser": "firefox",
        }
        self.final_override = final_override or {}
        self.writes = []

    @property
    def write_count(self):
        return len(self.writes)

    def login(self):
        return None

    def fetch_bug_json(self, _bug_id):
        return {"bug": dict(self.state)}

    def confirm_bug(self, _bug_id, _comment):
        if self.state["status"] == "active" and self.state["confirmed"] == "0":
            self.state["confirmed"] = "1"
            self.writes.append("confirm")
            return True
        return False

    def update_bug_browser_type(self, _bug_id, _bug_type):
        if self.state["browser"] == TYPE_CODE:
            return False
        if self.state["status"] in ("resolved", "closed"):
            raise RuntimeError("terminal classification conflict")
        self.state["browser"] = TYPE_CODE
        self.writes.append("classify")
        return True

    def resolve_bug(
        self,
        _bug_id,
        _resolution,
        _comment,
        _assigned_to,
        _bug_type,
    ):
        if self.state["status"] in ("resolved", "closed"):
            return False
        self.state["status"] = "resolved"
        self.writes.append("resolve")
        return True

    def get_bug_snapshot(self, _bug_id):
        snapshot = dict(self.state)
        snapshot.update(self.final_override)
        return snapshot


def test_repeated_writeback_has_no_second_write():
    """Running the full command twice does not create new tracker events."""
    client = StatefulWritebackClient()

    bugfix_flow.zentao_writeback(
        client, "5495", TYPE_NAME, ISSUE_URL, MR_URL, "owner"
    )
    first_write_count = client.write_count
    bugfix_flow.zentao_writeback(
        client, "5495", TYPE_NAME, ISSUE_URL, MR_URL, "owner"
    )

    assert first_write_count == 3
    assert client.write_count == first_write_count


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("status", "active"),
        ("confirmed", "0"),
        ("browser", "firefox"),
    ],
)
def test_writeback_rejects_failed_postcondition(
    field, invalid_value, capsys
):
    """Every claimed success must be backed by one final tracker snapshot."""
    client = StatefulWritebackClient({field: invalid_value})

    with pytest.raises(RuntimeError, match="最终校验失败"):
        bugfix_flow.zentao_writeback(
            client, "5495", TYPE_NAME, ISSUE_URL, MR_URL, "owner"
        )

    assert "禅道回写完成" not in capsys.readouterr().out


def test_fallback_resolve_wrapper_has_no_bug_type_parameter():
    """The fallback wrapper cannot classify after resolving by construction."""
    parameters = inspect.signature(bugfix_flow.zentao_resolve).parameters

    assert "bug_type" not in parameters
