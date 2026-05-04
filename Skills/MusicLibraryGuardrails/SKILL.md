# RytmRandomizer Music Library / Song Analysis Guardrails Skill

## Purpose

This skill defines a repeatable process for analyzing a song, reference track, folder of songs, DJ tools, live recordings, factory sounds, or a broader music library, then translating the musical findings into **mutation guardrails** for the RytmRandomizer project.

The purpose is not to copy songs, clone artists, or recreate copyrighted works exactly.

The purpose is:

**Reference → Discovery**

Use musical analysis to build safe, style-aware mutation boundaries for Analog Rytm MKII and Analog Four MKII performance systems.

---

## Core Rule

A reference track or music library can influence the guardrails.

It should not become a replica target.

The output should describe:

- energy behavior
- groove behavior
- density
- tonal range
- percussion role
- bass behavior
- texture
- movement
- tension/release
- mutation-safe ranges

The output should not attempt to directly copy melodies, arrangement, copyrighted hooks, or full sound design from a protected work.

---

## Use This Skill For

Use this skill when the user asks to analyze:

- A single song
- A folder of songs
- A DJ tool library
- User's own unreleased tracks
- A live recording
- Factory sound references
- A reference playlist
- A style target such as rolling techno, hypnotic techno, Birmingham techno, hardgroove, Schranz, Stigmata-style pressure, Jeff Mills-style attack, Developer-style hypnosis, etc.

---

## Expected Inputs

Possible inputs include:

- Audio file(s): WAV, AIFF, FLAC, MP3
- Folder path or exported library list
- Track names and written notes
- BPM/key information
- User-provided descriptions
- DAW exports
- MIDI captures
- SysEx captures
- Existing mutation logs
- Existing RytmRandomizer profiles

If audio files are not available, analyze from the available metadata and user description, but clearly mark the result as **description-based**, not audio-measured.

---

## Required Output

Every analysis should produce a guardrail profile, not only a summary.

Minimum output:

1. Music summary
2. Role mapping
3. Energy/density profile
4. Groove profile
5. Frequency/texture profile
6. Mutation-safe ranges
7. Locked parameters
8. Studio-discovery ranges
9. Live-safe ranges
10. Hardware validation checklist

---

# Analysis Workflow

## Step 1 — Identify Scope

Classify the analysis request:

```text
SINGLE_TRACK
FOLDER_LIBRARY
REFERENCE_PLAYLIST
USER_RELEASE_LIBRARY
LIVE_RECORDING
FACTORY_SOUND_STUDY
STYLE_DESCRIPTION_ONLY
```

Then classify confidence:

```text
HIGH = direct audio or complete data available
MEDIUM = partial audio/data plus user notes
LOW = user description only
```

---

## Step 2 — Extract Musical Features

For a single song, analyze:

- BPM / tempo stability
- Groove feel
- Kick density
- Snare/clap/rim density
- Hat/percussion density
- Bass movement
- Tonal center or tonal ambiguity
- Low-end weight
- Midrange pressure
- High-frequency brightness
- Noise/texture amount
- FX/reverb/delay presence
- Arrangement arc
- Intensity curve
- Repetition vs variation
- Tension/release strategy

For a library, analyze:

- BPM distribution
- Common energy zones
- Common groove types
- Common low-end behavior
- Common texture families
- Typical track length
- Density clusters
- Bright vs dark clusters
- Clean vs gritty clusters
- Hypnotic vs chaotic clusters
- Live-safe common ranges
- Outlier behaviors

---

## Step 3 — Create Style Tags

Assign 3–8 tags.

Example tags:

```text
rolling
hypnotic
hardgroove
raw
industrial-leaning
Birmingham
Schranz
tribal
metallic
sci-fi
dark
minimal
peak-time
tool-based
dense
sparse
dry
washed
gritty
clean
```

Guardrail:

- Style tags should describe behavior, not marketing hype.

---

## Step 4 — Map Music Features to Device Roles

Translate musical observations into RytmRandomizer roles.

### Analog Rytm MKII Roles

```text
Pad 1 = kick / low-end foundation
Pad 2 = snare / secondary percussion
Pad 3 = bass / synth-percussion / SY Raw motion
Pad 4 = body / impact / accent
Pads 5–12 = future hats, cymbals, toms, claps, rides, percussion, texture
```

### Analog Four MKII Roles

