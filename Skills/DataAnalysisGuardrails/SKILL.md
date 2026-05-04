# RytmRandomizer Data Analysis Guardrails Skill

## Purpose

This skill defines how to analyze Analog Rytm MKII and Analog Four MKII data for the RytmRandomizer project without producing unsafe, unmusical, or project-breaking recommendations.

The goal is not blind randomization.

The goal is:

**Reference → Discovery**

Use source data to discover safe musical ranges, profile behavior, anchor logic, and mutation rules while preserving live performance safety.

---

## Core Principles

1. **Never treat raw parameter data as automatically safe.**
   - Factory sounds, captured kits, SysEx dumps, MIDI captures, and user-created patches are reference material.
   - They must be filtered through musical role, live-safety, and hardware-specific constraints.

2. **Separate analysis from action.**
   - Analysis may study wide ranges.
   - Mutation code should only use approved ranges.
   - No new MIDI behavior should be added without validation.

3. **Anchors remain permanent.**
   - Validated anchors are always the safety net.
   - Captured anchors are optional additions, not replacements.

4. **Every parameter needs a reason.**
   - A parameter should only enter a mutation profile if it supports the role of that pad/track.

5. **Use conservative defaults.**
   - Expand ranges only after testing.
   - Prefer stable live-safe behavior over dramatic unpredictable changes.

---

## Data Sources This Skill Can Analyze

Use this skill for:

- Analog Rytm MKII SysEx dumps
- Analog Four MKII SysEx dumps
- MIDI CC/NRPN capture logs
- Existing RytmRandomizer Python profiles
- Factory sound studies
- User-created kit studies
- Manual parameter tables
- Validation notes
- Mutation logs
- Favorite/discarded mutation history

---

## Analysis Workflow

### Step 1 — Identify Device and Role

Before analyzing values, classify the target:

For Analog Rytm MKII:

- Pad 1: kick / low-end foundation
- Pad 2: snare / secondary percussion
- Pad 3: bass / synth-percussion / SY Raw motion
- Pad 4: body / impact / accent
- Pads 5–12: future expansion only unless explicitly allowed

For Analog Four MKII:

- Track 1: mono bass / low synth
- Track 2: stab / rhythmic synth / acid-style motion
- Track 3: pad / drone / chord pressure
- Track 4: FX / noise / tension / sci-fi accent

Guardrail:

- Never analyze a parameter without assigning it to a musical role.

---

### Step 2 — Classify Parameter Risk

Every parameter should be assigned a risk level.

#### Low-Risk Parameters

Usually safe for wider mutation:

- Filter cutoff within role-specific range
- Filter envelope amount within approved range
- Decay within approved range
- LFO depth when destination is safe
- Delay/reverb sends on non-low-end tracks
- Noise level on percussion/accent roles

#### Medium-Risk Parameters

Use constrained ranges:

- Oscillator tuning
- Filter resonance
- Overdrive
- LFO speed
- LFO destination
- Envelope attack/release
- Delay feedback
- Reverb amount
- Filter type

#### High-Risk Parameters

Locked by default unless intentionally enabled:

- Track volume
- Master volume
- Pattern change
- Program change
- Transport
- Clock
- Project/kit save or clear commands
- Extreme oscillator tuning
- Poly/voice settings on Analog Four
- Machine switching during live performance unless validated
- Any SysEx write command that alters stored data

---

### Step 3 — Determine Mutation Scope

Do not mutate everything at once. Sort parameters into scopes.

Analog Rytm MKII scopes:

- MACHINE
- SRC
- FILTER
- AMP
- LFO
- FX SEND
- SCENE/GLOBAL

Analog Four MKII scopes:

- OSC
- FILTER
- AMP/DRIVE
- ENV
- LFO
- FX SEND
- VOICE/POLY
- PERFORMANCE

Guardrail:

- A mutation command must declare its scope before it changes values.

---

### Step 4 — Build Safe Ranges from Data

When analyzing a dataset:

1. Extract all values for the parameter.
2. Group by device, pad/track, machine/patch type, and musical role.
3. Remove outliers that are not musically representative.
4. Calculate a conservative range from the central useful values.
5. Compare against known project preferences.
6. Mark whether the range is:
   - Live-safe
   - Studio-discovery only
   - Experimental
   - Forbidden by default

Suggested labels:

```text
SAFE_LIVE
SAFE_STUDIO
EXPERIMENTAL
LOCKED_DEFAULT
FORBIDDEN
```

---

### Step 5 — Protect Low-End Roles

For kick and bass roles:

- Avoid wide tuning jumps.
- Avoid excessive reverb.
- Avoid excessive delay.
- Avoid high resonance spikes.
- Avoid aggressive HP filtering unless it is clearly an accent mode.
- Avoid volume changes.
- Avoid untested machine switching live.

