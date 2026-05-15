# DataAnalysisGuardrails reference

Detailed reference for the `DataAnalysisGuardrails` skill. Read this
file when you are running an analysis - the tight `SKILL.md` holds the
procedure, this holds the exhaustive checklist.

The principles in `MusicLibraryGuardrails/reference.md` (reference ->
discovery, the safety floor, the lifecycle state machine) apply here
too; do not duplicate them. This reference focuses on the
*parameter/capture* side.

---

## Core principles

1. **Never treat raw parameter data as automatically safe.** Factory
   sounds, captured kits, SysEx dumps, MIDI captures, user-created
   patches are reference material - filtered through musical role,
   live-safety, and hardware-specific constraints.
2. **Separate analysis from action.** Analysis may study wide ranges;
   mutation code only uses approved ranges. No new MIDI behavior
   without validation.
3. **Anchors remain permanent.** Validated anchors are always the
   safety net. Captured anchors are optional additions, not
   replacements.
4. **Every parameter needs a reason.** A parameter only enters a
   mutation profile if it supports the role of that pad/track.
5. **Use conservative defaults.** Expand ranges only after testing.
   Prefer stable live-safe behavior over dramatic unpredictable
   changes.

---

## Data sources this skill can analyze

- Analog Rytm MK2 SysEx dumps
- Analog Four MK2 SysEx dumps
- MIDI CC/NRPN capture logs
- Existing RytmRandomizer Python profiles
- Factory sound studies
- User-created kit studies
- Manual parameter tables
- Validation notes
- Mutation logs
- Favorite/discarded mutation history

---

## Step 1 - Identify device + role

For Analog Rytm MK2:

- Pad 1: kick / low-end foundation
- Pad 2: snare / secondary percussion
- Pad 3: bass / synth-percussion / SY Raw motion
- Pad 4: body / impact / accent
- Pads 5-12: future expansion only

For Analog Four MK2:

- Track 1: mono bass / low synth
- Track 2: stab / rhythmic synth / acid-style motion
- Track 3: pad / drone / chord pressure
- Track 4: FX / noise / tension / sci-fi accent

**Guardrail:** never analyze a parameter without first assigning it to
a musical role. The WS-W validator's semantic layer rejects any
`GuardrailBound` whose pad has no `RoleAssignment`.

---

## Step 2 - Classify parameter risk

### Low-risk - usually safe for wider mutation

- Filter cutoff within role-specific range
- Filter envelope amount within approved range
- Decay within approved range
- LFO depth when destination is safe
- Delay/reverb sends on non-low-end tracks
- Noise level on percussion/accent roles

### Medium-risk - constrained ranges

- Oscillator tuning
- Filter resonance
- Overdrive
- LFO speed
- LFO destination
- Envelope attack/release
- Delay feedback
- Reverb amount
- Filter type

### High-risk - locked by default

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

The WS-W validator forces every high-risk parameter to `LOCKED_DEFAULT`
or `FORBIDDEN` regardless of what the draft says.

---

## Step 3 - Determine mutation scope

Sort parameters into scopes; a mutation command must declare its scope
before changing values.

Analog Rytm MK2 scopes:

```
MACHINE, SRC, FILTER, AMP, LFO, FX SEND, SCENE/GLOBAL
```

Analog Four MK2 scopes:

```
OSC, FILTER, AMP/DRIVE, ENV, LFO, FX SEND, VOICE/POLY, PERFORMANCE
```

---

## Step 4 - Build safe ranges from data

When analyzing a dataset:

1. Extract all values for the parameter.
2. Group by device, pad/track, machine/patch type, musical role.
3. Remove outliers that are not musically representative.
4. Calculate a conservative range from the central useful values.
5. Compare against known project preferences.
6. Mark the range with a `GuardrailClass`:
   - `LIVE_SAFE`
   - `STUDIO_DISCOVERY`
   - `EXPERIMENTAL`
   - `LOCKED_DEFAULT`
   - `FORBIDDEN`

---

## Step 5 - Protect low-end roles

For kick and bass:

- Avoid wide tuning jumps
- Avoid excessive reverb
- Avoid excessive delay
- Avoid high resonance spikes
- Avoid aggressive HP filtering unless clearly an accent mode
- Avoid volume changes
- Avoid untested machine switching live

Analog Rytm: Pad 1 kick stable; Pad 3 SY Raw can move, tuning + balance
controlled.

Analog Four: Track 1 bass protects pitch + voice priority + low-end
stability; Track 3 pad can be wider and more atmospheric.

---

## Step 6 - Voice and polyphony guardrails (Analog Four)

Four voices total.

- Track 1 bass must be protected from voice stealing.
- Track 3 pad/chord must not consume the entire voice pool by default.
- Track 4 FX/accent must not steal from Track 1.
- Unison off by default unless explicitly tested.
- Poly settings are high-risk.
- Voice routing documented before mutation.

---

## Step 7 - LFO guardrails

Before allowing an LFO mutation, define:

- Destination
- Depth range
- Speed range
- Mode/trigger behavior
- Whether it is live-safe or studio-only

Safe LFO destinations:

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

**Guardrail:** pitch LFOs must be shallow and role-approved.

---

## Step 8 - FX guardrails

Default locked / heavily limited:

- Delay feedback
- Reverb send on kick/bass
- Chorus depth on low-end tracks
- Overdrive on already-loud sounds
- External input level
- Any global/master effect level

Use wider FX ranges on:

- Analog Four Track 3 pad/drone
- Analog Four Track 4 FX/noise/tension
- Rytm accent/percussion lanes, not the main kick

---

## Step 9 - Capture-state guardrails

### Soft capture

Captures what the software already knows.

### True hardware capture

Reads actual hardware state, likely via SysEx parsing.

Rules:

- Captured anchors do not replace validated anchors.
- Captured anchors are marked temporary until saved.
- Mutations from captured anchors still obey role-based ranges.
- A/B compare + undo available before wide mutation.
- Captured data logged with timestamp + device.

---

## Step 10 - Mutation approval checklist

Before adding any analyzed range into code:

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

## Forbidden by default

Never mutate these unless explicitly approved and documented:

- Master volume
- Track volume
- Clock
- Transport
- Pattern change
- Program change
- Project change
- Kit clear/save commands
- Factory reset / system commands
- Calibration / system commands
- Unvalidated SysEx writes
- Unvalidated machine changes during live performance
- Unvalidated Analog Four poly/voice changes

---

## Legacy report format (kept for reference)

The pre-schema Markdown report shape. The typed `GuardrailProfile`
covers the same content with closed enums + content hashing + lifecycle
state.

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
- Discovery 1, 2, 3

## Proposed Safe Ranges
| Device | Pad/Track | Role | Parameter | Range | Mode | Risk | Notes |

## Locked / Avoided Parameters
| Parameter | Reason |

## Recommended Profile Changes
- Change 1, 2

## Requires Hardware Validation
- Test 1, 2

## Decision
Approved for:
- [ ] Documentation only
- [ ] Studio discovery
- [ ] Live-safe mutation
- [ ] Code implementation
```

---

## Naming conventions

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

## Final rule

When in doubt, do not widen ranges. Document the finding first. Test on
hardware. Then promote it from:

```
Documentation -> Studio Discovery -> Live-Safe Mutation -> Code Default
```

This is the lifecycle the schema's `ProfileState` machine encodes
formally: `DRAFT -> VALIDATED -> STUDIO_TESTED -> LIVE_APPROVED`. The
resolver enforces it at session-start time.