```text
Track 1 = mono bass / low synth
Track 2 = stab / rhythmic synth / acid-style motion
Track 3 = pad / drone / chord pressure
Track 4 = FX / noise / tension / sci-fi accent
```

Guardrail:

- Do not create mutation ranges until each musical feature has been mapped to a device role.

---

## Step 5 — Derive Mutation Behavior

Convert musical traits into mutation behavior.

Examples:

### If the reference is rolling and hypnotic

Use:

- smaller pitch ranges
- stable kick anchors
- moderate filter movement
- subtle LFO depth
- repeated rhythmic motifs
- gradual scene transitions
- low-to-medium FX changes

Avoid:

- large tuning jumps
- chaotic machine switching
- extreme delay feedback
- aggressive volume changes

### If the reference is raw and peak-time

Use:

- stronger overdrive range
- tighter envelopes
- brighter hats/percussion
- more aggressive filter movement
- higher density mutation scenes
- controlled grit

Avoid:

- washing out low-end with reverb
- too much random pitch movement
- sudden bass disappearance

### If the reference is sci-fi / hypnotic / metallic

Use:

- safe LFO movement
- noise/tone modulation
- band-limited metallic textures
- Track 4 / Pad 3 motion
- moderate FX modulation

Avoid:

- deep bass pitch instability
- untested LFO-to-volume or LFO-to-pitch extremes

---

## Step 6 — Classify Parameter Risk

Every proposed mutation parameter must be classified.

### Low Risk

Often safe for wider variation:

- Filter cutoff in role-safe range
- Decay in role-safe range
- Noise level on percussion/accent roles
- FX send on pad/accent roles
- LFO depth to safe destinations

### Medium Risk

Constrain carefully:

- Resonance
- Overdrive
- Oscillator tune
- Filter type
- Delay send
- Reverb send
- LFO speed
- LFO destination
- Envelope attack/release

### High Risk

Locked by default:

- Track volume
- Master volume
- Clock
- Transport
- Pattern change
- Program change
- Project change
- Kit save/clear
- Extreme oscillator tuning
- Analog Four voice/poly changes
- Unvalidated SysEx writes
- Live machine switching unless tested

---

## Step 7 — Build Guardrail Classes

Every derived range must be assigned one of these classes:

```text
LIVE_SAFE
STUDIO_DISCOVERY
EXPERIMENTAL
LOCKED_DEFAULT
FORBIDDEN
```

### LIVE_SAFE

Can be used during performance.

Characteristics:

- modest range
- no volume spikes
- no destructive changes
- stable low-end
- anchor return available

### STUDIO_DISCOVERY

Useful for finding new sounds, but not default for live use.

Characteristics:

- wider ranges
- more surprise
- possible instability
- must be auditioned before performance

### EXPERIMENTAL

Potentially interesting but risky.

Characteristics:

- high movement
- strong timbral change
- possible harshness
- likely needs manual review

### LOCKED_DEFAULT

Not changed unless user unlocks it.

### FORBIDDEN

Should not be mutated by this tool.

---

## Step 8 — Derive Per-Role Guardrails

Create guardrails by musical role.

### Kick / Low-End Foundation

Default behavior:

- Protect pitch
- Protect volume
- Protect decay from extremes
- Avoid reverb/delay wash
- Avoid high resonance spikes
- Avoid sudden HP filtering
- Mutate filter and tone modestly

### Snare / Secondary Percussion

Default behavior:

- Allow snap/noise/body variation
- Allow controlled decay variation
- Allow moderate filter movement
- Avoid excessive volume or FX spikes

### Bass / Synth-Percussion

Default behavior:

- Protect root/pitch center
- Allow controlled filter motion
- Allow moderate waveform/timbre changes
- Allow LFO if destination is safe
- Avoid wide pitch LFO live

### Hats / Cymbals / Metallic Percussion

Default behavior:

- Allow decay/brightness variation
- Allow texture variation
- Avoid harsh resonance peaks
- Avoid excessive level increase

### Pad / Drone / Atmosphere

Default behavior:

- Allow wider FX
- Allow slower LFO movement
- Allow broader filter sweeps
- Protect against voice stealing on Analog Four

### FX / Noise / Tension

Default behavior:

- Allow the widest range
- Keep output level safe
- Avoid overwhelming the mix
- Return-to-anchor must be available

---

## Step 9 — Build Scene Guardrails

