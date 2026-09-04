# Outreach copy

Two messages, both ending in the same paste-able prompt. **The prompt is the product.** Everything
before it exists to get someone to paste it.

---

## Email

**Subject:** A personal assistant you can have running in five minutes

Hi <name>,

You already pay for Claude. It can do more than answer questions — it can hold a job.

I've been running an AI chief of staff for months. It reads my email, keeps my task list, remembers
what I told it in March, and drafts things I'd otherwise put off. It isn't a product I'm selling you.
It's an open-source framework, MIT licensed, and it takes about five minutes to set up.

If you want one, open Claude Code and paste this:

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

It will tell you one command to run. Run it, and your assistant introduces itself and asks four
questions: what to call you, what its job is, what it should handle every week, and how you'll know
in six weeks whether it was worth it.

You can skip every question. It gets on with it either way.

The repo is here if you'd rather read before you run anything:
https://github.com/23blocks-OS/lolabot

Happy to help if you get stuck.

<signature>

---

## LinkedIn

Shorter. People skim.

> **You already pay for Claude. It can hold a job, not just answer questions.**
>
> I've been running an AI chief of staff for months — it handles my email, my task list, and
> remembers things I told it in March. The framework is open source and MIT licensed.
>
> Setup is one paste into Claude Code:
>
> *"Set me up with lolabot. Clone https://github.com/23blocks-OS/lolabot.git into ~/lolabot, run
> setup.sh against ~/assistant with sensible defaults, and tell me the one command to run next."*
>
> Then it asks you four questions — what to call you, what its job is, what it should handle weekly,
> and how you'll judge it in six weeks. You can skip all four.
>
> Repo: https://github.com/23blocks-OS/lolabot
>
> Not selling anything. If you build one, tell me what you made it do.

---

## Notes for whoever sends these

**Do not promise email until they've configured it.** The framework ships an email client; it does
nothing until the user adds credentials. *"It reads my email"* is true of the sender's instance, not
of a fresh install. Keep it in the first person for that reason.

**Do not claim it works on Windows.** The setup script is tested on macOS and Linux.

**The four questions are the differentiator, so lead with them, not with the feature list.** Everyone
has seen a feature list. Almost nobody has been asked by a piece of software how it should be judged.

**If someone replies "what's the catch"** — the honest answer is that it needs a Claude subscription,
it runs on your own machine, and nobody is hosting it for you. That is the trade.
