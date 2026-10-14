#!/usr/bin/env python3
"""
Tests for calendar handling in email_client.py

An Outlook or Google invitation arrives as a text/calendar part, often with no
text/plain sibling. Before 2026-10-14 such a message read as an empty body.
"""

import os
import sys
import email

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from email_client import calendar_summary, get_email_body  # noqa: E402

ICS = "\r\n".join([
    "BEGIN:VCALENDAR",
    "PRODID:-//Microsoft Corporation//Outlook 16.0 MIMEDIR//EN",
    "VERSION:2.0",
    "METHOD:REQUEST",
    "BEGIN:VEVENT",
    "ATTENDEE;CN=lola@example.com;RSVP=TRUE:mailto:lola@example.com",
    "ATTENDEE;CN=very.long.name@example.com;RSVP=TRUE:mailto:very.long.na",
    "\tme@example.com",
    "DESCRIPTION:Bring the deck\\, please.\\nSecond line.",
    'DTEND;TZID="Mountain Standard Time":20261016T133000',
    'DTSTART;TZID="Mountain Standard Time":20261016T123000',
    "LOCATION:Avery Brewing",
    "ORGANIZER;CN=host@example.com:mailto:host@example.com",
    "SUMMARY;LANGUAGE=en-us:Team Lunch",
    "END:VEVENT",
    "END:VCALENDAR",
]) + "\r\n"


def test_summary_fields():
    out = calendar_summary(ICS)
    assert out.startswith("[Calendar invitation]")
    assert "Event:     Team Lunch" in out
    assert "Fri 2026-10-16 12:30 Mountain Standard Time" in out
    assert "to  Fri 2026-10-16 13:30" in out
    assert "Where:     Avery Brewing" in out
    assert "Organizer: host@example.com" in out
    # folded continuation line is joined back
    assert "very.long.name@example.com" in out
    # escaped comma and newline are unescaped
    assert "Bring the deck, please.\nSecond line." in out


def test_blank_description_is_dropped():
    ics = ICS.replace("DESCRIPTION:Bring the deck\\, please.\\nSecond line.", "DESCRIPTION: \\n\\n")
    out = calendar_summary(ics)
    assert "Second line" not in out
    assert out.rstrip().endswith("Attendees: lola@example.com, very.long.name@example.com")


def test_reply_method_and_partstat():
    ics = ICS.replace("METHOD:REQUEST", "METHOD:REPLY").replace(
        "ATTENDEE;CN=lola@example.com;RSVP=TRUE", "ATTENDEE;CN=lola@example.com;PARTSTAT=ACCEPTED")
    out = calendar_summary(ics)
    assert out.startswith("[Calendar reply]")
    assert "lola@example.com (accepted)" in out


def test_single_part_calendar_message_has_body():
    raw = (
        "From: host@example.com\r\nTo: lola@example.com\r\nSubject: Team Lunch\r\n"
        "Content-Type: text/calendar; charset=utf-8; method=REQUEST\r\n\r\n" + ICS
    ).encode()
    body_text, body_html = get_email_body(email.message_from_bytes(raw))
    assert "Event:     Team Lunch" in body_text
    assert body_html == ""


def test_calendar_appended_after_plain_text():
    raw = (
        "From: host@example.com\r\nTo: lola@example.com\r\nSubject: Team Lunch\r\n"
        "MIME-Version: 1.0\r\nContent-Type: multipart/alternative; boundary=\"b\"\r\n\r\n"
        "--b\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nSee you Friday.\r\n"
        "--b\r\nContent-Type: text/calendar; charset=utf-8; method=REQUEST\r\n\r\n" + ICS +
        "--b--\r\n"
    ).encode()
    body_text, _ = get_email_body(email.message_from_bytes(raw))
    assert body_text.startswith("See you Friday.")
    assert "[Calendar invitation]" in body_text


def test_plain_message_unchanged():
    raw = b"From: a@example.com\r\nTo: b@example.com\r\nSubject: hi\r\n\r\nJust text.\r\n"
    body_text, body_html = get_email_body(email.message_from_bytes(raw))
    assert body_text == "Just text.\r\n"
    assert body_html == ""


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
