# MusicLibraryGuardrails reference

Detailed reference for the `MusicLibraryGuardrails` skill. Read this
file when you are actually running an analysis - the tight `SKILL.md`
holds the procedure; this file holds the *exhaustive* feature
checklists, per-style mutation examples, role-behavior defaults, scene
conventions, and the canonical output shape.

This reference complements `GUARDRAILS_DESIGN_SPEC.md` (sections 4-7);
do not redefine concepts here, point at the spec where it already
defines them.

---

## Use this skill for

- A single song
- A folder of songs
- A DJ tool library
- User's own unreleased tracks
- A live recording
- Factory sound references
- A reference playlist
- A style target such as rolling techno, hypnotic techno, Birmingham
  techno, hardgroove, Schranz, Stigmata-style pressure, Jeff
  Mills-style attack, Developer-style hypnosis, etc.

---

## Expected inputs

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

If audio files are not available, analyze from the available metadata
and user description, but mark the result as **description-based**, not
audio-measured (the schema's `Confidence.LOW` does this for you in
`Provenance.confidence`).

---

## SourceType taxonomy (closed enum on the schema)

```
SINGLE_TRACK
FOLDER_LIBRARY
REFERENCE_PLAYLIST
USER_RELEASE_LIBRARY
LIVE_RECORDING
FACTORY_SOUND_STUDY
STYLE_DESCRIPTION_ONLY
```

## Confidence taxonomy

```
HIGH    = direct audio / complete data available (extract_from_audio /
          analyze_library produced the FeatureReport)
MEDIUM  = partial audio plus user notes (extract_from_partial)
LOW     = user description only (extract_from_description)
```

---

## Step-by-step (the full checklist)

### Step 1 - Identify scope

Use the `SourceType` enum above. Decide whether you are analyzing one
track, a library, a playlist, the user's own catalogue, a live set, a
factory-sound study, or a written style description.

### Step 2 - Extract musical features

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

In the typed draft, these populate
`MusicalCharacter.musical_findings` (a frozen `Mapping[str, str]` with
keys like `tempo_groove`, `low_end_behavior`, `percussion_density`,
`bass_tonal_movement`, `texture_noise`, `fx_space`,
`arrangement_energy_arc`).

### Step 3 - Style tags

Assign 3-8 tags into `MusicalCharacter.style_tags`. Example tags:

```
rolling, hypnotic, hardgroove, raw, industrial-leaning, Birmingham,
Schranz, tribal, metallic, sci-fi, dark, minimal, peak-time,
tool-based, dense, sparse, dry, washed, gritty, clean
```

**Guardrail:** style tags describe behavior, not marketing hype.

### Step 4 - Map music features to device roles

Translate musical observations into Rytm pad / Analog Four track roles.
Populate `RoleMapping.assignments` with one `RoleAssignment(role,
mutation_direction)` per pad.

#### Analog Rytm MK2 roles (today)

```
Pad 1 = kick / low-end foundation
Pad 2 = snare / secondary percussion
Pad 3 = bass / synth-percussion / SY Raw motion
Pad 4 = body / impact / accent
Pads 5-12 = future expansion: hats, cymbals, toms, claps, rides,
            percussion, texture (not yet wired)
```

#### Analog Four MK2 roles (reserved)

```
Track 1 = mono bass / low synth
Track 2 = stab / rhythmic synth / acid-style motion
Track 3 = pad / drone / chord pressure
Track 4 = FX / noise / tension / sci-fi accent
```

**Guardrail:** do not create mutation ranges until each musical
feature has been mapped to a device role. The WS-W validator's semantic
layer rejects any `GuardrailBound` whose pad does not have a
`RoleAssignment` first.

### Step 5 - Derive mutation behavior (per-style examples)

#### Rolling and hypnotic

Use: smaller pitch ranges, stable kick anchors, moderate filter
movement, subtle LFO depth, repeated rhythmic motifs, gradual scene
transitions, low-to-medium FX changes. Avoid: large tuning jumps,
chaotic machine switching, extreme delay feedback, aggressive volume
changes.

#### Raw peak-time

Use: stronger overdrive range, tighter envelopes, brighter
hats/percussion, more aggressive filter movement, higher density
mutation scenes, controlled grit. Avoid: washing out low-end with
reverb, too much random pitch movement, sudden bass disappearance.

#### Sci-fi / hypnotic / metallic

Use: safe LFO movement, noise/tone modulation, band-limited metallic
textures, Track 4 / Pad 3 motion, moderate FX modulation. Avoid: deep
bass pitch instability, untested LFO-to-volume or LFO-to-pitch
extremes.

### Step 6 - Risk-tier the parameters

#### Low risk - wider variation usually OK

Filter cutoff (role-safe range), decay (role-safe), noise level on
percussion/accent roles, FX send on pad/accent roles, safe LFO depth.

#### Medium risk - constrain carefully

Resonance, overdrive, oscillator tune, filter type, delay/reverb send,
LFO speed/destination, envelope attack/release.

#### High risk - locked by default (the safety floor)

