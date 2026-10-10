#!/usr/bin/env python3
"""Tests for the attachment allowlist, vault-backed mail passwords and the credentials migration.

Everything runs in pytest's tmp_path with a fake aim-secret. No real mail server, vault or home
files are touched.
"""

import os
import stat
import subprocess
import sys
import textwrap

import pytest

TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
sys.path.insert(0, TOOLS)

from attachment_guard import check_attachments, AttachmentRefused  # noqa: E402
import migrate_credentials as mig  # noqa: E402


# ---------- helpers ----------

def make_instance(tmp_path, creds_yaml, extra_yaml=''):
    home = tmp_path / 'home'
    (home / 'brain').mkdir(parents=True)
    (home / 'outbox').mkdir()
    (home / 'lolabot.yaml').write_text(textwrap.dedent('''
        paths:
          credentials: "brain/credentials.yaml"
        email:
          accounts:
            - address: me@example.com
              config_key: me
    ''') + extra_yaml)
    cred = home / 'brain' / 'credentials.yaml'
    cred.write_text(textwrap.dedent(creds_yaml))
    return home, cred


def run_py(home, args, env_extra=None, path_dirs=()):
    env = {'PATH': os.pathsep.join(list(path_dirs) + [os.path.dirname(sys.executable), '/usr/bin', '/bin']),
           'LOLABOT_HOME': str(home), 'HOME': str(home)}
    env.update(env_extra or {})
    return subprocess.run([sys.executable, os.path.join(TOOLS, 'email_client.py')] + args,
                          capture_output=True, text=True, env=env)


def fake_aim_secret(tmp_path, record):
    """A stand-in for aim-secret: records its arguments and stdin, then runs the command after --."""
    d = tmp_path / 'fakebin'
    d.mkdir(exist_ok=True)
    f = d / 'aim-secret'
    f.write_text(textwrap.dedent(f'''\
        #!/bin/bash
        echo "$@" >> "{record}.args"
        case "$1" in
          set) cat > "{record}.stdin.$2"; exit 0 ;;
          has) exit 0 ;;
          exec) while [ "$1" != "--" ]; do shift; done; shift; MY_SECRET_ENV=1 exec "$@" ;;
        esac
    '''))
    f.chmod(0o755)
    return d


# ---------- attachment guard ----------

