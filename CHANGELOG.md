# Changelog

All notable changes to lolabot. Each release is also published on
[GitHub Releases](https://github.com/23blocks-OS/lolabot/releases) with the same notes.
Versions follow [Semantic Versioning](https://semver.org/).

## [1.2.0] — 2026-10-14

### Added
- **Delivery record for every send.** `send`, `reply` and `forward` append one JSON line to
  `emails/<account>/sent-log.jsonl`: time, account, to, cc, subject, Message-ID (now set by the
  client), SHA-256 and size of the exact bytes handed to the SMTP server, each attachment's name,
  size and SHA-256, accepted and refused recipients. The client then opens the Sent folder over
  IMAP and looks for the Message-ID; a server that files no copy of its own (Gmail does) gets the
  bytes appended to Sent, and the record says `how: appended`. A rejected send is recorded as
  `failed` and exits 1. New commands: `email.sh sent-log [--account] [-n]` and
  `email.sh verify <account> <record-id | Message-ID>`. The log is append-only and holds no secrets.
- **The mail-handler skill says what to report after a send:** "sent and verified" only from the
  client's `✓ Verified` line; on `⚠ Not verified` run `verify` once, then say what is true; never
  resend to make sure.
- **Calendar invitations are readable.** A `text/calendar` part (Outlook, Google) is rendered into
  the plain-text body: method, event, when with time zone, where, organizer, attendees, description.
  The raw part is saved as `invite.ics` so the event can be imported. Before, an invitation with no
  `text/plain` sibling read as an empty message.

### Fixed
- The sent-mail cache (`emails/<account>/sent/`) records the attachments sent again; v1.1.0 had
  dropped them.

### Documentation
- `docs/email-security-system.md`: calendar parts and the delivery record. `CLAUDE.TEMPLATE.md` and
  `README.md` carry the new commands. `presentations/`: *AI and Ghosts* (RMAIIG, CU Boulder,
  2026-10-13).

154 tests pass (14 new).

## [1.1.1] — 2026-10-10

Follow-up to 1.1.0, found by rolling it onto a real, hand-configured instance.

### Fixed
- The plaintext-password warning no longer prints on every run (it would fill cron logs). It
  appears once, in `email.sh accounts`.
- The attachment refusal message points at the right place to add a folder. Instances without a
  `lolabot.yaml` can keep the list in `tools/email_client.py`.
- `tools/migrate_credentials.py --file PATH` works without `config.py`, so older instances can
  move their mail password into the vault.

141 tests pass.

## [1.1.0] — 2026-10-10

Security release. Fixes two High findings in the email tools.

### Fixed
- **Attachments could exfiltrate any readable file.** Attachments are limited to
  `email.attachment_dirs` (default `outbox/`); secret-looking names, secret folders, symlinks out
  of the allowed folders and the credentials file are refused before the client connects. A missing
  file is an error, and one bad file refuses the whole send.
- **Mailbox passwords sat in plaintext where the agent could read them.** `password_secret: NAME`
  with the vault (`aim-secret` from AI Maestro); `tools/email.sh` injects the value and scrubs it
  from the output. `python3 tools/migrate_credentials.py --apply` moves existing passwords.
  Plaintext still works but warns; the credentials file is set to owner-only (600).
- A missing secret fails before any network connection.
- `email-send.sh` no longer defaults to a hardcoded personal sender; it uses the first account in
  `lolabot.yaml` or `--from`.
- One credentials default path: `brain/credentials.yaml` (the old name is still found).

### Upgrading an existing instance
`setup.sh` copies tools with `cp -n`, so an existing instance keeps its old tools. Copy
`tools/attachment_guard.py`, `tools/migrate_credentials.py`, `tools/email.sh`,
`tools/email-send.sh`, `tools/email_client.py` and `tools/config.py` into the instance, create
`outbox/`, add `attachment_dirs: ["outbox"]` under `email:` in `lolabot.yaml`, then run the
migration.

140 tests pass (56 new).

## [1.0.2] — 2026-10-09

### Fixed
- **The memory integrity check reported "all OK" on macOS.** `sha256sum -c` with no file argument
  prints a usage error there and verifies nothing; the script turned the empty result into OK. The
  list is now read with `sha256sum -c -`. If the tool does not account for every recorded file, the
  check logs `INTEGRITY CHECK COULD NOT RUN`, prints an error and exits 3.
- The timestamp no longer depends on GNU `date -Iseconds`.
- The tamper test runs on every platform; 104 tests pass, none skipped.

If you ran 1.0.0 or 1.0.1 on a Mac, treat any past "OK" from this check as unverified.

## [1.0.1] — 2026-10-09

### Fixed
- The integrity alert log rotates at 5 MB and keeps one previous file (`LOLABOT_ALERT_LOG` to
  move it). The cron example no longer uses an unbounded `>>`.
- Converted HEIC JPGs older than 7 days are removed from the default output directory only
  (`LOLABOT_HEIC_OUTPUT` to move it).
- Opt-in `LOLABOT_EMAIL_RETENTION_DAYS` prunes cached inbox/sent JSON on `check` and `sync`. Off by
  default; quarantine and attachments are never touched.

13 new tests; 101 pass.

## [1.0.0] — 2026-10-01

First release. The four skills (file-processing, mail-handler, pa-memory-delegation,
pa-onboarding) rewritten to Anthropic's skill best practices.

- Trigger suite: 7 cases, Sonnet, 3 runs each. Score 0.71 → 1.00; 7/7 cases pass every run; no
  skill fires on unrelated requests.
- Skill names follow the spec, so Claude Code loads them; each description says when to use it.
- Bodies about 40% smaller (6,293 → 3,520 tokens). Safety rules for email kept and stated plainly.
- Examples use a fictional household.
- `email-check.sh` no longer defaults to a personal address: pass the account or set
  `LOLA_EMAIL_ACCOUNT`.
- The skill's drifted copy of `memory_indexer.py` is removed; the skill uses
  `tools/memory_indexer.py`.

[1.2.0]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.2.0
[1.1.1]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.1.1
[1.1.0]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.1.0
[1.0.2]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.0.2
[1.0.1]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.0.1
[1.0.0]: https://github.com/23blocks-OS/lolabot/releases/tag/v1.0.0
