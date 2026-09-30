---
name: pi-appliance-source-evidence
description: Maintain the shared Cockpit Pi appliance's source-bound runtime, exact native value previews, and distinct simulation/capture/hardware authority.
---

# Pi appliance source and evidence

Use this when changing the appliance runtime or its captured-value presentation.

- Run the production preview from the integrated checkout. A Python executable
  from another editable installation can silently import that other checkout;
  the appliance launcher must bind its source root before importing the package
  and reject an already-loaded foreign package. A successful HTTP response alone
  does not prove which source was loaded.
- `RYTM_RAND_MIDI_BACKEND=off` disables enumeration, not the existing explicit
  arm handler. Simulation seals the session's arm authority during composition,
  before private bootstrap injection. Test an actual arm attempt against a fake
  provider, including after the environment variable changes.
- Resolve Rytm rows by machine, original catalog section and parameter. Compact
  keys such as `tun` and `dec` are not globally unique. An unavailable pad value
  remains unknown; do not label another track's value as track 1.
- A4 saved-state values use the existing typed codec and canonical frame check.
  Mutate native integer words and scale once; format Q8.8/Q8.7 display values
  exactly. Match `osc1_tune`/`osc2_tune` exactly: `endswith('tune')` also matches
  the distinct bipolar Detune field. FIN is a shared pitch-word component and
  cannot be independently randomized.
- Readable saved-state values and software-only previews confer no live SEND or
  restore capability. Keep unknown bytes in the retained source, and retain
  individual row blockers. New codecs cannot turn old saved values into proof
  of unsaved working RAM.
- Test the actual production bundle at all three viewport targets. Count touch
  targets and inspect clipping; unit coverage does not establish touch usability.
  Private launch credentials stay outside screenshots, logs, URLs and packages.

See `docs/PI_APPLIANCE_OPERATOR.md`, `docs/PI_APPLIANCE_CAPABILITIES.md` and
`docs/PI_APPLIANCE_DEPLOYMENT.md` for the current product contract.
