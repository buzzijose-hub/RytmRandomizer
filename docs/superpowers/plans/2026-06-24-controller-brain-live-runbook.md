# Controller Brain Live Runbook + State Contract Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive controller-brain live runbook and derived state contract that turns the OXI/E16-style hardware-controller idea into deterministic stage, inspect, fire, recover, queued-intent, and audit-event metadata without opening controller input, WebSocket dispatch, MIDI ports, or hardware sends.

**Architecture:** Add report modules under `rytm_randomizer/reports/` that compose existing passive controller rehearsal, OXI live set strategy, and Cockpit performance console payloads. Wire them through the existing passive CLI registry pattern with text/JSON output, update operator docs, and keep all action surfaces explicitly blocked until a future approved controller bridge exists.

**Tech Stack:** Python 3.11, frozen dataclasses, existing `cli_registry.make_passive_report_command`, existing `reports.formatter.passive_report_lines`, pytest, ruff, black, isort.

---

## File Structure

- Create `rytm_randomizer/reports/controller_brain_live_runbook.py`
  - Owns the new report dataclasses, deterministic composition, JSON payload, text formatter, passive CLI command, and `__all__`.
- Create `tests/test_controller_brain_live_runbook_report.py`
  - Verifies report composition, controller gesture bindings, readiness gates, text/JSON CLI behavior, argument rejection, and no real-MIDI imports.
- Create `rytm_randomizer/reports/controller_brain_live_state.py`
  - Derives passive state rows, queued intents, audit events, readiness gates, blocked bridge actions, JSON payloads, text formatter, passive CLI command, and `__all__` from the runbook.
- Create `tests/test_controller_brain_live_state_report.py`
  - Verifies state-row composition, queued-intent/audit-event JSON, readiness gates, text/JSON CLI behavior, argument rejection, help text, defensive helpers, and no real-MIDI imports.
- Modify `rytm_randomizer/cli.py`
  - Adds lazy import entries for `controller-brain-live-runbook-report` and `controller-brain-live-state-report`.
- Modify `rytm_randomizer/help_text.py`
  - Adds command usage, detailed help, top-level command list, and help resolver registration.
- Modify `README.md` and `docs/CLI_REFERENCE.md`
  - Documents the new passive report and how it differs from armed hardware paths.
- Modify `docs/STATUS.md`
  - Records the bundle as passive/mock-safe progress.
- Modify `tests/fixtures/cli_help_expected.txt` and `tests/test_cli.py`
  - Keeps top-level help and operator-facing docs tests aligned.
- Create `rytm_randomizer/reports/controller_brain_live_bridge_readiness.py`
  - Derives bridge contract packets, bridge-readiness gates, blocked runtime
    actions, JSON payloads, text formatter, passive CLI command, and `__all__`
    from the live state contract.
- Create `tests/test_controller_brain_live_bridge_readiness_report.py`
  - Verifies contract-packet composition, ready/blocked gate counts, text/JSON
    CLI behavior, argument rejection, help text, defensive helpers, and
    no-real-MIDI imports.

## Task 1: Add the Red Tests

- [ ] **Step 1: Create `tests/test_controller_brain_live_runbook_report.py`**

```python
def test_live_runbook_composes_controller_oxi_and_console_packets() -> None:
    from rytm_randomizer.reports.controller_brain_live_runbook import (
        build_controller_brain_live_runbook_report,
    )

    report = build_controller_brain_live_runbook_report()

    assert report.runbook_version == "controller-brain-live-runbook-v1"
    assert report.runbook_status == "passive-ready"
    assert report.controller_profile_key == "generic-16-encoder-performance"
    assert report.controller_template_row_count == 112
    assert report.controller_page_count == 7
    assert report.gesture_count == 9
    assert report.live_chapter_count == 7
    assert report.console_status == "mock-safe"
```

- [ ] **Step 2: Run the new test and verify it fails**

Run:

```powershell
python -m pytest tests\test_controller_brain_live_runbook_report.py -n 0 -q
```

Expected: fail with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.controller_brain_live_runbook'`.

## Task 2: Implement the Passive Report Model

- [ ] **Step 1: Create `rytm_randomizer/reports/controller_brain_live_runbook.py`**

Implement frozen dataclasses:

