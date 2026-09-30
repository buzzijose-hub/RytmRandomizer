# Touch performance appliance

`#/appliance` is a dedicated presentation of the existing Cockpit. STUDIO returns
to the full desktop workflow. Choose RYTM, A4 or BOTH, then use SCOPE to select
pads/tracks, pages, track/page depth and parameter protection. Empty targets select
**nothing** here; legacy scope behavior stays unchanged. Locks win. Master, track
and page depth multiply before the shared engine rounds once to the source's
native integer precision. Captured A4 fixed-point fields retain their fractional
bits and show exact display values. Zero depth does not stage a mutation. Changing a slider affects the
next roll and never applies or undoes a previous roll.

MUTATE stages a diff; APPLY requires the exact current candidate confirmation.
Context, scope, profile or connection changes revoke it. Duplicate/stale actions
fail. Simulation APPLY updates local history and sends zero MIDI. Simulated A4
numbers are normalized seven-bit illustration values, not native fractional
encodings or working hardware state. Unsupported categorical controls remain
protected with a reason instead of being interpolated.

NEW ANCHOR remembers the known local source. UNDO, REDO and RETURN TO ANCHOR
navigate local history; none restores instrument RAM or an entire KIT.
CAPTURE/RESYNC is separate: choose a unique exact input, then manually send the KIT
from that instrument during the input-only window. The registered family codec
validates the dump. This proves saved-state evidence only; checksums, timestamps
and round trips cannot establish unsaved front-panel state. Automatic requests
remain unavailable without verified request/response evidence. No device save is
performed to obtain a capture.

New scoped appliance live APPLY remains blocked pending working-state readback
and precise applied-delta restore evidence. Existing Studio Rytm live audition
remains available under its established source reload, arming and exact action
confirmation procedure. General A4 and linked BOTH live apply remain blocked;
neither lane sends when linked preflight fails. Local-send acceptance never means
physical hardware verification.

Before Pi or full-set acceptance, complete the
[first computer hardware gate](COCKPIT_QUICKSTART.md#first-computer-hardware-gate)
using the existing studio checklist. Rytm uses guarded Show Kit audition,
manual source reload and fresh whole-payload verification; a changed,
in-scope, unlocked paired control makes the whole plan unready. Supported
packets can remain for inspection, but none is transmitted and no MSB-only or
partial subset is applied. The KIT capture provider requires one exact
input-name match before opening. The separate, supervised A4 single-CC app probe
does not enable A4 or BOTH in this surface. USB discovery alone proves neither
backup/configuration nor physical mutation or recovery.

Scope presets include device/fingerprint associations. Production recall refuses
unknown or different kit identity. Presets never persist arming, candidates,
pending commands, capture authority or history. Versioned storage holds at most
32 presets/64 KiB and publishes atomically. Corruption is preserved on read;
explicit validated IMPORT recovers it while retaining original bytes in a sibling
recovery file. Newer schemas cannot be overwritten by a rollback build. Diagnostics
shows storage errors. Optional physical mappings emit the same touch intents;
no GPIO pins activate without a selected board configuration and controls cannot
arm or implicitly confirm APPLY. Numeric adjustment and profile naming work
through visible touch keypads.
Dialog titles, Close and confirmation/cancellation actions stay visible while
the contents scroll. On compact screens, the target picker retains the full
12-pad layout; long parameter lists and connection details scroll within their
own panel.

| Variable | Default and purpose |
|---|---|
| `RYTM_RAND_APPLIANCE_SIMULATION` | unset/production; exact `1` enables no-output simulation |
| `RYTM_RAND_APPLIANCE_PROFILE_FILE` | `default_profiles_dir().parent / "appliance-scopes.json"` (Linux: `$XDG_CONFIG_HOME/rytm-randomizer/`, default `~/.config/rytm-randomizer/`); server-owned path, never supplied over the wire |

See [deployment](PI_APPLIANCE_DEPLOYMENT.md), [capability matrix](PI_APPLIANCE_CAPABILITIES.md)
and the [execution ledger](superpowers/plans/2026-09-30-pi-performance-appliance_STATE.json).
Physical Pi boot/touch/cable/audio acceptance is separate from desktop checks.
