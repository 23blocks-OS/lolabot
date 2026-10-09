#!/usr/bin/env python3
"""Tests for the bounded log, HEIC cleanup and optional email retention.

Everything runs in pytest's tmp_path. No real data, network or home files are touched.
"""

import os
import subprocess
import sys
import time

import pytest

TOOLS = os.path.join(os.path.dirname(__file__), '..', 'tools')
LIB = os.path.join(TOOLS, 'bounded-log.sh')


def bash(script, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run(['bash', '-c', f'source "{LIB}"; {script}'],
                          capture_output=True, text=True, env=e)


def age(path, days):
    t = time.time() - days * 86400
    os.utime(path, (t, t))


def test_log_rotates_at_cap_and_keeps_one_previous(tmp_path):
    log = tmp_path / 'a.log'
    env = {'LOLABOT_LOG_MAX_BYTES': '100'}
    for i in range(30):
        r = bash(f'echo "line number {i} xxxxxxxxxx" | bounded_log_append "{log}"', env)
        assert r.returncode == 0
    names = sorted(p.name for p in tmp_path.iterdir())
    assert names == ['a.log', 'a.log.1']
    assert log.stat().st_size < 200
    assert 'line number 29' in log.read_text()


def test_log_under_cap_just_appends(tmp_path):
    log = tmp_path / 'a.log'
    bash(f'echo one | bounded_log_append "{log}"; echo two | bounded_log_append "{log}"')
    assert log.read_text() == 'one\ntwo\n'
    assert [p.name for p in tmp_path.iterdir()] == ['a.log']


def test_prune_only_old_matching_regular_files(tmp_path):
    d = tmp_path / 'out'
    d.mkdir()
    old, new, other = d / 'old.jpg', d / 'new.jpg', d / 'old.txt'
    for f in (old, new, other):
        f.write_text('x')
    age(old, 8)
    age(other, 30)
    sub = d / 'sub'
    sub.mkdir()
    (sub / 'deep.jpg').write_text('x')
    age(sub / 'deep.jpg', 30)
    keep = tmp_path / 'outside.jpg'
    keep.write_text('x')
    age(keep, 30)
    r = bash(f'prune_old_files "{d}" 7 "*.jpg"')
    assert r.returncode == 0
    assert not old.exists()
    assert new.exists() and other.exists()
    assert (sub / 'deep.jpg').exists()
    assert keep.exists()


@pytest.mark.parametrize('days', ['', '0', 'abc', '-1', '7; rm'])
def test_prune_rejects_bad_days(tmp_path, days):
    f = tmp_path / 'old.jpg'
    f.write_text('x')
    age(f, 30)
    bash(f'prune_old_files "{tmp_path}" "{days}" "*.jpg"')
    assert f.exists()


def test_prune_ignores_symlinked_dir(tmp_path):
    real = tmp_path / 'real'
    real.mkdir()
    f = real / 'old.jpg'
    f.write_text('x')
    age(f, 30)
    link = tmp_path / 'link'
    link.symlink_to(real)
    bash(f'prune_old_files "{link}" 7 "*.jpg"')
    assert f.exists()


def test_heic_script_prunes_default_dir_only(tmp_path):
    home = tmp_path / 'home'
    (home / 'tools').mkdir(parents=True)
    (home / '.venv/bin').mkdir(parents=True)
    (home / '.venv/bin/activate').write_text('')
    for n in ('heic-convert.sh', 'bounded-log.sh'):
        (home / 'tools' / n).write_text(open(os.path.join(TOOLS, n)).read())
    default = tmp_path / 'default-out'
    default.mkdir()
    custom = tmp_path / 'custom-out'
    custom.mkdir()
    src = tmp_path / 'src'
    src.mkdir()
    for d in (default, custom):
        (d / 'old.jpg').write_text('x')
        age(d / 'old.jpg', 10)
    env = dict(os.environ, LOLABOT_HOME=str(home), LOLABOT_HEIC_OUTPUT=str(default))
    script = str(home / 'tools/heic-convert.sh')
    subprocess.run(['bash', script, str(src)], env=env, capture_output=True)
    assert not (default / 'old.jpg').exists()
    subprocess.run(['bash', script, str(src), str(custom)], env=env, capture_output=True)
    assert (custom / 'old.jpg').exists()


def test_integrity_alert_log_is_bounded(tmp_path):
    home = tmp_path / 'home'
    (home / 'tools').mkdir(parents=True)
    (home / 'indexes').mkdir()
    (home / 'CLAUDE.md').write_text('good')
    for n in ('memory-integrity-check.sh', 'bounded-log.sh'):
        (home / 'tools' / n).write_text(open(os.path.join(TOOLS, n)).read())
    # HOME points at an empty dir so no real ~/.claude files are watched.
    empty = tmp_path / 'fakehome'
    empty.mkdir()
    log = tmp_path / 'alerts.log'
    env = dict(os.environ, LOLABOT_HOME=str(home), HOME=str(empty),
               LOLABOT_ALERT_LOG=str(log), LOLABOT_LOG_MAX_BYTES='300')
    script = str(home / 'tools/memory-integrity-check.sh')
    probe = subprocess.run(['bash', '-c', 'echo x | sha256sum -c'], capture_output=True, text=True)
    if 'usage' in probe.stderr.lower() or 'usage' in probe.stdout.lower():
        pytest.skip('sha256sum without -c (macOS shim); the script targets GNU coreutils')
    subprocess.run(['bash', script, 'init'], env=env, capture_output=True, check=True)
    (home / 'CLAUDE.md').write_text('tampered')
    for _ in range(20):
        r = subprocess.run(['bash', script, 'check'], env=env, capture_output=True, text=True)
        assert r.returncode == 2
    assert sorted(p.name for p in tmp_path.glob('alerts.log*')) == ['alerts.log', 'alerts.log.1']
    assert log.stat().st_size < 600


@pytest.fixture
def mail(tmp_path, monkeypatch):
    sys.path.insert(0, TOOLS)
    import email_client
    monkeypatch.setattr(email_client, 'EMAILS_DIR', str(tmp_path))
    monkeypatch.setattr(email_client, 'ACCOUNT_MAP', {'a@example.com': 'a'})
    base = tmp_path / 'a@example.com'
    files = {}
    for folder in ('inbox', 'sent', 'quarantine'):
        (base / folder).mkdir(parents=True)
        f = base / folder / '1.json'
        f.write_text('{}')
        age(f, 400)
        files[folder] = f
    fresh = base / 'inbox' / '2.json'
    fresh.write_text('{}')
    files['fresh'] = fresh
    return email_client, files


def test_email_retention_off_by_default(mail, monkeypatch):
    ec, files = mail
    for v in (None, '', '0', 'abc', '-5'):
        if v is None:
            monkeypatch.delenv('LOLABOT_EMAIL_RETENTION_DAYS', raising=False)
        else:
            monkeypatch.setenv('LOLABOT_EMAIL_RETENTION_DAYS', v)
        assert ec.prune_email_cache() == 0
    assert all(f.exists() for f in files.values())


def test_email_retention_removes_only_old_inbox_and_sent(mail, monkeypatch):
    ec, files = mail
    monkeypatch.setenv('LOLABOT_EMAIL_RETENTION_DAYS', '90')
    assert ec.prune_email_cache() == 2
    assert not files['inbox'].exists() and not files['sent'].exists()
    assert files['quarantine'].exists()
    assert files['fresh'].exists()
