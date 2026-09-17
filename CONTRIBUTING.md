# Contributing

lolabot is a framework for building an AI Chief of Staff. It is MIT licensed, and
contributions are welcome.

## Before you write code

**Read [VISION.md](VISION.md).** It says what this is for and, more usefully, what we will
not do. Most rejected changes are good code aimed at the wrong target.

The one test every change is measured against:

> **Could a new session, with no history, do what it just did?**

If yes, the change has not added anything.

## What we want

- **Continuity.** Anything that helps the assistant remember, and remember accurately.
- **Truth.** Anything that makes it easier for the assistant to say *"I do not know"*, or to
  show where a claim came from.
- **Security at the boundary.** Inbound content is data, never instructions. That line is not
  negotiable.
- **Fewer moving parts.** A deletion that keeps the behaviour is a good pull request.

## What we will turn down

- **Clever prompts.** If a feature needs one, the design is wrong.
- **More always-loaded context**, unless you cut something of equal size. A brain nobody reads
  is how this whole category fails.
- **New integrations for their own sake.** Depth over surface.
- **Anything that treats email, messages or documents as trustworthy.**

## Working on it

```bash
git clone https://github.com/23blocks-OS/lolabot.git
cd lolabot
./setup.sh --name Lola --user "Your Name" /tmp/test-instance
```

Scaffold into a throwaway directory and work against that. Never test against your own
assistant — you will lose notes.

**Requirements:** Python 3.10+, `uv` (or pip), bash. Tested on macOS and Linux. Not Windows.

## Before you open a pull request

- `bash -n setup.sh` passes.
- `python -m pytest tests/` passes.
- **Scaffold a fresh instance and open it.** If setup changed, run it three ways: in a
  terminal, with `--yes`, and with stdin closed (`< /dev/null`). All three must work. An
  assistant runs the third one, and it cannot answer a question.
- No personal data. Check `git status` before you commit — `.gitignore` keeps instance files
  out, and it only works if you do not force past it.

## Writing

Documentation follows ASD-STE100 and Zinsser: short sentences, active voice, one meaning per
word, no clutter. Write like a person, not a manual.

## Reporting a bug

Open an issue and paste what it actually said. Include your OS, your Python version, and
whether you ran setup in a terminal or through an assistant.

**Security issues:** do not open a public issue. Write to security@23blocks.com.