Track volume, master volume, clock, transport, pattern/program/project
change, kit save/clear, extreme oscillator tuning, Analog Four
poly/voice changes, unvalidated SysEx, live machine switching.

WS-W's validator forces every high-risk parameter to `LOCKED_DEFAULT`
or `FORBIDDEN` regardless of what the draft says. Mark them correctly
upfront.

### Step 7 - Build guardrail classes

Closed enum from the schema:

```
LIVE_SAFE         - modest range, no spikes, anchor-return available
STUDIO_DISCOVERY  - wider; audition before performance
EXPERIMENTAL      - high movement; needs manual review
LOCKED_DEFAULT    - not mutated unless user unlocks
FORBIDDEN         - never mutated by this tool
```

Each `GuardrailBound` carries exactly one class.

### Step 8 - Per-role guardrail defaults

#### Kick / low-end foundation (Pad 1)

Protect pitch, volume, decay-from-extremes. Avoid reverb/delay wash,
high-resonance spikes, sudden HP filtering. Mutate filter/tone
modestly.

#### Snare / secondary percussion (Pad 2)

Allow snap/noise/body and controlled decay variation; moderate filter
movement. Avoid volume/FX spikes.

#### Bass / synth-percussion (Pad 3)

Protect root/pitch center. Allow controlled filter motion, moderate
timbre changes, safe-destination LFO. Avoid wide pitch LFO live.

#### Body / impact / accent (Pad 4)

Allow body and accent variation; the widest of the four pads, but
level-safe.

#### Hats / cymbals / metallic percussion (future Pads 5-12)

Allow decay/brightness variation; allow texture variation; avoid harsh
resonance peaks; avoid excessive level increase.

#### Pad / drone / atmosphere (Analog Four T3)

Allow wider FX; allow slower LFO movement; allow broader filter
sweeps; protect against voice stealing on Analog Four.

#### FX / noise / tension (Analog Four T4)

Allow the widest range; keep output level safe; avoid overwhelming the
mix; return-to-anchor must be available.

### Step 9 - Build scene guardrails

Populate `scenes: tuple[SceneGuardrail, ...]`. Each
`SceneGuardrail(scene_key, pads_allowed, mutation_depth, risk_class,
locked_roles)` defines a scene's behavior.

Common scene keys:

```
ROLLING_LIGHT, ROLLING_PUSH,
DEEPER_GROOVE, DEEPER_PRESSURE,
INTENSE_MOTION, INTENSE_GRIT,
WILD_CONTROLLED, WILD_MAXIMUM,
BREAKDOWN, REBUILD, RESET_CLEAN
```

### Step 10 - The typed draft

Construct the `GuardrailProfile` directly. The artifact is the output -
not free-form JSON, not Markdown. The schema lives at
`rytm_randomizer/guardrails/schema.py`.

Minimum required fields:

```python
GuardrailProfile(
    provenance=Provenance(...),
    character=MusicalCharacter(...),
    role_mapping=RoleMapping(assignments={1: RoleAssignment(...), ...}),
    bounds=(GuardrailBound(...), ...),
    locked_default=(...),
    forbidden=(...),
    scenes=(SceneGuardrail(...), ...),
    state=ProfileState.DRAFT,
    schema_version=SCHEMA_VERSION,
    content_hash=compute_content_hash(profile_without_hash),
)
```

Two-pass construction: build with `content_hash=""`, compute
`compute_content_hash(profile)`, replace via `dataclasses.replace`.

### Step 11 - Hardware validation checklist

Every draft profile must end with a hardware validation checklist that
WS-W's resolver requires before promoting to `LIVE_APPROVED`:

```
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

## Special rules

### User's own music library

Prioritize: recurring sonic identity, preferred low-end behavior,
common BPM zone, recurring percussion density, texture families,
favorite mutation directions, what should remain stable during live
performance, what can be pushed during discovery. Do not overfit to one
track unless the user asks for a one-track profile.

### Reference artists / commercial songs

Do: describe high-level musical traits, create style-aware guardrails,
suggest original anchor directions, preserve the user's sonic identity.

Do NOT: recreate exact melodies, provide copied arrangement maps, claim
to clone a specific artist, instruct direct imitation, generate a
sound-alike patch intended to pass as the original. (The schema *can
not* express these even if you wanted to - it has no field for them.)

Language to use:

```
inspired by the reference behavior, style-aware guardrails, energy
profile, texture profile, mutation boundaries, original anchor
direction
```

Language to avoid:

```
clone this track, copy this sound exactly, make it identical
```

---

## Legacy JSON template (kept for reference)

The pre-schema JSON template carried these fields. The typed schema
covers them all and adds tamper-evident hashing + a closed lifecycle:

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

## Final rule

Analysis is not implementation. A music library or song can define
**direction**, **ranges**, and **guardrails**. Only hardware validation
can promote those guardrails into live-safe defaults
(`ProfileState.LIVE_APPROVED`). Until then the profile is `DRAFT`,
`VALIDATED`, or `STUDIO_TESTED` - the resolver enforces this at
session-start time.