```python
@dataclass(frozen=True)
class ControllerBrainRunbookStep:
    step: int
    intent_key: str
    controller_assignment: str
    controller_gesture: str
    operator_goal: str
    stage_action: str
    inspect_action: str
    fire_policy: str
    recovery_action: str
    target_device: str
    target_scope: str
    readiness: str
    blocked_action: str
```

Compose existing payloads from:

```python
build_controller_brain_rehearsal_payload()
build_oxi_live_set_strategy_payload()
live_gui_performance_console_model_payload()
```

Use helper functions that safely narrow `dict[str, object]`, `list[object]`, and `str` values. The report must stay deterministic and passive.

- [ ] **Step 2: Run the report tests and verify they pass**

Run:

```powershell
python -m pytest tests\test_controller_brain_live_runbook_report.py -n 0 -q
```

Expected: all tests in the new file pass.

## Task 3: Wire the Passive CLI and Help Text

- [ ] **Step 1: Add lazy command registration**

Modify `rytm_randomizer/cli.py`:

```python
"controller-brain-live-runbook-report": (
    "rytm_randomizer.reports.controller_brain_live_runbook",
    "CONTROLLER_BRAIN_LIVE_RUNBOOK_CLI_COMMAND",
),
```

- [ ] **Step 2: Add help text**

Modify `rytm_randomizer/help_text.py` to include:

```text
controller-brain-live-runbook-report [--json]
```

and a detailed help function that says the command is passive, opens no controller input, dispatches no WebSocket command, opens no MIDI port, and sends no MIDI.

- [ ] **Step 3: Verify CLI behavior**

Run:

```powershell
python -m pytest tests\test_controller_brain_live_runbook_report.py tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -n 0 -q
```

Expected: new report tests pass; top-level help fails only until the fixture is updated.

## Task 4: Update Operator Docs

- [ ] **Step 1: Update README**

Add a sample command near the current OXI/controller CLI examples:

```bash
python -m rytm_randomizer.cli controller-brain-live-runbook-report --json
```

- [ ] **Step 2: Update CLI reference**

Add the command to the OXI/live/controller table and describe that it composes controller rehearsal, OXI set strategy, and Cockpit console evidence into a passive runbook.

- [ ] **Step 3: Update status**

Add one concise `docs/STATUS.md` entry noting the passive runbook, no hardware behavior, and verification status.

## Task 5: Verify and Prepare the PR

- [ ] **Step 1: Run targeted tests**

```powershell
python -m pytest tests\test_controller_brain_live_runbook_report.py tests\test_cli.py tests\test_real_midi_passive_cli_safety.py -n 0 -q
```

- [ ] **Step 2: Run architecture and lint**

```powershell
python -m pytest tests\architecture\ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [ ] **Step 3: Run fast and full suites**

```powershell
python -m pytest -m fast
python -m pytest
```

- [ ] **Step 4: Commit, push, and open one PR**

Use one cohesive PR against `modularize-v1.34`, not a stacked base. Include this plan link and the full 18-gate checklist in the PR body.

## Task 6: Extend the Same PR With the Passive Live State Contract

- [x] **Step 1: Add red tests for `controller-brain-live-state-report`**

The tests pin the derived state rows, queued intents, audit events, readiness gates,
blocked bridge actions, CLI text/JSON behavior, detailed help text, defensive
helpers, and no-real-MIDI-import contract.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_state.py`**

The implementation composes `controller-brain-live-runbook-report` rather than
inventing a second source of truth. Every runbook step becomes a deterministic
`state.*` row, `queued.*` intent, and `audit.*` event with fire blocked until an
approved controller bridge exists.

- [x] **Step 3: Wire CLI, help, README, CLI reference, status, and help fixture**

The new command sits beside the runbook command and remains passive/read-only:
no MIDI controller input, no MIDI learn/raw CC capture, no WebSocket dispatch,
no MIDI port opening, no MIDI send, and no snapshot mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 9: Extend the Same PR With Passive Feedback Rehearsal

- [x] **Step 1: Add red tests for `controller-brain-live-feedback-rehearsal-report`**

