# Digitakt verification — step-by-step

**For:** Steve
**Time needed:** about 20 minutes for Part A, plus 15 for Part B
**What you need:** your Digitakt (or Digitakt II), a USB cable, and a computer

**This is two separate jobs.** Part A checks four numbers on a screen and needs
no cable. Part B captures a backup file from your machine and sends it to us.
Do Part A first — if you only have time for one, Part A is the one we need
most.

---

## What you are checking, in plain English

We added Digitakt support to the app. We wrote down some facts about your
machine — how many tracks it has, what MIDI channel it uses by default — but
**nobody has checked those facts against a real Digitakt.** That is what you
are doing.

You are not testing whether the app can control your Digitakt. It cannot, on
purpose, and it will not try. See "Is this safe?" below.

**Your job is to read four numbers off a screen and tell us if they match your
machine.** That is genuinely it.

---

## Is this safe? (Read this — it is short)

**Yes. The app cannot send anything to your Digitakt.** This is not a setting
you could accidentally flip; it is built into the code.

- The app never opens a MIDI *output* port to your Digitakt.
- The part of the app that would build messages to send produces an **empty
  list**, always, for Digitakt. There is nothing to send.
- Your patterns, samples, projects and sounds **cannot be changed by this
  test.** Nothing gets written to your machine.

You can leave your Digitakt on with your own project loaded. Nothing will
touch it.

**Part A does not need the cable at all.** Steps 1–3 read numbers out of the
app; Step 4 is just you looking at your machine.

**Part B does use the cable, and it is still safe.** Data flows one way only —
*from* your Digitakt *to* your computer. You press the send button on the
Digitakt itself; the computer only listens. Nothing is written back.

---

# PART A — Check the four numbers

## Step 1 — Open a Terminal

![A Terminal window after Step 2 — the prompt now ends in `RytmRandomizer`](images/00-terminal.png)

**On a Mac:** press `Cmd` + `Space`, type `Terminal`, press `Enter`.

**On Windows:** press the Windows key, type `PowerShell`, press `Enter`.

A window opens with a blinking cursor. It will look plain and a bit
intimidating. You will only type two things into it, and you can copy-paste
both.

---

## Step 2 — Go to the project folder

Copy the line below, paste it into the Terminal window, and press `Enter`.

```
cd ~/RytmRandomizer
```

> **If you get "No such file or directory":** the project is somewhere else on
> your machine. Ask Eddie where it lives and use that path instead. Do not
> guess.

Nothing visible happens. That is correct — it just moved you into the folder.

---

## Step 3 — Run the check

Copy this line, paste it, press `Enter`:

```
.venv/bin/python -m rytm_randomizer.cli live-gui-device-inventory-report
```

> **On Windows,** use this instead:
> ```
> .venv\Scripts\python.exe -m rytm_randomizer.cli live-gui-device-inventory-report
> ```
> Use that full path, not plain `python`. On Windows, typing `python` can hit a
> Microsoft Store placeholder that fails with a confusing disk error.

A page of text scrolls past, one block per device. **Scroll until you find the
block for your machine** — it starts with `Device digitakt_mk1` or
`Device digitakt_ii`. It looks like this:

![The Digitakt entries, with the facts to check highlighted](images/04-device-inventory.png)

The **highlighted lines are the ones you check**. Everything in grey is
background detail you can ignore.

---

## Step 4 — Check the numbers against your machine

This is the actual verification. **Find the line for the machine you own** and
check each thing in the table.

### If you have a Digitakt (the original)

The app says:

```
- digitakt_mk1 / Elektron Digitakt / 8 tracks
```

| # | What the app claims | How to check it on your Digitakt | Match? |
|---|---|---|---|
| 1 | It is called **"Elektron Digitakt"** | Read the name on the front of the machine | ☐ yes ☐ no |
| 2 | It has **8 tracks** | Count the track buttons — the row you press to pick a track | ☐ yes ☐ no |
| 3 | Default **MIDI channel 1** | `SETTINGS` → `MIDI CONFIG` → `CHANNELS` — look at the **Auto Channel** | ☐ yes ☐ no |
| 4 | Manufacturer ID **00 20 3c** | Nothing to check — this is Elektron's company code, same for all their gear | n/a |

### If you have a Digitakt II

The app says:

```
- digitakt_ii / Elektron Digitakt II / 16 tracks
```

| # | What the app claims | How to check it on your Digitakt II | Match? |
|---|---|---|---|
| 1 | It is called **"Elektron Digitakt II"** | Read the name on the front of the machine | ☐ yes ☐ no |
| 2 | It has **16 tracks** | Count the track buttons | ☐ yes ☐ no |
| 3 | Default **MIDI channel 1** | `SETTINGS` → `MIDI CONFIG` → `CHANNELS` — look at the **Auto Channel** | ☐ yes ☐ no |
| 4 | Manufacturer ID **00 20 3c** | Nothing to check | n/a |

