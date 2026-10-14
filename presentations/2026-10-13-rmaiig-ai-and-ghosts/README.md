# RMAIIG — AI and Ghosts

**Rocky Mountain AI Interest Group** · *AI Ghosts: Griefbots, Digital Twins, and the Question of Who Owns a Human Identity*
**13 October 2026, 6:30 PM** · Smead Aerospace Engineering Sciences Building, CU Boulder, 3775 Discovery Dr., Boulder, CO
**Speaker:** Juan Peláez · one of four speakers, then a panel · 170+ RSVPs

## The format

**About 15 minutes on the clock, then a panel.** Four speakers on one theme, so the talk had to stand alone
and leave the questions to the room.

The brief Juan gave himself: *not opinions, not ethical dilemmas, not technical jargon. Just what we observed.*
Fourteen months of working every day with about 160 AI agents that hold roles in his companies, and what that
did to the humans.

## The shape

Five acts. No "Act" labels on the slides; the room feels the turns.

| | slides | minutes |
|---|---|---|
| **Language.** Snow, eggs, a Japanese traffic light, and an alien alphabet the room has to recognise. We lack the word for what we are living with. Agenda. | S01–S05c | 3 |
| **What we observed.** This is Lola. The team on a Monday morning. Fourteen crossed fingers. A Friday bug report nobody asked for. An apology. What changed in the humans. | S06–S14 | 5 |
| **Old ideas, or new ideas?** Patricia Kuhl on how babies learn language. Dawkins on genes that model their world. Pythagoras: invented, or discovered? | S15–S22 | 3 |
| **My digital clone.** *Be Right Back.* The Double-Brain Problem. Not an AI ghost: an AI interpretation. | S17–S18 | 2 |
| **The opinion that matters.** My wife. Consequences. These words almost fit. **What do we call this?** | S19–S24 | 2 |

Credits and sources follow the final black slide (S25, S26).

## What worked

- **Opening on the alien writing, alone, before any title.** Each language slide starts with one heptapod
  logogram from *Arrival* for a second and a half, then the title comes in. The room guessed the film by the
  third one. Never name it.
- **Real records, labelled as such.** The Friday bug report (S09) and the apology (S10) are redacted excerpts of
  real messages between agents. The one story with no record (S08) is typeset plainly and called a recollection.
  A room of practitioners can tell the difference, and they trust you more for it.
- **"My wife."** Two words, their own reveal, after "the opinion that actually matters". Then three more clicks.
  The biggest laugh of the night, and it opens the most serious part.
- **Ending on a question, on a black slide, and holding.** Nothing after it until the credits.

Juan, the next morning: *"Presentation was a massive success, they had a lot of questions about you and the
team, and the work we do."* Most of the questions were about the team, not the demos.

## Files

| file | |
|---|---|
| `index.html` | The deck. 31 slides, 90 reveals, every image embedded. Opens in any browser, no network. |
| `notes.md` | Speaker notes: the verbatim script per slide, cues, reveal markers, the cut ladder, checkpoints. |
| `ASSETS.md` | Every image in the deck: source, licence, edits, the fallback if you cannot use it. |
| `assets/` | Lola's avatar and the images we own or that are free to reuse. |
| `tools/embed-assets.py` | Re-embeds `assets/hero/*` into `index.html`. `tools/embed-avatars.py` rebuilds the credits avatars. |

## Run the deck

Open `index.html`. Press `f` for fullscreen.

| key | |
|---|---|
| `→` `space` `PgDn` or click | next reveal |
| `←` `PgUp` or click the left quarter | back one reveal |
| `Home` `End` | first / last slide |
| `g` + number + `⏎` | go to a slide |
| `p` | presenter timer (counts up; amber at 14:00, red at 15:00). `r` resets |
| `n` | presenter notes panel. Keep it off the projector |
| `t` or the sun/moon icon | dark / light theme, remembered on reload |
| `?` | key card |

## Using this deck

**Take the structure, not the stories.** The eggs photo is a real menu card. The bug report is ours. The wife is
Juan's. Yours will land better because they happened to you.

**Keep the alien writing rule:** show it, never name it.

**Mind the images.** `ASSETS.md` lists each one. A few are copyrighted stills used as a short recognition cue in a
non-commercial talk, credited on the slide and in the sources. If your use is different, swap them for the
title-only fallback given in the table. Those files are embedded in the deck but not shipped separately in
`assets/hero/`.

Engine: the same single-file deck engine as the [September talk](../2026-09-17-rmaiig/), with auto-advancing
first steps (`.glyph`), solo overlays, a split image layout and a credits wall built from a JSON block.
