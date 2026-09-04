# Outreach copy

Final versions. **The prompt is the product** — everything before it exists to get someone to paste it.

**Audience check before you send:** this needs **Claude Code**, which runs in a terminal. Someone with
only the Claude or ChatGPT web app cannot run it. The copy below says so plainly rather than
generating confused replies.

---

## Email

**Subject:** The thing I've been using instead of a to-do list

Hi <name>,

You already pay for Claude. It can do more than answer questions — it can hold a job.

I've had one working as my chief of staff for a few months now. It keeps my task list, remembers what
I told it in March, drafts the emails I keep putting off, and tells me what I've forgotten. Not a
chatbot I visit. Something that turns up already knowing where we left off.

It isn't a product and I'm not selling it. It's a free, open-source setup, and you can have your own
running in about five minutes.

**If you use Claude Code**, open it and paste this:

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

It gives you one command. Run it, and your assistant introduces itself and asks four questions: what
to call you, what its job is, what it should handle every week, and how you'll know in six weeks
whether it was worth having.

You can skip all four. Ask it to do something real instead and it just gets on with it.

**If you don't use Claude Code yet**, that's the only thing standing in the way — it's Anthropic's
command-line version of Claude, and it's the same subscription you already have.

Everything runs on your own machine. Nothing of yours goes anywhere.

Repo, if you'd rather read before running anything:
https://github.com/23blocks-OS/lolabot

If you get stuck, reply and I'll help.

<signature>

---

## LinkedIn

**First line matters — LinkedIn cuts the rest until someone taps "more".**

> Most people use Claude like a search box. Mine has a job.
>
> It keeps my task list, remembers what I told it months ago, drafts what I keep postponing, and
> tells me what I've forgotten. It shows up already knowing where we left off.
>
> I've open-sourced the setup. It's free, it runs on your own machine, and nothing you give it leaves
> your computer.
>
> If you have Claude Code, paste this into it:
>
> *"Set me up with lolabot. Clone https://github.com/23blocks-OS/lolabot.git into ~/lolabot, run
> setup.sh against ~/assistant with sensible defaults, then tell me the one command to run next."*
>
> It hands you one command. Run it, and your assistant introduces itself and asks four questions —
> what to call you, what its job is, what it should handle weekly, and how you'll judge it in six
> weeks.
>
> That last question is the one I care about. Software almost never asks how it should be measured.
>
> You can skip all four and just put it to work.
>
> https://github.com/23blocks-OS/lolabot
>
> Built it for myself. If you make one, tell me what you gave it to do.

---

## Rules for whoever sends these

**Do not promise email.** The framework ships an email client that does nothing until the user adds
their own credentials. *"It drafts my emails"* is true of the sender's instance, not of a fresh
install. Keep those claims in the first person — that is why both drafts say "mine" and "I".

**Do not say it works with the Claude or ChatGPT web apps.** It needs Claude Code. Say so early;
someone discovering it at step three is a reply you have to answer.

**Do not claim Windows.** setup.sh is tested on macOS and Linux.

**Lead with the four questions, not the feature list.** Everyone has seen a feature list. Almost
nobody has been asked by software how it should be judged.

**If someone asks what the catch is:** it needs a Claude subscription, it runs on their machine, and
nobody is hosting it for them. That is the whole trade.