> **On the track count:** count the buttons you press to *select a track*, not
> the sixteen step buttons underneath. On the original Digitakt those are two
> different rows. If you are unsure, say so rather than guessing — "I wasn't
> sure how to count this" is a genuinely useful answer.

> **On the MIDI channel:** if yours is set to something other than 1, that may
> just be because *you* changed it at some point. Tell us what it is set to
> **and** whether you remember changing it. Both facts matter.

---

## Step 5 — Tell us what you found

Reply with this, filled in:

```
Machine:          Digitakt  /  Digitakt II     (circle one)

1. Name matches:           yes / no
2. Track count matches:    yes / no   — I counted: ____
3. Auto Channel is:        ____       — did I change it? yes / no / don't remember

Anything that looked odd:
```

**If something does not match, that is a success, not a failure.** Finding a
wrong number is exactly why we asked you to do this. Please do not "round" an
answer to what you think we want.

---

# PART B — Capture a backup file from your Digitakt

**Why we need this.** Part A checks facts we read from the manual. This part
gets us something no manual can give: **the actual bytes your Digitakt
produces.** We need those to teach the app how your machine stores its
settings. Until someone sends us a real file, that work cannot start — this is
the missing piece, and you are the person who can supply it.

**You are not installing anything or changing your Digitakt.** You are asking
it to send a copy of a project, the same way you would make a backup, and
saving that copy as a file.

---

## What Part B is, in one sentence

Your Digitakt can send a copy of a project over USB. You catch that copy with
a free program and save it as a file ending in `.syx`. Then you send us the
file.

---

## Step 6 — Get a program that can catch the file

You need one free program. Pick the one for your computer:

| Your computer | Program | Where |
|---|---|---|
| **Mac** | SysEx Librarian | `https://www.snoize.com/SysExLibrarian/` |
| **Windows** | MIDI-OX | `http://www.midiox.com/` |

Download it, install it, open it. Both are small, long-established free tools.

> **If you already own something that records SysEx** — Elektron Transfer, a
> DAW, anything — use that instead. Any tool that saves a `.syx` file is fine.

---

## Step 7 — Connect the Digitakt

1. Plug the Digitakt into your computer with the USB cable.
2. Turn the Digitakt on.
3. In the program from Step 6, set the **input / source** to your Digitakt.
   It will appear by name in a dropdown — "Elektron Digitakt" or similar.

> **If the Digitakt does not appear in the list:** try a different USB cable
> first. Some cables are charge-only and carry no data — this is by far the
> most common cause, and it is not something you did wrong.

---

## Step 8 — Tell the program to start listening

- **SysEx Librarian (Mac):** click **Record One** (or **Record Many**). It
  will say it is waiting.
- **MIDI-OX (Windows):** open **View → SysEx**, then **Command Window →
  Receive Manual Dump**.

The program now sits waiting. Nothing happens until you do Step 9.

---

## Step 9 — Send the kit from the Digitakt

On the Digitakt itself:

1. Press **`SETTINGS`**.
2. Go to **`SYSEX DUMP`**.
3. Choose **`SYSEX SEND`**.
4. Choose **`KIT`** — the currently loaded kit, **not** the whole project.
5. Press **`YES`** to send.

> **Why a kit and not the whole project:** a kit is a few kilobytes; a whole
> project can be hundreds of times larger. These files get committed into the
> project's history permanently, so smaller is genuinely better. A kit is also
> exactly what the software models.

The Digitakt shows a progress bar. The program on your computer should show
data arriving — a size in bytes, or a new row in a list.

> **Honest note:** these menu names are from the Rytm and Analog Four, which
> use the same scheme. **We have not confirmed them on a Digitakt.** If your
> menus differ, that is useful information — tell us what you actually see and
> we will correct the instructions. You are the first person doing this.

> **If nothing arrives:** check the program is still in "waiting/record" mode
> — some tools time out after 30 seconds and need restarting before you press
> `YES`.

---

## Step 10 — Save the file

1. In the program, **save** what it caught. Choose a filename ending in
   **`.syx`**.
2. Name it exactly like this, so the files sort and read cleanly:
   - `digitakt_mk1_kit_filter_000.syx` — or `digitakt_ii_...` if you have a II
3. Note the file size. **A kit should be a few kilobytes.** If you got
   hundreds of kilobytes you probably sent the whole project — redo Step 9 and
   choose `KIT`.

Where the files go is Step 11.

---

## Step 11 — Run one command; it does the rest

You do **not** have to create folders, compute checksums, or write the
provenance note by hand. One command does all of it.

Capture **both** files first (Step 13 explains the second one), then run:

