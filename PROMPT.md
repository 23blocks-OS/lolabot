# Get your own Lola

**Copy the block below. Paste it into [Claude Code](https://docs.anthropic.com/en/docs/claude-code).
That is the whole setup.**

It takes about five minutes and costs nothing. MIT licensed.

---

```
Set me up with lolabot, a personal-assistant framework.

1. Create a folder at ~/assistant
2. Clone https://github.com/23blocks-OS/lolabot.git into ~/lolabot
3. Run ~/lolabot/setup.sh ~/assistant using sensible defaults — ask me only
   for my name and what I want to call you
4. Copy lolabot.yaml.example to lolabot.yaml in ~/assistant
5. Tell me the one command to run next, then stop

Don't set up email or anything needing passwords. I'll do that later.
```

---

## What happens next

It gives you **one command**. Run it, and your assistant introduces itself and asks four questions:

**What to call you.**
**What its job is.**
**What it should handle every week.**
**How you will know, in six weeks, whether it was worth having.**

**That last question is the one to pay attention to.** It writes your answer down word for word and
puts the review on its own task list. Most software never asks how it should be judged.

**You can skip all four and just give it work instead.**

## Two honest notes

**It needs Claude Code specifically** — the desktop app or the CLI. Not the Claude or ChatGPT web
app, because it has to be able to write files.

**Tested on macOS and Linux.** Not Windows.

## Then what

Give it something real. An inbox, a customer, a decision you keep re-explaining. **The whole point is
that tomorrow it still knows.**

- Full setup and options: [INSTALL.md](INSTALL.md)
- What this is and why: [VISION.md](VISION.md)
- The talk that sent you here: [presentations/](presentations/)

## If it breaks

Open an issue and paste what it said. **Fixing that is a reasonable first task for an assistant.**
