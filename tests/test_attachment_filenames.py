#!/usr/bin/env python3
"""Attachment names come from outside: they must never leave the email's folder."""

import os
import sys
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

import email_client  # noqa: E402


def _msg(filename: str) -> EmailMessage:
    m = EmailMessage()
    m.set_content("hi")
    m.add_attachment(b"data", maintype="application", subtype="octet-stream", filename=filename)
    return m


def test_dot_dot_name_is_saved_inside_the_email_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(email_client, "EMAILS_DIR", str(tmp_path))
    out = email_client.extract_attachments(_msg(".."), "1", "a@example.com")
    assert out and out[0]["filename"] == "attachment"
    saved = tmp_path / "a@example.com" / out[0]["path"]
    assert saved.is_file()
    assert (tmp_path / "a@example.com" / "attachments" / "1") in saved.parents


def test_slashes_are_neutralised(tmp_path, monkeypatch):
    monkeypatch.setattr(email_client, "EMAILS_DIR", str(tmp_path))
    out = email_client.extract_attachments(_msg("../../x.txt"), "2", "a@example.com")
    assert out and "/" not in out[0]["filename"]
    for p in Path(tmp_path).rglob("x.txt"):
        assert "attachments" in p.parts