```
.venv/bin/python scripts/intake_digitakt_capture.py \
  --device digitakt_mk1 \
  --low  ~/Desktop/low.syx \
  --high ~/Desktop/high.syx \
  --captured-by "Steve" \
  --os-version "1.52A" \
  --menu-path "SETTINGS > SYSEX DUMP > SYSEX SEND > KIT"
```

Change these to match you:

| Part | What to put |
|---|---|
| `--device` | `digitakt_mk1` or `digitakt_ii` |
| `--low` / `--high` | where you saved the two files |
| `--captured-by` | your name |
| `--os-version` | from `SETTINGS > SYSTEM > OS VERSION` on the Digitakt |
| `--menu-path` | **the exact menu names you actually pressed** |

> **On Windows,** start the command with `.venv\Scripts\python.exe` instead of
> `.venv/bin/python`, and put it all on one line.

### What it does for you

- Checks the files really are Digitakt dumps — and tells you plainly if you
  sent the whole project by mistake, or if the capture tool caught nothing.
- Checks the two files actually differ, so "I forgot to move the knob" is
  caught immediately rather than three weeks later.
- Creates `tests/fixtures/digitakt_saved_kit/`, copies the files in with
  consistent names, computes the SHA256s.
- Writes the provenance note automatically.

**If anything is wrong it stops and writes nothing**, so a failed run never
leaves a half-finished mess behind. Read the message — it says what to redo.

It is **passive**: it reads your files and writes into the project folder. It
never opens a MIDI port and never contacts your Digitakt.

---

## Step 12 — Send it

The command prints where it put everything. Then either:

- **Simplest:** send Eddie the whole `tests/fixtures/digitakt_saved_kit`
  folder. Done.
- **If you use git:** commit that folder on a new branch and open a pull
  request. Do **not** commit to `main` or `modularize-v1.34`.

### One thing that really matters

**Use a disposable kit, not your real work.** Make a new kit, leave it
initialized, change only what Step 13 asks. This keeps your own material out of
a public repository and makes the file far easier for us to read.

---

## Step 13 — The second capture (this is the important one)

If you have another ten minutes, this doubles the value of Part B:

1. Do Steps 8–10 again, but **before** sending, change **exactly one thing**:
   turn **track 1's filter frequency** knob to its **highest** setting. Change
   nothing else.
2. Save it as `digitakt_mk1_kit_filter_127.syx` (or `digitakt_ii_...`).

So you end up with a matched pair: the same kit, differing only in one knob.

**Why this matters so much:** with two files that differ in exactly one known
way, we can find where that setting lives in the file by comparing them. With
only one file we would be guessing. This one extra capture is worth more than
anything else in this document.

Record in the Step 12 note **which knob you moved and what the display showed**
(e.g. "track 1 FILTER FREQ, 0 in the first file, 127 in the second"). The
on-screen number is more useful to us than "most of the way up".

---

## What we do with your files

We compare the bytes, find where each setting lives, and write that into the
app with your files kept as the evidence. Nothing is sent back to your
Digitakt.

**Your files contain your project** — pattern and sound settings. They do not
contain audio samples, and they carry nothing personal. If your project is
private, send a throwaway one instead: make a new empty project, tweak a
couple of knobs, and capture that. It works just as well for our purposes.

---

## Things that might go wrong

| What you see | What it means | What to do |
|---|---|---|
| `command not found: .venv/bin/python` | The project is not set up on this machine yet | Send Eddie the exact text you see |
| `No such file or directory` | You are in the wrong folder | Re-check Step 2 |
| No `Device digitakt_...` block anywhere | Wrong version of the app | Send Eddie the first 20 lines of output |
| Only Rytm and Analog Four are listed, no Digitakt | You are on an older version | Send Eddie a screenshot |
| Terminal output looks like a wall of nonsense | Normal — most of it is irrelevant | Scroll to your `Device digitakt_...` block |

### Part B problems

| What you see | What it means | What to do |
|---|---|---|
| Digitakt not in the program's device list | Usually a charge-only USB cable | Try a different cable first |
| Program catches nothing when you press `YES` | It stopped waiting | Restart the record/receive step, then send again |
| Menu names on the Digitakt do not match Step 9 | Expected — we have not confirmed these on a Digitakt | **Tell us what you actually see.** This is useful, not a failure |
| Saved file is 0 bytes | Nothing was captured | Redo Steps 8–9; make sure recording starts *before* you press `YES` |

**Any error at all: copy the text, paste it in a message, send it.** Do not try
to fix it. A screenshot works too.

---

## Stuck? Paste this into ChatGPT or Claude

You do not have to wait on Eddie to get unstuck. Copy everything in the box
below into ChatGPT, Claude, or whichever assistant you use, then describe your
problem underneath it.