Convert the analysis into scene behavior.

Common scene examples:

```text
ROLLING_LIGHT
ROLLING_PUSH
DEEPER_GROOVE
DEEPER_PRESSURE
INTENSE_MOTION
INTENSE_GRIT
WILD_CONTROLLED
WILD_MAXIMUM
BREAKDOWN
REBUILD
RESET_CLEAN
```

Each scene must define:

- Which pads/tracks it may touch
- Which scopes it may touch
- Mutation depth
- Risk class
- Locked roles
- Anchor return behavior

Example:

```text
Scene: ROLLING_LIGHT
Risk: LIVE_SAFE
Rytm: kick locked, snare subtle, bass/synth-perc subtle filter movement
A4: bass stable, stab subtle, pad mild width
FX: low
```

---

## Step 10 — Produce a Mutation Guardrail Profile

Output a structured profile in Markdown and optionally JSON.

Suggested profile fields:

```json
{
  "profile_name": "",
  "source_type": "",
  "confidence": "",
  "style_tags": [],
  "bpm_range": [],
  "energy_profile": "",
  "density_profile": "",
  "device_roles": {},
  "live_safe": {},
  "studio_discovery": {},
  "experimental": {},
  "locked_default": [],
  "forbidden": [],
  "hardware_validation_tests": []
}
```

---

## Step 11 — Hardware Validation Checklist

Before implementation, define tests.

Every guardrail profile should end with:

```text
Requires hardware validation:
- Load known anchors
- Apply live-safe mutation
- Confirm low-end stability
- Confirm no volume spike
- Confirm anchor return works
- Confirm no pattern/transport/clock messages are sent
- Confirm locked parameters remain untouched
- Save useful results on hardware manually
```

---

# Special Rules for User's Own Music Library

If analyzing the user's own library, prioritize:

- recurring sonic identity
- preferred low-end behavior
- common BPM zone
- recurring percussion density
- texture families
- favorite mutation directions
- what should remain stable during live performance
- what can be pushed during discovery

Do not overfit to one track unless the user asks for a one-track profile.

---

# Special Rules for Reference Artists / Commercial Songs

When analyzing reference artists or commercial tracks:

Do:

- describe high-level musical traits
- create style-aware guardrails
- suggest original anchor directions
- preserve the user's sonic identity

Do not:

- recreate exact melodies
- provide exact copied arrangement maps
- claim to clone a specific artist
- instruct direct imitation
- generate a sound-alike patch intended to pass as the original

Use language like:

```text
inspired by the reference behavior
style-aware guardrails
energy profile
texture profile
mutation boundaries
original anchor direction
```

Avoid language like:

```text
clone this track
copy this sound exactly
make it identical
```

---

# Output Report Template

Use this template for every analysis.

```markdown
# Music Analysis to Mutation Guardrails Report

## Source
- Source name:
- Source type:
- Device target:
- Confidence:
- Date:

## Summary
Short summary of the musical behavior.

## Style Tags
- tag
- tag
- tag

## Musical Findings
### Tempo / Groove
### Low-End Behavior
### Percussion Density
### Bass / Tonal Movement
### Texture / Noise
### FX / Space
### Arrangement / Energy Arc

## Rytm Role Mapping
| Pad | Role | Finding | Mutation Direction |
|---|---|---|---|

## Analog Four Role Mapping
| Track | Role | Finding | Mutation Direction |
|---|---|---|---|

## Live-Safe Guardrails
| Device | Pad/Track | Scope | Parameter Group | Range/Behavior | Notes |
|---|---|---|---|---|---|

## Studio-Discovery Guardrails
| Device | Pad/Track | Scope | Parameter Group | Range/Behavior | Notes |
|---|---|---|---|---|---|

## Locked by Default
| Parameter/Behavior | Reason |
|---|---|

## Forbidden
| Parameter/Behavior | Reason |
|---|---|

## Suggested Scene Behavior
| Scene | Risk | Device Behavior | Notes |
|---|---|---|---|

## Hardware Validation Tests
- Test 1
- Test 2
- Test 3

## Decision
Approved for:
- [ ] Documentation only
- [ ] Studio discovery
- [ ] Live-safe testing
- [ ] Code implementation
```

---

# Final Rule

Analysis is not implementation.

A music library or song can define **direction**, **ranges**, and **guardrails**.

Only hardware validation can promote those guardrails into live-safe defaults.