Analog Rytm examples:

- Pad 1 kick should remain stable.
- Pad 3 SY Raw can move, but tuning and balance must remain controlled.

Analog Four examples:

- Track 1 bass should protect pitch, voice priority, and low-end stability.
- Track 3 pad can be wider and more atmospheric.

---

### Step 6 — Voice and Polyphony Guardrails for Analog Four MKII

Analog Four MKII has four voices total.

Rules:

- Track 1 bass must be protected from voice stealing.
- Track 3 pad/chord behavior must not consume the entire voice pool by default.
- Track 4 FX/accent should not steal from Track 1.
- Unison should be off by default unless explicitly tested.
- Poly settings should be treated as high-risk.
- Voice routing should be documented before mutation.

---

### Step 7 — LFO Guardrails

LFOs are powerful but dangerous.

Before allowing an LFO mutation, define:

- Destination
- Depth range
- Speed range
- Mode/trigger behavior
- Whether it is live-safe or studio-only

Safe LFO destinations often include:

- Filter cutoff
- Filter envelope amount
- Noise level
- Timbre/tone parameters
- FX send on atmosphere/accent roles

High-risk LFO destinations:

- Pitch
- Volume
- Master/level controls
- Machine selection
- Voice/poly settings
- Extreme oscillator modulation

Guardrail:

- Pitch LFOs must be shallow and role-approved.

---

### Step 8 — FX Guardrails

FX can quickly destroy live balance.

Default locked or heavily limited:

- Delay feedback
- Reverb send on kick/bass
- Chorus depth on low-end tracks
- Overdrive on already loud sounds
- External input level
- Any global/master effect level

Use wider FX ranges on:

- Analog Four Track 3 pad/drone
- Analog Four Track 4 FX/noise/tension
- Rytm accent/percussion lanes, not the main kick

---

### Step 9 — Capture-State Guardrails

Future capture features must distinguish between:

#### Soft Capture

Captures what the software already knows.

#### True Hardware Capture

Reads actual hardware state, likely through SysEx parsing.

Rules:

- Captured anchors do not replace validated anchors.
- Captured anchors must be marked temporary until saved.
- Mutations from captured anchors should still obey role-based ranges.
- A/B compare and undo should be available before wide mutation.
- Captured data should be logged with timestamp and device.

---

### Step 10 — Mutation Approval Checklist

Before adding any analyzed range into code, confirm:

- Device identified
- Pad/track role identified
- Parameter scope identified
- MIDI CC/NRPN/SysEx mapping confirmed
- Safe range defined
- Risk level assigned
- Live-safe or studio-discovery mode assigned
- Anchor return behavior confirmed
- Undo/state behavior considered
- No forbidden controls touched
- Test command planned
- Validation note will be recorded

---

## Forbidden by Default

Do not mutate these unless explicitly approved and documented:

- Master volume
- Track volume
- Clock
- Transport
- Pattern change
- Program change
- Project change
- Kit clear/save commands
- Factory reset/system commands
- Calibration/system commands
- Unvalidated SysEx writes
- Unvalidated machine changes during live performance
- Unvalidated Analog Four poly/voice changes

---

## Output Format for Analysis Reports

When analyzing a data source, produce results in this format:

```markdown
# Analysis Report: [Source Name]

## Source
- File:
- Device:
- Date analyzed:
- Data type:

## Summary
Brief description of what was found.

## Useful Discoveries
- Discovery 1
- Discovery 2
- Discovery 3

## Proposed Safe Ranges
| Device | Pad/Track | Role | Parameter | Range | Mode | Risk | Notes |
|---|---|---|---|---|---|---|---|

## Locked / Avoided Parameters
| Parameter | Reason |
|---|---|

## Recommended Profile Changes
- Change 1
- Change 2

## Requires Hardware Validation
- Test 1
- Test 2

## Decision
Approved for:
- [ ] Documentation only
- [ ] Studio discovery
- [ ] Live-safe mutation
- [ ] Code implementation
```

---

## Naming Recommendations

Use clear names for documents and branches.

Documents:

- `Docs/DATA_ANALYSIS_GUARDRAILS.md`
- `Docs/STATE_CAPTURE_ROADMAP.md`
- `Docs/ANALOG_FOUR_MUTATOR_PLAN.md`
- `Docs/PROJECT_TIMELINE_ROADMAP.md`

Branches:

- `analysis-factory-sounds`
- `feature-soft-capture`
- `feature-state-history`
- `a4-track1-prototype`
- `gui-one-screen-performance`

---

## Final Rule

When in doubt, do not widen ranges.

Document the finding first.

Then test on hardware.

Then promote it from:

```text
Documentation → Studio Discovery → Live-Safe Mutation → Code Default
```