The prompt tells the assistant what you are doing, what is safe, and — most
importantly — **to say "I don't know" rather than guess about your hardware.**
That last part matters: a confident wrong answer about a menu path will waste
more of your time than a plain "ask Eddie".

```text
I am helping test a music-software project. I am not a programmer, so please
explain things simply and one step at a time.

MY HARDWARE: an Elektron Digitakt (or Digitakt II) drum machine/sampler,
connected to my computer by USB.

WHAT I AM DOING, in two parts:

PART A - I run one command in a terminal and read four facts off the screen,
then check them against my actual machine:
  1. the device name
  2. the number of tracks (should be 8 on a Digitakt, 16 on a Digitakt II)
  3. the default MIDI channel (Auto Channel, in SETTINGS > MIDI CONFIG >
     CHANNELS)
  4. the manufacturer ID (00 20 3c - I do not need to check this one)

The command is one of these, run from the project folder:
  macOS/Linux:  .venv/bin/python -m rytm_randomizer.cli live-gui-device-inventory-report
  Windows:      .venv\Scripts\python.exe -m rytm_randomizer.cli live-gui-device-inventory-report

PART B - I capture a SysEx dump from the Digitakt and save it as a .syx file:
  - a free catcher program (SysEx Librarian on Mac, MIDI-OX on Windows)
  - set its MIDI input to the Digitakt, put it in record/receive mode
  - on the Digitakt: SETTINGS > SYSEX DUMP > SYSEX SEND > KIT > YES
    (a KIT, not the whole PROJECT - a kit is a few kilobytes, a project is
    hundreds of times larger and these files get committed permanently)
  - save the result as a .syx file
  - do it twice: once with track 1 filter frequency at its LOWEST, once at its
    HIGHEST, changing nothing else between them
  - then I run ONE command that validates the files, files them, computes
    checksums and writes the provenance note for me:
      .venv/bin/python scripts/intake_digitakt_capture.py --device digitakt_mk1
        --low <low.syx> --high <high.syx> --captured-by "Steve"
        --os-version "<from SETTINGS > SYSTEM>" --menu-path "<what I pressed>"
    (Windows: .venv\Scripts\python.exe instead of .venv/bin/python)
    If it prints an error it has written nothing -- the message says what to
    redo. Help me read it rather than working around it.

IMPORTANT SAFETY FACTS - please do not suggest anything that contradicts these:
  - This software CANNOT send anything to my Digitakt. It is receive-only by
    design. My patterns, samples and projects cannot be altered by it.
  - In Part B the data flows one way only: FROM the Digitakt TO my computer.
  - I should never be asked to install firmware, reset my device, factory
    reset, or overwrite a project. If a step seems to ask for that, stop and
    tell me to check with the project owner.

HOW I WANT YOU TO HELP:
  - Explain terminal commands before I run them, in plain language.
  - Help me read error messages and tell me what they mean.
  - Help me find menus on the Digitakt and set up the catcher program.
  - Ask me what I see on screen rather than assuming.

CRITICAL - WHEN YOU DO NOT KNOW:
  The exact Digitakt menu path for SysEx dump has NOT been confirmed on real
  hardware by the project. It is an educated guess based on other Elektron
  devices. If my menus do not match, DO NOT invent a path that sounds
  plausible. Say you are not certain, and tell me to report what I actually
  see. A wrong guess here costs more time than saying "I don't know".

  The same applies to anything else you are unsure about. I would much rather
  hear "I'm not sure, ask Eddie" than a confident answer that turns out wrong.

MY PROBLEM IS:
[describe what happened, and paste any error text or what your screen shows]
```

**One thing to watch for:** if the assistant tells you to do something that
writes *to* the Digitakt — install, update, reset, overwrite, restore — stop
and ask Eddie. Nothing in this test requires that.

---

## What happens next

If your numbers match, we mark the Digitakt facts as hardware-verified and
that unblocks the next stage of the work.

If something does not match, we fix the wrong number and ask you to check that
one thing again. That is a five-minute follow-up, not a repeat of everything.

---

## For the record — what this test does NOT cover

Being straight about the limits, so nobody later thinks this proved more than
it did:

- **Part A** does not verify the Digitakt's saved-project byte layout. Those
  offsets stay unverified and the code refuses to use them.
- **Part B does not verify them either** — it *collects the evidence* that
  lets us do that work later. Sending the files does not make the app able to
  control your Digitakt; that is a separate change with its own review.
- It does **not** test sending anything to the device, because that capability
  deliberately does not exist yet.
- It does **not** test capture, mutation, or any performance feature for the
  Digitakt — there are none.

This test covers the **identity facts only**: name, track count, default MIDI
channel, manufacturer ID. That is the full scope, and it is the part that is
currently unverified.

---

*Questions: ask Eddie. There is no wrong question here, and "I don't
understand this step" is the most useful thing you can tell us — it means the
instructions need fixing, not you.*