The tests pin a fifth passive layer that composes
`controller-brain-live-dispatch-rehearsal-report` into metadata-only feedback
frames, feedback zones, blocked output gates, text/JSON CLI behavior, help text,
defensive helpers, and the no-real-MIDI-import contract. The expected red state
is a missing `rytm_randomizer.reports.controller_brain_live_feedback_rehearsal`
module and a missing passive CLI command registration.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_feedback_rehearsal.py`**

The implementation builds from
`build_controller_brain_live_dispatch_rehearsal_report()`, turns every shadow
dispatch decision into deterministic LED, encoder-ring, and display metadata,
summarizes state/queue/audit feedback zones, and keeps controller output,
WebSocket feedback, MIDI output, hardware feedback, and snapshot mutation
blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness, and
dispatch-rehearsal commands and remains passive/read-only: no MIDI controller
output, no controller feedback emission, no WebSocket feedback dispatch, no
runtime reducer execution, no MIDI port opening, no MIDI send, and no snapshot
mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 10: Extend the Same PR With Passive Cockpit Handoff

- [x] **Step 1: Add red tests for `controller-brain-live-cockpit-handoff-report`**

The tests pin a sixth passive layer that composes
`controller-brain-live-feedback-rehearsal-report` into GUI-ready handoff cards,
Cockpit panel summaries, disabled Cockpit controls, text/JSON CLI behavior,
help text, defensive helpers, and the no-real-MIDI-import contract. The
expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_cockpit_handoff` module and a
missing passive CLI command registration.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_cockpit_handoff.py`**

The implementation builds from
`build_controller_brain_live_feedback_rehearsal_report()`, turns every metadata
feedback frame into a deterministic disabled Cockpit handoff card, summarizes
GUI panels, records disabled runtime/output controls, and keeps controller
input, reducers, WebSocket dispatch, controller output, MIDI output, hardware
send, and snapshot mutation blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, and feedback-rehearsal commands and remains
passive/read-only: no controller input, no runtime reducer execution, no
WebSocket dispatch, no controller feedback emission, no MIDI controller output,
no MIDI port opening, no MIDI send, and no snapshot mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 11: Extend the Same PR With Passive Implementation Bridge

- [x] **Step 1: Add red tests for `controller-brain-live-implementation-bridge-report`**

The tests pin a seventh passive layer that composes
`controller-brain-live-cockpit-handoff-report` into disabled future-GUI
implementation bindings, fixture bundles, implementation gates, text/JSON CLI
behavior, help text, defensive helpers, and the no-real-MIDI-import contract.
The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_implementation_bridge` module, a
missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_implementation_bridge.py`**

The implementation builds from
`build_controller_brain_live_cockpit_handoff_report()`, turns every disabled
Cockpit handoff card into deterministic implementation-binding metadata,
records fixture bundles and implementation gates, and keeps GUI launch, GUI
renderer startup, runtime reducers, WebSocket dispatch, controller feedback,
MIDI output, hardware send, and snapshot mutation blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, and Cockpit-handoff commands and
remains passive/read-only: no GUI launch, no GUI renderer start, no runtime
reducer execution, no WebSocket dispatch, no controller feedback emission, no
MIDI controller output, no MIDI port opening, no MIDI send, and no snapshot
mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 12: Extend the Same PR With Passive Desktop Blueprint

- [x] **Step 1: Add red tests for `controller-brain-live-desktop-blueprint-report`**

The tests pin an eighth passive layer that composes
`controller-brain-live-implementation-bridge-report` into desktop regions,
component contracts, view-model bindings, fixture hints, acceptance checks,
text/JSON CLI behavior, help text, defensive helpers, and the
no-real-MIDI-import contract. The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_desktop_blueprint` module, a
missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_desktop_blueprint.py`**

The implementation builds from
`build_controller_brain_live_implementation_bridge_report()`, turns every
disabled implementation binding into deterministic desktop component metadata,
declares future desktop regions and view-model bindings, records fixture hints
and acceptance checks, and keeps GUI launch, GUI renderer startup, runtime
reducers, WebSocket dispatch, controller feedback, MIDI output, hardware send,
snapshot mutation, and fixture file writing blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, Cockpit-handoff, and
implementation-bridge commands and remains passive/read-only: no GUI launch, no
GUI renderer start, no runtime reducer execution, no WebSocket dispatch, no
controller feedback emission, no MIDI controller output, no MIDI port opening,
no MIDI send, no snapshot mutation, and no file writing.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 13: Extend the Same PR With Passive Desktop App Plan

- [x] **Step 1: Add red tests for `controller-brain-live-desktop-app-plan-report`**

The tests pin a ninth passive layer that composes
`controller-brain-live-desktop-blueprint-report` into disabled future app
routes, component file hints, state slices, style tokens, acceptance checks,
text/JSON CLI behavior, help text, defensive helpers, and the no-real-MIDI
import contract. The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_desktop_app_plan` module, a
missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_desktop_app_plan.py`**

The implementation builds from
`build_controller_brain_live_desktop_blueprint_report()`, turns every disabled
desktop region into an app route, turns every component contract into an
advisory component file hint and disabled state slice, declares future style
tokens and acceptance checks, and keeps GUI launch, app launch, renderer
startup, runtime reducers, WebSocket dispatch, controller feedback, MIDI
output, hardware send, snapshot mutation, and file writing blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, Cockpit-handoff, implementation-bridge,
and desktop-blueprint commands and remains passive/read-only: no GUI launch, no
app launch, no GUI renderer start, no runtime reducer execution, no WebSocket
dispatch, no controller feedback emission, no MIDI controller output, no MIDI
port opening, no MIDI send, no snapshot mutation, and no file writing.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 14: Extend the Same PR With Passive Desktop Component Contracts

- [x] **Step 1: Add red tests for `controller-brain-live-desktop-component-contract-report`**

The tests pin a tenth passive layer that composes
`controller-brain-live-desktop-app-plan-report` into disabled future component
API contracts, view-model prop contracts, disabled event contracts, test hooks,
fixture contracts, acceptance checks, text/JSON CLI behavior, help text,
defensive helpers, and the no-real-MIDI import contract. The expected red state
is a missing
`rytm_randomizer.reports.controller_brain_live_desktop_component_contract`
module, a missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_desktop_component_contract.py`**