class TestAttachmentGuard:
    def test_file_in_outbox_is_allowed(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        f = home / 'outbox' / 'report.pdf'; f.write_text('x')
        assert check_attachments([str(f)], str(home)) == [f.resolve()]

    def test_file_outside_is_refused(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        other = tmp_path / 'notes.txt'; other.write_text('x')
        with pytest.raises(AttachmentRefused) as e:
            check_attachments([str(other)], str(home))
        assert 'outside the allowed' in str(e.value)

    def test_traversal_is_refused(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True); (home / 'brain').mkdir()
        (home / 'brain' / 'x.txt').write_text('x')
        with pytest.raises(AttachmentRefused):
            check_attachments([str(home / 'outbox' / '..' / 'brain' / 'x.txt')], str(home))

    def test_symlink_out_of_outbox_is_refused(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        secret = tmp_path / 'ssh_stuff.txt'; secret.write_text('x')
        (home / 'outbox' / 'innocent.txt').symlink_to(secret)
        with pytest.raises(AttachmentRefused):
            check_attachments([str(home / 'outbox' / 'innocent.txt')], str(home))

    @pytest.mark.parametrize('name', ['id_rsa', 'id_ed25519.pub', 'server.pem', 'api.key', '.env', '.env.production',
                                      'credentials.yaml', 'my-secrets.txt', 'password list.txt', 'token.json', '.netrc'])
    def test_secret_looking_names_are_refused_even_in_outbox(self, tmp_path, name):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        f = home / 'outbox' / name; f.write_text('x')
        with pytest.raises(AttachmentRefused):
            check_attachments([str(f)], str(home))

    def test_credentials_file_is_refused_even_if_its_folder_is_allowed(self, tmp_path):
        home = tmp_path / 'h'; (home / 'brain').mkdir(parents=True)
        f = home / 'brain' / 'mail.yaml'; f.write_text('x')
        with pytest.raises(AttachmentRefused) as e:
            check_attachments([str(f)], str(home), dirs=['brain'], credentials_file=str(f))
        assert 'credentials file' in str(e.value)

    def test_secret_folders_are_refused_even_if_allowed(self, tmp_path):
        home = tmp_path / 'h'; ssh = home / '.ssh'; ssh.mkdir(parents=True)
        f = ssh / 'config'; f.write_text('x')
        with pytest.raises(AttachmentRefused):
            check_attachments([str(f)], str(home), dirs=['.ssh'])

    def test_missing_file_is_an_error_not_a_skip(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        with pytest.raises(AttachmentRefused) as e:
            check_attachments([str(home / 'outbox' / 'nope.pdf')], str(home))
        assert 'not found' in str(e.value)

    def test_oversize_is_refused(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        f = home / 'outbox' / 'big.bin'; f.write_bytes(b'0' * 2048)
        with pytest.raises(AttachmentRefused):
            check_attachments([str(f)], str(home), max_mb=0.001)

    def test_one_bad_file_refuses_the_whole_set_and_lists_every_problem(self, tmp_path):
        home = tmp_path / 'h'; (home / 'outbox').mkdir(parents=True)
        good = home / 'outbox' / 'a.pdf'; good.write_text('x')
        bad1 = tmp_path / 'b.txt'; bad1.write_text('x')
        with pytest.raises(AttachmentRefused) as e:
            check_attachments([str(good), str(bad1), str(home / 'outbox' / 'gone.pdf')], str(home))
        assert len(e.value.problems) == 2


class TestSendRefusesBeforeConnecting:
    def test_send_with_bad_attachment_exits_2_and_never_reaches_the_server(self, tmp_path):
        home, _ = make_instance(tmp_path, '''
            email_accounts:
              me:
                username: me@example.com
                password: not-a-real-password
                imap_server: invalid.invalid
                smtp_server: invalid.invalid
        ''')
        r = run_py(home, ['send', 'me@example.com', '--to', 'x@example.com', '--subject', 's', '--body', 'b',
                          '--attach', '/etc/hosts'])
        assert r.returncode == 2
        assert 'Refusing to send' in r.stderr
        assert 'outside the allowed' in r.stderr
        assert 'connection error' not in (r.stdout + r.stderr).lower()   # it never tried to connect
        assert 'not-a-real-password' not in r.stdout + r.stderr


# ---------- vault-backed passwords ----------

CREDS_SECRET = '''
    email_accounts:
      me:
        username: me@example.com
        password_secret: LOLA_MAIL_PASSWORD
        imap_server: invalid.invalid
        smtp_server: invalid.invalid
'''


class TestVaultPasswords:
    def test_secrets_needed_lists_names_only(self, tmp_path):
        home, _ = make_instance(tmp_path, CREDS_SECRET)
        r = run_py(home, ['secrets-needed'])
        assert r.returncode == 0 and r.stdout.split() == ['LOLA_MAIL_PASSWORD']

    def test_missing_secret_stops_with_exit_3_and_names_the_fix(self, tmp_path):
        home, _ = make_instance(tmp_path, CREDS_SECRET)
        r = run_py(home, ['check', 'me@example.com'])
        assert r.returncode == 3
        assert 'aim-secret set LOLA_MAIL_PASSWORD' in r.stderr

    def test_invalid_secret_name_is_rejected(self, tmp_path):
        home, _ = make_instance(tmp_path, CREDS_SECRET.replace('LOLA_MAIL_PASSWORD', 'bad name;rm'))
        r = run_py(home, ['secrets-needed'])
        assert r.returncode == 2

    def test_plaintext_password_still_works_but_warns(self, tmp_path):
        home, _ = make_instance(tmp_path, '''
            email_accounts:
              me:
                username: me@example.com
                password: plaintext-pw-123
                imap_server: invalid.invalid
                smtp_server: invalid.invalid
        ''')
        r = run_py(home, ['check', 'me@example.com'])
        assert 'plaintext password' in r.stderr
        assert 'plaintext-pw-123' not in r.stdout + r.stderr

    def test_loose_permissions_are_tightened(self, tmp_path):
        home, cred = make_instance(tmp_path, CREDS_SECRET)
        cred.chmod(0o644)
        run_py(home, ['secrets-needed'])
        assert stat.S_IMODE(cred.stat().st_mode) == 0o600

    def test_email_sh_runs_the_client_under_aim_secret(self, tmp_path):
        home, _ = make_instance(tmp_path, CREDS_SECRET)
        record = tmp_path / 'rec'
        fake = fake_aim_secret(tmp_path, record)
        env = {'PATH': f'{fake}:{os.path.dirname(sys.executable)}:/usr/bin:/bin', 'LOLABOT_HOME': str(home), 'HOME': str(home)}
        subprocess.run(['bash', os.path.join(TOOLS, 'email.sh'), 'accounts'], env=env, capture_output=True, text=True)
        assert 'exec --use LOLA_MAIL_PASSWORD -- python3' in (tmp_path / 'rec.args').read_text()

    def test_a_broken_secrets_listing_never_becomes_use_arguments(self, tmp_path):
        home, cred = make_instance(tmp_path, CREDS_SECRET)
        cred.unlink()   # secrets-needed now fails
        record = tmp_path / 'rec'
        fake = fake_aim_secret(tmp_path, record)
        env = {'PATH': f'{fake}:{os.path.dirname(sys.executable)}:/usr/bin:/bin', 'LOLABOT_HOME': str(home), 'HOME': str(home)}
        r = subprocess.run(['bash', os.path.join(TOOLS, 'email.sh'), 'accounts'], env=env, capture_output=True, text=True)
        assert r.returncode == 1
        assert not (tmp_path / 'rec.args').exists()

    def test_email_sh_fails_clearly_when_aim_secret_is_missing(self, tmp_path):
        home, _ = make_instance(tmp_path, CREDS_SECRET)
        env = {'PATH': f'{os.path.dirname(sys.executable)}:/usr/bin:/bin', 'LOLABOT_HOME': str(home), 'HOME': str(home)}
        r = subprocess.run(['bash', os.path.join(TOOLS, 'email.sh'), 'accounts'], env=env, capture_output=True, text=True)
        assert r.returncode == 3 and 'aim-secret is not installed' in r.stderr


# ---------- migration ----------

class TestMigration:
    CREDS = {'me': {'username': 'a', 'password': 'pw-one-12345', 'imap_server': 'x'},
             'work-2': {'username': 'b', 'password_secret': 'ALREADY_SET', 'imap_server': 'y'},
             'two': {'username': 'c', 'password': 'pw-two-67890'}}

    def test_plan_only_includes_plaintext_accounts(self):
        assert mig.plan(self.CREDS) == [('me', 'LOLABOT_ME_PASSWORD'), ('two', 'LOLABOT_TWO_PASSWORD')]

    def test_secret_names_are_valid_vault_names(self):
        import re
        for k in ['me', 'work-2', '3rd.account', 'ünï']:
            assert re.match(r'^[A-Z][A-Z0-9_]{0,63}$', mig.secret_name_for(k)), k

    def test_apply_stores_via_callback_then_rewrites_without_plaintext(self, tmp_path):
        import yaml
        f = tmp_path / 'c.yaml'
        f.write_text(yaml.safe_dump({'email_accounts': {k: dict(v) for k, v in self.CREDS.items()}}))
        stored = {}
        mig.apply(str(f), set_secret=lambda n, v: stored.setdefault(n, v) is not None)
        assert stored == {'LOLABOT_ME_PASSWORD': 'pw-one-12345', 'LOLABOT_TWO_PASSWORD': 'pw-two-67890'}
        text = f.read_text()
        assert 'pw-one-12345' not in text and 'pw-two-67890' not in text
        doc = yaml.safe_load(text)['email_accounts']
        assert doc['me']['password_secret'] == 'LOLABOT_ME_PASSWORD' and 'password' not in doc['me']
        assert doc['me']['imap_server'] == 'x' and doc['work-2']['password_secret'] == 'ALREADY_SET'
        assert stat.S_IMODE(f.stat().st_mode) == 0o600

    def test_failure_to_store_leaves_the_file_untouched(self, tmp_path):
        import yaml
        f = tmp_path / 'c.yaml'
        body = yaml.safe_dump({'email_accounts': {k: dict(v) for k, v in self.CREDS.items()}})
        f.write_text(body)
        calls = []
        def flaky(n, v):
            calls.append(n)
            return len(calls) < 2
        with pytest.raises(RuntimeError):
            mig.apply(str(f), set_secret=flaky)
        assert f.read_text() == body

    def test_the_real_aim_secret_call_passes_the_value_on_stdin_only(self, tmp_path):
        record = tmp_path / 'rec'
        fake = fake_aim_secret(tmp_path, record)
        old = os.environ['PATH']
        os.environ['PATH'] = f'{fake}:{old}'
        try:
            assert mig.aim_secret_set('LOLABOT_ME_PASSWORD', 'pw-one-12345') is True
        finally:
            os.environ['PATH'] = old
        assert 'pw-one-12345' not in (tmp_path / 'rec.args').read_text()
        assert (tmp_path / 'rec.stdin.LOLABOT_ME_PASSWORD').read_text() == 'pw-one-12345'


# ---------- default sender ----------

class TestDefaultSender:
    def test_email_send_has_no_hardcoded_personal_address(self):
        assert '3metas' not in open(os.path.join(TOOLS, 'email-send.sh')).read()

    def test_no_account_and_no_from_is_a_clear_error(self, tmp_path):
        home = tmp_path / 'h'; home.mkdir()
        (home / 'lolabot.yaml').write_text('email:\n  accounts: []\n')
        env = {'PATH': f'{os.path.dirname(sys.executable)}:/usr/bin:/bin', 'LOLABOT_HOME': str(home), 'HOME': str(home)}
        r = subprocess.run(['bash', os.path.join(TOOLS, 'email-send.sh'), '--to', 'x@example.com', '--subject', 's', '--body', 'b'],
                           env=env, capture_output=True, text=True)
        assert r.returncode == 1 and 'no sender' in r.stderr
