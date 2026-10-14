#!/usr/bin/env python3
"""
Tests for the delivery record in email_client.py

Every send appends a line to emails/<account>/sent-log.jsonl with the SHA-256 of
the bytes handed to the SMTP server, what the server accepted, and whether the
copy was found in the Sent folder. `verify` appends a later line that refers to
the first. These tests cover the pure parts; the IMAP round trip is exercised by
sending a real message.
"""

import os
import sys
import json
import hashlib
import importlib

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LOLABOT_HOME", str(tmp_path))
    (tmp_path / "lolabot.yaml").write_text(
        "email:\n  accounts:\n    - address: a@example.com\n      config_key: a\n")
    import config
    config._config_cache = None
    import email_client
    importlib.reload(email_client)
    yield email_client
    config._config_cache = None


RAW = (b"From: a@example.com\r\nTo: b@example.com\r\nSubject: Hello\r\n"
       b"Message-ID: <abc@example.com>\r\nIn-Reply-To: <xyz@example.com>\r\n\r\nBody\r\n")


def test_record_hashes_exact_bytes(client, tmp_path):
    f = tmp_path / "report.pdf"
    f.write_bytes(b"%PDF-1.4 test")
    rec = client.build_delivery_record(RAW, "a@example.com", ["b@example.com"], [], "Hello", [str(f)],
                                       {"server": "smtp.example.com", "port": 465, "accepted": ["b@example.com"], "refused": {}})
    assert rec["event"] == "sent"
    assert rec["sha256"] == hashlib.sha256(RAW).hexdigest()
    assert rec["id"] == rec["sha256"][:12]
    assert rec["size"] == len(RAW)
    assert rec["message_id"] == "<abc@example.com>"
    assert rec["in_reply_to"] == "<xyz@example.com>"
    assert rec["attachments"] == [{"filename": "report.pdf", "size": 13,
                                   "sha256": hashlib.sha256(b"%PDF-1.4 test").hexdigest()}]
    assert rec["sent_folder"]["verified"] is False


def test_parse_list_line_variants(client):
    attrs, name = client.parse_list_line(b'(\\HasNoChildren \\Sent) "/" "[Gmail]/Sent Mail"')
    assert "\\sent" in attrs and name == "[Gmail]/Sent Mail"
    attrs, name = client.parse_list_line(b'(\\HasNoChildren) "." INBOX.Sent')
    assert attrs == ["\\hasnochildren"] and name == "INBOX.Sent"
    attrs, name = client.parse_list_line(b'(\\Noselect \\HasChildren) NIL "[Gmail]"')
    assert name == "[Gmail]"
    assert client.parse_list_line(b"garbage") == ([], "")


class FakeMail:
    def __init__(self, lines):
        self.lines = lines

    def list(self):
        return 'OK', self.lines


def test_find_sent_folder_prefers_special_use(client):
    mail = FakeMail([b'(\\HasNoChildren) "/" "Sent"', b'(\\HasNoChildren \\Sent) "/" "Outbox-ish"'])
    assert client.find_sent_folder(mail) == "Outbox-ish"


def test_find_sent_folder_falls_back_to_names(client):
    mail = FakeMail([b'(\\HasNoChildren) "/" "INBOX"', b'(\\HasNoChildren) "/" "Sent Items"'])
    assert client.find_sent_folder(mail) == "Sent Items"
    assert client.find_sent_folder(FakeMail([b'(\\HasNoChildren) "/" "INBOX"'])) is None


def test_log_append_and_fold_verification(client, tmp_path):
    rec = client.build_delivery_record(RAW, "a@example.com", ["b@example.com"], [], "Hello", [],
                                       {"server": "s", "port": 465, "accepted": ["b@example.com"], "refused": {}})
    path = client.append_sent_log("a@example.com", rec)
    assert path == tmp_path / "emails" / "a@example.com" / "sent-log.jsonl"
    client.append_sent_log("a@example.com", {"event": "verified", "ref": rec["id"],
                                             "sent_folder": {"verified": True, "folder": "Sent", "uid": "7", "how": "server"}})
    rows = client.read_sent_log("a@example.com")
    assert len(rows) == 1
    assert rows[0]["sent_folder"]["verified"] is True
    assert rows[0]["sent_folder"]["uid"] == "7"
    # the file stays append-only: two lines, both valid JSON
    lines = path.read_text().splitlines()
    assert len(lines) == 2 and all(json.loads(l) for l in lines)


def test_format_delivery_states(client):
    rec = client.build_delivery_record(RAW, "a@example.com", ["b@example.com"], [], "Hello", [],
                                       {"server": "s", "port": 465, "accepted": [], "refused": {"b@example.com": ["550", "no"]}})
    out = client.format_delivery(rec)
    assert "⚠ Server refused: b@example.com" in out
    assert "⚠ Not verified" in out and "email.sh verify a@example.com" in out
    rec["sent_folder"] = {"verified": True, "folder": "[Gmail]/Sent Mail", "uid": "42", "how": "server"}
    assert "✓ Verified: copy in Sent folder '[Gmail]/Sent Mail' (uid 42)" in client.format_delivery(rec)
    rec["sent_folder"]["how"] = "appended"
    assert "filed in Sent folder" in client.format_delivery(rec)


def test_verify_without_message_id_reports_why(client):
    out = client.verify_in_sent({}, "", raw=None)
    assert out["verified"] is False
    assert "Message-ID" in out["error"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