The implementation builds from
`build_controller_brain_live_desktop_app_plan_report()`, turns every advisory
component file hint into a disabled future component API contract, turns every
disabled state slice into a future `viewModel` prop contract, declares disabled
event contracts, test hooks, fixture contracts, and acceptance checks, and keeps
GUI launch, app launch, renderer startup, runtime reducers, WebSocket dispatch,
controller feedback, MIDI output, hardware send, snapshot mutation, and file
writing blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture diagrams, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, Cockpit-handoff, implementation-bridge,
desktop-blueprint, and desktop-app-plan commands and remains passive/read-only:
no GUI launch, no app launch, no GUI renderer start, no runtime reducer
execution, no WebSocket dispatch, no controller feedback emission, no MIDI
controller output, no MIDI port opening, no MIDI send, no snapshot mutation,
and no file writing.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 16: Extend the Same PR With Passive Desktop Render Contracts

- [x] **Step 1: Add red tests for `controller-brain-live-desktop-render-contract-report`**

The tests pin a twelfth passive layer that composes
`controller-brain-live-desktop-view-model-report` into disabled future render
surfaces, one-way render bindings, render guards, render assertions,
acceptance checks, text/JSON CLI behavior, help text, defensive helpers, and
the no-real-MIDI import contract. The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_desktop_render_contract`
module, missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_desktop_render_contract.py`**

The implementation builds from
`build_controller_brain_live_desktop_view_model_report()`, turns every future
component view model into a disabled future render surface, maps state
bindings into disabled one-way render bindings, maps disabled action models
into render guards, carries source render assertions into render-contract
assertions, declares acceptance checks, and keeps GUI launch, app launch,
component mounting, renderer execution, runtime reducers, WebSocket dispatch,
controller feedback, MIDI output, hardware send, snapshot mutation, and file
writing blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture diagrams, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, Cockpit-handoff,
implementation-bridge, desktop-blueprint, desktop-app-plan,
desktop-component-contract, and desktop-view-model commands and remains
passive/read-only: no GUI launch, no app launch, no component mount, no GUI
renderer start, no renderer execution, no runtime reducer execution, no
WebSocket dispatch, no controller feedback emission, no MIDI controller
output, no MIDI port opening, no MIDI send, no snapshot mutation, and no file
writing.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 15: Extend the Same PR With Passive Desktop View Models

- [x] **Step 1: Add red tests for `controller-brain-live-desktop-view-model-report`**

