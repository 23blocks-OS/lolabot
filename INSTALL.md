# Install

**You need two things: Claude Code, and five minutes.**

There is no installer to download and no script to pipe into your shell. You already have an AI that
can install software — so you ask it to.

---

## The fast way: paste this into Claude Code

Open Claude Code anywhere and paste this. It does everything.

```
Set me up with lolabot, a personal-assistant framework.

1. Create a folder at ~/assistant and cd into it
2. Clone https://github.com/23blocks-OS/lolabot.git into ~/lolabot
3. Run ~/lolabot/setup.sh ~/assistant and answer its questions using sensible
   defaults — ask me only for my name and what I want to call you
4. Copy lolabot.yaml.example to lolabot.yaml in ~/assistant
5. Tell me the single command I need to run next, and stop

Do not configure email or anything requiring passwords. I will do that later.
```

When it finishes, it will tell you to run one command. Run it. **That's the install.**

> **Why a prompt and not `curl … | bash`?** Because you should not pipe a script from the internet
> into your shell, and we are not going to be the ones who taught you to. Everything above is
> readable before it runs, and your AI will tell you what it is doing.

---

## The manual way

If you would rather do it yourself:

```bash
# 1. Get the framework
git clone https://github.com/23blocks-OS/lolabot.git ~/lolabot

# 2. Create your assistant's home and scaffold it
~/lolabot/setup.sh ~/assistant

# 3. Configure
cd ~/assistant
cp lolabot.yaml.example lolabot.yaml

# 4. Start your assistant
claude
```

**The last line is the whole point.** `~/assistant` is your assistant's home: its instructions, its
memory, its notes. Running `claude` there is how you talk to it. Running `claude` anywhere else gets
you plain Claude Code.

---

## What happens the first time

Your assistant introduces itself and asks four questions:

1. What should it call you, and what should you call it
2. What its job is, in one line
3. Two or three things it should handle every week without being asked
4. How you will know, in six weeks, whether it was worth it

It writes the answers to `brain/charter.md` and into its own instructions. **Every question can be
skipped** — say "skip" and it gets on with whatever you actually wanted.

If you open with real work instead — *"check my email"* — it does that first and asks later.

---

## Make it one click

So you are not typing paths every morning.

**macOS or Linux — a launcher command:**

```bash
~/lolabot/scripts/make-launcher.sh ~/assistant
```

That creates an `assistant` command. Type `assistant` in any terminal and you are talking to it.

**macOS — a Dock icon:**

The same script offers to create `~/Applications/Assistant.app`. Drag it to your Dock. Clicking it
opens a terminal already talking to your assistant.

**Linux — a desktop entry:**

The script offers to write `~/.local/share/applications/assistant.desktop`, which puts it in your
application menu.

---

## Requirements

| | |
|---|---|
| **Claude Code** | [Install instructions](https://docs.anthropic.com/en/docs/claude-code) — needs a Claude subscription or API key |
| **git** | Almost certainly already installed. `git --version` to check |
| **Python 3.10+** | Only needed for memory search, file indexing and email. Everything else works without it |

**You do not need Python to start.** The assistant will tell you when something needs it, and how to
get it.

---

## Optional: more than one assistant

If one assistant is not enough — you want a researcher, a bookkeeper, someone watching a particular
inbox — lolabot works with [AI Maestro](https://github.com/23blocks-OS/ai-maestro), which lets your
assistant create other agents and message them.

**Ignore this until you need it.** One assistant that works beats five that do not.

---

## If something goes wrong

**`claude: command not found`** — Claude Code is not installed or not on your PATH.
See [the Claude Code docs](https://docs.anthropic.com/en/docs/claude-code).

**The assistant does not seem to know who it is** — you are probably running `claude` in the wrong
folder. It must be your assistant's home, `~/assistant`, not the `~/lolabot` framework folder.

**Anything else** — tell your assistant. It has the repo, it can read its own setup, and diagnosing
its own installation is a reasonable first task.
