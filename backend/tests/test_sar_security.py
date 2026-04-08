"""Property-style tests for SAR security helpers."""

from pathlib import Path

from app.services.sar.security import (
    sanitize_text_input,
    sanitize_filename,
    validate_path_traversal,
    sanitize_sar_data_for_pdf,
    log_sar_access,
)


def test_property_input_sanitization_removes_control_sequences():
    raw = "hello\x00world\x07\\evil\f\v"
    out = sanitize_text_input(raw)
    assert "\x00" not in out
    assert "\x07" not in out
    assert "\f" not in out
    assert "\v" not in out
    # Backslash should be escaped.
    assert "\\\\" in out


def test_property_path_traversal_prevention(tmp_path):
    allowed = tmp_path / "sar"
    allowed.mkdir(parents=True)
    safe = str(allowed / "sar_1.pdf")
    bad = str(allowed / ".." / "secret.txt")
    assert validate_path_traversal(safe, allowed) is True
    assert validate_path_traversal(bad, allowed) is False


def test_property_sanitize_filename_blocks_traversal_tokens():
    name = "../../etc/passwd\\x\0.pdf"
    out = sanitize_filename(name)
    assert ".." not in out
    assert "/" not in out
    assert "\\" not in out
    assert "\x00" not in out


def test_property_audit_payload_sanitization_is_recursive():
    payload = {
        "narrative": "bad\x00input",
        "nested": {"field": "line\\break"},
        "arr": ["ok", "x\x07y"],
    }
    out = sanitize_sar_data_for_pdf(payload)
    assert "\x00" not in out["narrative"]
    assert "\\\\" in out["nested"]["field"]
    assert "\x07" not in out["arr"][1]


def test_property_audit_trail_logs_generate_events(monkeypatch):
    events: list[str] = []

    class _L:
        def info(self, msg):
            events.append(str(msg))

        def warning(self, msg):
            events.append(str(msg))

    monkeypatch.setattr("app.services.sar.security.logger", _L())
    log_sar_access("generate", sar_id="sar-1", report_id="rep-1", user_id="u-1", success=True)
    log_sar_access("download", sar_id="sar-1", success=False, error_message="denied")

    assert any("action=generate" in e for e in events)
    assert any("action=download" in e and "success=False" in e for e in events)