The tests pin an eleventh passive layer that composes
`controller-brain-live-desktop-component-contract-report` into future component
view models, state bindings, disabled action models, render assertions,
acceptance checks, text/JSON CLI behavior, help text, defensive helpers, and
the no-real-MIDI import contract. The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_desktop_view_model` module, a
missing passive CLI command registration, and missing help text.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_desktop_view_model.py`**

The implementation builds from
`build_controller_brain_live_desktop_component_contract_report()`, turns every
future component API contract into a disabled future component view model,
maps prop contracts into passive state bindings, maps event contracts into
disabled action models, declares render assertions and acceptance checks, and
keeps GUI launch, app launch, renderer startup, runtime reducers, WebSocket
dispatch, controller feedback, MIDI output, hardware send, snapshot mutation,
and file writing blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture diagrams, and help fixture**

The new command sits beside the runbook, live-state, bridge-readiness,
dispatch-rehearsal, feedback-rehearsal, Cockpit-handoff,
implementation-bridge, desktop-blueprint, desktop-app-plan, and
desktop-component-contract commands and remains passive/read-only: no GUI
launch, no app launch, no GUI renderer start, no runtime reducer execution, no
WebSocket dispatch, no controller feedback emission, no MIDI controller output,
no MIDI port opening, no MIDI send, no snapshot mutation, and no file writing.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 8: Extend the Same PR With Passive Dispatch Rehearsal

- [x] **Step 1: Add red tests for `controller-brain-live-dispatch-rehearsal-report`**

The tests pin a fourth passive layer that composes
`controller-brain-live-bridge-readiness-report` into shadow-dispatch decisions,
dry-run dispatch groups, blocked transport gates, text/JSON CLI behavior, help
text, defensive helpers, and the no-real-MIDI-import contract. The expected red
state is a missing
`rytm_randomizer.reports.controller_brain_live_dispatch_rehearsal` module and a
missing passive CLI command registration.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_dispatch_rehearsal.py`**

The implementation must not duplicate runbook/state/bridge facts. It builds from
`build_controller_brain_live_bridge_readiness_report()`, turns every bridge
contract packet into a deterministic shadow-dispatch decision, summarizes
state/queue/audit dispatch groups, and keeps controller input, reducer
execution, WebSocket dispatch, controller feedback, MIDI output, hardware send,
and snapshot mutation blocked.

- [x] **Step 3: Wire CLI, help, CLI reference, status, architecture docs, and help fixture**

The new command sits beside the runbook, live-state, and bridge-readiness
commands and remains passive/read-only: no MIDI controller input, no MIDI
learn/raw CC capture, no runtime reducer execution, no WebSocket dispatch, no
controller feedback, no MIDI port opening, no MIDI send, and no snapshot
mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.

## Task 7: Extend the Same PR With Passive Controller Bridge Readiness

- [x] **Step 1: Add red tests for `controller-brain-live-bridge-readiness-report`**

The tests pin a third passive layer that composes
`controller-brain-live-state-report` into bridge contract packets, ready/blocked
readiness gates, blocked runtime actions, text/JSON CLI behavior, help text, and
the no-real-MIDI-import contract. The expected red state is a missing
`rytm_randomizer.reports.controller_brain_live_bridge_readiness` module and
missing passive CLI command registration.

- [x] **Step 2: Implement `rytm_randomizer/reports/controller_brain_live_bridge_readiness.py`**

The implementation must not duplicate the runbook/source facts. It builds from
`build_controller_brain_live_state_report()`, turns every `state.*`,
`queued.*`, and `audit.*` row into a deterministic bridge packet, marks only the
state/queue/audit contracts ready, and keeps controller input, runtime reducer,
WebSocket dispatch, MIDI output, hardware send, feedback output, and snapshot
mutation blocked.

- [x] **Step 3: Wire CLI, help, README, CLI reference, status, and help fixture**

The new command sits beside the runbook and live-state commands and remains
passive/read-only: no MIDI controller input, no MIDI learn/raw CC capture, no
runtime reducer execution, no WebSocket dispatch, no controller feedback, no
MIDI port opening, no MIDI send, and no snapshot mutation.

- [x] **Step 4: Re-run focused, architecture, lint, fast/full, coverage, vulture, and pre-push checks**

Use this expanded same-PR verification set before amending and force-with-lease
pushing PR #200.
