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
  Measure complete dialog header/footer visibility, including after scrolling.
  A 44-pixel button below the viewport does not satisfy immediate-action access.
  Scroll capture panels to their actual refusal text before recording error-state
  screenshots; a visible tab alone is not evidence of an understandable blocker.
  Private launch credentials stay outside screenshots, logs, URLs and packages.
- Release rollback must restore the previous release's service templates as well
  as its source pointer. Verify retained immutable file inventory before stopping
  the healthy service, preserve the user's autostart choice, and test releases
  whose launch settings differ. A wheelhouse receipt may certify only a fresh
  build's wheels, never leftover wheels from another source revision.
- Exercise both sides of platform-specific permission decisions on every host.
  Inject the runtime module's OS view without changing global `os.name`, which
  also controls `pathlib`. Assert directory and credential-file permissions;
  a Windows-only 100% coverage receipt does not establish POSIX branch coverage.
- Isolate log-capture handlers and restore their propagation and levels. A pytest
  capture handler attached to both a child logger and its ancestor counts one
  event twice. Privacy checks must distinguish verified source `pathname`
  metadata from request data: `/appliance_runtime.py` is a source file, while a
  unique path from an actual refused request must be absent from the whole record.

See `docs/PI_APPLIANCE_OPERATOR.md`, `docs/PI_APPLIANCE_CAPABILITIES.md` and
`docs/PI_APPLIANCE_DEPLOYMENT.md` for the current product contract.
