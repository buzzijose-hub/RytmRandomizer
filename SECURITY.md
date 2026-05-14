# Security Policy

RytmRandomizer is currently a private collaboration project. Security issues
should be reported directly to the repository owner rather than through public
issues until the repository is intentionally made public.

## Supported Branch

- `modularize-v1.34`
- active execution branches derived from it, such as `codex/*`

## Safety-Sensitive Areas

Treat these as high-sensitivity changes:

- real MIDI imports
- MIDI port opening
- MIDI sending
- active CLI behavior
- command dispatch or execution
- hardware mutation
- SysEx behavior
- packaging or dependency changes
- changes to `rytm_hybrid_randomizer_v134.py`

## Reporting

Send a concise report with:

- affected file
- observed behavior
- expected behavior
- reproduction steps
- whether hardware was involved

Do not run hardware-facing experiments without explicit owner approval.
