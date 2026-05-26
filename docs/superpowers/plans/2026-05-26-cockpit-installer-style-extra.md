# Cockpit Installer Style Extra Plan - 2026-05-26

> Status: in-flight

## Goal

Fix the manual/install path that lets the Cockpit Profile Wizard launch but
fails audio analysis with `StyleAnalysisDependencyError` because the runtime did
not install the style analyzer dependency.

## Scope

- Keep the existing passive default and MIDI hardware guardrails unchanged.
- Keep `mido==1.3.3` and `python-rtmidi==1.5.8` pinned exactly.
- Make `pip install -e ".[dev]"` enough for local manual cockpit testing.
- Make `pip install -e ".[cockpit]"` enough for sidecar-only cockpit runtime.
- Make Briefcase app runtime requirements include the same cockpit sidecar and
  audio analyzer dependencies for all supported platforms.
- Update installer/manual/style docs so the operator path matches packaging.

## Non-Goals

- Do not change the desktop UI, 4-pad placeholder state, export button behavior,
  snapshot semantics, or hardware send path.
- Do not open MIDI ports, send MIDI, or touch hardware.
- Do not regenerate V1.34 parity fixtures.

## Verification

- `python -m pytest tests/architecture/test_cockpit_runtime_dependencies.py -n 0`
- `python -m pytest tests/architecture/ -q`
- `python -m pytest -m fast`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`
- `python scripts/code_review_gate.py --mode cli`

## Plan Requirements Reference

Per `docs/PLAN_REQUIREMENTS.md`, this is a narrow packaging/docs bugfix. The
main gates touched are dependency safety, passive/no-hardware behavior, tests,
docs freshness, and reviewability. The change avoids architecture movement and
does not alter byte-frozen V1.34 engine/group/scene outputs.
