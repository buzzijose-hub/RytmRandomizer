# Digitakt verification — step-by-step

**For:** Steve
**Time needed:** about 20 minutes
**What you need:** your Digitakt (or Digitakt II), a USB cable, and a computer

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

**You do not even need to plug it in for most of this test.** Steps 1–3 read
numbers out of the app. Step 4 is the only one where your hardware matters,
and it is just you looking at your machine.

---

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

## Things that might go wrong

| What you see | What it means | What to do |
|---|---|---|
| `command not found: .venv/bin/python` | The project is not set up on this machine yet | Send Eddie the exact text you see |
| `No such file or directory` | You are in the wrong folder | Re-check Step 2 |
| No `Device digitakt_...` block anywhere | Wrong version of the app | Send Eddie the first 20 lines of output |
| Only Rytm and Analog Four are listed, no Digitakt | You are on an older version | Send Eddie a screenshot |
| Terminal output looks like a wall of nonsense | Normal — most of it is irrelevant | Scroll to your `Device digitakt_...` block |

**Any error at all: copy the text, paste it in a message, send it.** Do not try
to fix it. A screenshot works too.

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

- It does **not** verify the Digitakt's saved-project byte layout. Those
  offsets are still unverified and the code refuses to use them.
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
