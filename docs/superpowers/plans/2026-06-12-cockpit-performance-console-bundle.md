# Cockpit Performance Console Bundle Implementation Plan

> Status: in-flight
> Dependency: PR #161 merged in `origin/modularize-v1.34`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the cinematic Cockpit direction into a real passive/operator console by composing the existing Rytm 12-pad, Style Crates/Queue/Journal, safety, command-queue, snapshot-history, and post-#161 Analog Four set-plan contracts into one GUI-ready performance packet.

**Architecture:** This is a post-#161 bundle and must start from the branch state after `feat: bridge A4 set plan into live flow` has merged. The backend adds one passive report/model module under `rytm_randomizer/reports/` that aggregates existing report builders instead of duplicating facts. The frontend consumes that contract in the existing Cockpit surface and keeps all active hardware actions blocked unless a separate armed/send path already exists.

**Tech Stack:** Python 3.11, frozen dataclasses/TypedDict-style payloads, existing passive report formatter patterns, existing CLI registry, React/TypeScript Cockpit components, Vitest, pytest, ruff, black, isort.

---

## Source Inputs

- Visual target: `docs/assets/rytmrandomizer-cockpit-cinematic-ui-reference-2026-06-09.png`
- Dependency: PR #161 must merge first because this plan consumes the `analog_four_set_plan` bridge.
- Existing backend sources:
  - `rytm_randomizer/reports/live_gui_performance_flow_model.py`
  - `rytm_randomizer/reports/oxi_live_macro_catalog.py`
  - `rytm_randomizer/reports/style_crate_rehearsal_deck.py`
  - `rytm_randomizer/reports/live_gui_12_pad_surface_model.py`
  - `rytm_randomizer/reports/live_gui_snapshot_history_model.py`
  - `rytm_randomizer/reports/live_gui_command_queue_model.py`
  - `rytm_randomizer/reports/live_gui_safety_checklist_model.py`
  - `rytm_randomizer/reports/live_gui_device_inventory_model.py`
- Existing frontend sources:
  - `desktop/web/src/cockpit/Cockpit.tsx`
  - `desktop/web/src/cockpit/DeviceRail.tsx`
  - `desktop/web/src/cockpit/LiveReadinessPanel.tsx`
  - `desktop/web/src/cockpit/StyleCrateQueue.tsx`
  - `desktop/web/src/cockpit/SnapshotPanel.tsx`
  - `desktop/web/src/cockpit/HistoryStrip.tsx`
  - `desktop/web/src/cockpit/ActionBar.tsx`
  - `desktop/web/src/types/live_gui_protocol.ts`

## Scope

This bundle is passive/mock-first.

In scope:

- one GUI-ready performance-console backend packet;
- one passive CLI report command for text/JSON review;
- TypeScript protocol alignment with the Python packet;
- Cockpit layout wiring that moves toward the cinematic reference;
- tests proving SEND/arm/hardware actions remain blocked.

Out of scope:

- opening MIDI ports;
- sending MIDI;
- launching the GUI sidecar from tests;
- A4 outbound macro send;
- profile-wizard audio analysis;
- persistent journal writes;
- real-time queue dispatch.

## File Structure

- Create `rytm_randomizer/reports/live_gui_performance_console_model.py`
  - Owns the top-level passive console packet.
  - Composes existing reports; does not duplicate crate/macro/A4 facts.
  - Registers `live-gui-performance-console-report`.
- Keep `rytm_randomizer/reports/__init__.py` unchanged
  - The reports package deliberately avoids eager imports; the new command is lazy-loaded through `cli.py` instead.
- Modify `rytm_randomizer/cli.py`
  - Add one lazy CLI registry entry for `live-gui-performance-console-report`.
- Modify `rytm_randomizer/help_text.py`
  - Add passive safety help for the new command.
- Create `tests/test_live_gui_performance_console_model.py`
  - Covers composition, determinism, blocked active actions, and CLI behavior.
- Modify `desktop/web/src/types/live_gui_protocol.ts`
  - Add `LiveGuiPerformanceConsoleModelDict` and nested aliases.
- Create `desktop/web/src/cockpit/PerformanceConsole.tsx`
  - Renders the composed console packet with existing components where possible.
- Keep `desktop/web/src/cockpit/Cockpit.tsx` unchanged for this bundle
  - No runtime state source currently supplies the composed console packet, so this PR exports the tested component for the future Tauri/state wiring step.
- Create `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`
  - Covers 12 pads, A4 set plan, style queue, safety rail, blocked actions, and snapshot history.
- Modify `README.md`
  - Document the passive console report and its hardware boundaries.
- Modify `docs/STATUS.md`
  - Add a dated shipped/proposed entry when the implementation lands.

## Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`, the implementation PR must satisfy all 18 gates.

- [x] Gate 1 - touched backend files get 100% branch coverage.
- [x] Gate 2 - no V1.34 parity fixture regeneration.
- [x] Gate 3 - ruff, black `--target-version=py311`, and isort pass.
- [x] Gate 4 - no dead code; run vulture on touched backend files.
- [x] Gate 5 - README and STATUS update in the same PR.
- [x] Gate 6 - frozen dataclasses/TypedDict-style payloads; no `Any` escape hatch.
- [x] Gate 7 - passive report only; no new hot hardware path.
- [x] Gate 8 - tests mirror source and use existing fixtures.
- [x] Gate 9 - new backend code stays inside `reports/`.
- [x] Gate 10 - no new mode/intensity string-dispatch arm.
- [x] Gate 11 - no duplicated test fixture bodies.
- [x] Gate 12 - module constants annotated with `Final`.
- [x] Gate 13 - no new environment variables.
- [x] Gate 14 - maintainability review included below.
- [x] Gate 15 - no new reusable skill expected; document any lesson if one appears.
- [x] Gate 16 - one post-#161 PR, not stacked.
- [x] Gate 17 - aggregate existing report builders; do not reimplement them.
- [x] Gate 18 - update architecture docs only if the CLI/report command count changes require it.

## Maintainability Audit

- Onboarding curve: the new report should be discoverable beside the existing live GUI reports and named in README.
- Naming hygiene: use `live_gui_performance_console_model` because the output is a full console packet, not another A4 or Rytm-only report.
- Coupling: Python report composes existing report builders; React component consumes protocol data only.
- Magic strings: command name is one `Final[str]`; status/action labels come from existing payloads.
- Configuration: no env vars or runtime config.
- Test maintainability: backend has one focused test file; frontend has one focused component test.
- Dev loop friction: focused Python and Vitest tests can run without hardware.
- Error messages: CLI rejects unsupported args with the command name in the error.
- Versioning: no version bump.
- Future-proofing: future real SEND can hang off existing blocked-action fields without changing the display contract.

## Task 1: Backend Console Contract Tests

**Files:**
- Create: `tests/test_live_gui_performance_console_model.py`

- [x] **Step 1: Write the failing composition test**

Add:

```python
from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_performance_console_composes_existing_operator_packets() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
        format_live_gui_performance_console_model,
    )

    model = build_live_gui_performance_console_model()
    text = "\n".join(format_live_gui_performance_console_model(model))

    assert model["console_version"] == "live-gui-performance-console-v1"
    assert model["hardware_mode"] == "passive"
    assert len(model["rytm_pad_surface"]["pads"]) == 12
    assert model["performance_flow"]["analog_four_set_plan"]["set_name"]
    assert model["style_queue"]["queue_cards"]
    assert model["snapshot_history"]["entries"]
    assert model["command_queue"]["queued_commands"]
    assert "send to hardware" in model["blocked_active_actions"]
    assert "A4 outbound macro send" in model["blocked_active_actions"]
    assert "RytmRandomizer live GUI performance console" in text
    assert "Hardware: passive/mock-safe" in text
```

- [x] **Step 2: Write the failing deterministic JSON test**

Add:

```python
def test_performance_console_json_payload_is_deterministic() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_payload,
    )

    first = build_live_gui_performance_console_payload()
    second = build_live_gui_performance_console_payload()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["live_gui_performance_console"]["console_version"] == (
        "live-gui-performance-console-v1"
    )
```

- [x] **Step 3: Run and verify red**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.live_gui_performance_console_model'`.

## Task 2: Backend Console Model

**Files:**
- Create: `rytm_randomizer/reports/live_gui_performance_console_model.py`
- Modify: `rytm_randomizer/reports/__init__.py`

- [x] **Step 1: Implement the passive model module**

Create `rytm_randomizer/reports/live_gui_performance_console_model.py` with:

```python
from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from typing import Final, TypedDict

from ..cli_registry import CliCommand, register
from .live_gui_12_pad_surface_model import build_live_gui_12_pad_surface_model
from .live_gui_command_queue_model import build_live_gui_command_queue_model
from .live_gui_device_inventory_model import build_live_gui_device_inventory_model
from .live_gui_performance_flow_model import build_live_gui_performance_flow_model
from .live_gui_safety_checklist_model import build_live_gui_safety_checklist_model
from .live_gui_snapshot_history_model import build_live_gui_snapshot_history_model
from .style_crate_rehearsal_deck import build_style_crate_rehearsal_deck_report

REPORT_TITLE: Final[str] = "RytmRandomizer live GUI performance console"
CONSOLE_VERSION: Final[str] = "live-gui-performance-console-v1"


class LiveGuiPerformanceConsoleModelDict(TypedDict):
    console_version: str
    title: str
    hardware_mode: str
    device_inventory: object
    rytm_pad_surface: object
    performance_flow: object
    style_queue: object
    snapshot_history: object
    command_queue: object
    safety_checklist: object
    blocked_active_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _style_queue_payload() -> object:
    deck = build_style_crate_rehearsal_deck_report()
    return {
        "deck_version": deck.deck_version,
        "queue_cards": tuple(card.to_dict() for card in deck.queue_cards),
        "crate_cards": tuple(card.to_dict() for card in deck.crate_cards),
        "journal_cards": tuple(card.to_dict() for card in deck.journal_cards),
    }


def build_live_gui_performance_console_model() -> LiveGuiPerformanceConsoleModelDict:
    return {
        "console_version": CONSOLE_VERSION,
        "title": REPORT_TITLE,
        "hardware_mode": "passive",
        "device_inventory": build_live_gui_device_inventory_model(),
        "rytm_pad_surface": build_live_gui_12_pad_surface_model(),
        "performance_flow": build_live_gui_performance_flow_model(),
        "style_queue": _style_queue_payload(),
        "snapshot_history": build_live_gui_snapshot_history_model(),
        "command_queue": build_live_gui_command_queue_model(),
        "safety_checklist": build_live_gui_safety_checklist_model(),
        "blocked_active_actions": (
            "send to hardware",
            "open MIDI output",
            "A4 outbound macro send",
            "dispatch style queue",
        ),
        "replay_commands": (
            "python -m rytm_randomizer.cli live-gui-performance-console-report",
            "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
        ),
    }


def build_live_gui_performance_console_payload() -> dict[str, object]:
    return {"live_gui_performance_console": build_live_gui_performance_console_model()}


def format_live_gui_performance_console_model(
    model: LiveGuiPerformanceConsoleModelDict,
) -> tuple[str, ...]:
    return (
        str(model["title"]),
        "Hardware: passive/mock-safe",
        f"Console version: {model['console_version']}",
        "Blocked active actions: " + ", ".join(model["blocked_active_actions"]),
        "Replay:",
        *("  " + command for command in model["replay_commands"]),
    )


def _parse_args(args: Sequence[str]) -> dict[str, object]:
    if not args:
        return {"json": False}
    if tuple(args) == ("--json",):
        return {"json": True}
    raise ValueError("live-gui-performance-console-report accepts only optional --json")


def _handle_report(*, json_output: bool = False) -> int:
    if json_output:
        sys.stdout.write(json.dumps(build_live_gui_performance_console_payload(), sort_keys=True))
        sys.stdout.write("\n")
        return 0
    model = build_live_gui_performance_console_model()
    sys.stdout.write("\n".join(format_live_gui_performance_console_model(model)))
    sys.stdout.write("\n")
    return 0


LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="live-gui-performance-console-report",
    summary="Print the passive Cockpit performance console packet.",
    args_parser=_parse_args,
    handler=lambda *, json=False: _handle_report(json_output=json),
)

register(LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND)
```

If existing report builders expose `to_dict()` names that differ from the snippet above, adjust the adapter functions to their actual public JSON helpers and add assertions that the same builder remains the source of truth.

- [x] **Step 2: Keep the model helpers lazily imported**

No eager `rytm_randomizer/reports/__init__.py` re-export was added. The reports package documents that heavy or behavior-specific dependencies stay lazy, so the console command is registered through the existing lazy CLI entry instead.

- [x] **Step 3: Run tests**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py -n 0
```

Expected: tests progress from import failure to any real contract mismatch.

## Task 3: CLI And Help Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_live_gui_performance_console_model.py`

- [x] **Step 1: Add CLI tests**

Add:

```python
def test_performance_console_cli_supports_text_and_json(capsys) -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND,
    )

    LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND.invoke(())
    text = capsys.readouterr().out
    assert "RytmRandomizer live GUI performance console" in text

    LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND.invoke(("--json",))
    payload = json.loads(capsys.readouterr().out)
    assert payload["live_gui_performance_console"]["hardware_mode"] == "passive"

    with pytest.raises(ValueError, match="live-gui-performance-console-report"):
        LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND.invoke(("--arm",))
```

- [x] **Step 2: Add lazy CLI entry**

In `rytm_randomizer/cli.py`, add:

```python
"live-gui-performance-console-report": (
    "rytm_randomizer.reports.live_gui_performance_console_model",
    "LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND",
),
```

- [x] **Step 3: Add help text**

In `rytm_randomizer/help_text.py`, add command help that includes:

```text
Prints the passive Cockpit performance console packet for the mock-safe GUI.
Composes Rytm pad state, style queue, snapshot history, command queue, safety
state, and A4 set-plan review. Opens no MIDI ports and sends no MIDI.
```

- [x] **Step 4: Run CLI/help tests**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py tests\test_real_midi_passive_cli_safety.py -k "performance_console or live-gui-performance-console or passive" -n 0
```

Expected: CLI tests pass and passive safety remains intact.

## Task 4: Frontend Protocol And Component

**Files:**
- Modify: `desktop/web/src/types/live_gui_protocol.ts`
- Create: `desktop/web/src/cockpit/PerformanceConsole.tsx`
- Modify: `desktop/web/src/cockpit/Cockpit.tsx`
- Create: `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`

- [x] **Step 1: Add frontend test**

Create `desktop/web/tests/cockpit/PerformanceConsole.test.tsx`:

```tsx
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PerformanceConsole } from '../../src/cockpit/PerformanceConsole';
import type { LiveGuiPerformanceConsoleModelDict } from '../../src/types/live_gui_protocol';

const model = {
  console_version: 'live-gui-performance-console-v1',
  title: 'RytmRandomizer live GUI performance console',
  hardware_mode: 'passive',
  device_inventory: { devices: [{ device_label: 'Analog Rytm MKII' }, { device_label: 'Analog Four MKII' }] },
  rytm_pad_surface: { pads: Array.from({ length: 12 }, (_, index) => ({ pad: index + 1, label: `Pad ${index + 1}` })) },
  performance_flow: { analog_four_set_plan: { set_name: 'Industrial arc', current_macro: 'pressure', up_next_macros: ['space'], replay_command: 'python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json', blocked_active_actions: ['A4 outbound macro send'] } },
  style_queue: { queue_cards: [{ queue_key: 'queue-dark', move_name: 'Dark Hypnotic', risk_status: 'safe' }] },
  snapshot_history: { entries: [{ key: 'base', label: 'Base' }, { key: 'snap-01', label: 'snap-01' }] },
  command_queue: { queued_commands: [{ order: 1, label: 'Dry-run send', status: 'waiting' }] },
  safety_checklist: { checks: [{ label: 'No MIDI Port Open', status: 'ok' }] },
  blocked_active_actions: ['send to hardware', 'A4 outbound macro send'],
  replay_commands: ['python -m rytm_randomizer.cli live-gui-performance-console-report --json'],
} satisfies LiveGuiPerformanceConsoleModelDict;

describe('PerformanceConsole', () => {
  it('renders the passive live console without enabling hardware actions', () => {
    render(<PerformanceConsole model={model} />);

    expect(screen.getByText('RytmRandomizer live GUI performance console')).toBeInTheDocument();
    expect(screen.getByText('Analog Rytm MKII')).toBeInTheDocument();
    expect(screen.getByText('Analog Four MKII')).toBeInTheDocument();
    expect(screen.getAllByTestId(/console-pad-/)).toHaveLength(12);
    expect(screen.getByText('Dark Hypnotic')).toBeInTheDocument();
    expect(screen.getByText('Industrial arc')).toBeInTheDocument();

    const blocked = screen.getByTestId('console-blocked-actions');
    expect(within(blocked).getByText('send to hardware')).toBeInTheDocument();
    expect(within(blocked).getByText('A4 outbound macro send')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /send to hardware/i })).not.toBeInTheDocument();
  });
});
```

- [x] **Step 2: Add protocol type**

In `desktop/web/src/types/live_gui_protocol.ts`, add:

```ts
export interface LiveGuiPerformanceConsoleModelDict {
  readonly console_version: string;
  readonly title: string;
  readonly hardware_mode: string;
  readonly device_inventory: unknown;
  readonly rytm_pad_surface: { readonly pads: ReadonlyArray<{ readonly pad: number; readonly label: string }> };
  readonly performance_flow: { readonly analog_four_set_plan?: unknown };
  readonly style_queue: { readonly queue_cards: ReadonlyArray<{ readonly queue_key: string; readonly move_name: string; readonly risk_status: string }> };
  readonly snapshot_history: { readonly entries: ReadonlyArray<{ readonly key: string; readonly label: string }> };
  readonly command_queue: { readonly queued_commands: ReadonlyArray<{ readonly order: number; readonly label: string; readonly status: string }> };
  readonly safety_checklist: { readonly checks: ReadonlyArray<{ readonly label: string; readonly status: string }> };
  readonly blocked_active_actions: ReadonlyArray<string>;
  readonly replay_commands: ReadonlyArray<string>;
}
```

If the existing TypeScript file already has narrower exported interfaces for any nested model, use those instead of `unknown`.

- [x] **Step 3: Implement component**

Create `desktop/web/src/cockpit/PerformanceConsole.tsx` with:

```tsx
import type { LiveGuiPerformanceConsoleModelDict } from '../types/live_gui_protocol';

interface PerformanceConsoleProps {
  readonly model: LiveGuiPerformanceConsoleModelDict;
}

export function PerformanceConsole({ model }: PerformanceConsoleProps) {
  const a4Plan = model.performance_flow.analog_four_set_plan as
    | { set_name?: string; current_macro?: string; up_next_macros?: readonly string[]; blocked_active_actions?: readonly string[] }
    | undefined;

  return (
    <main className="performance-console" data-testid="performance-console">
      <header className="performance-console__header">
        <h1>{model.title}</h1>
        <span>{model.hardware_mode === 'passive' ? 'SAFE - No Hardware Port Open' : model.hardware_mode}</span>
      </header>
      <section aria-label="Rytm pads" className="performance-console__pads">
        {model.rytm_pad_surface.pads.map((pad) => (
          <article data-testid={`console-pad-${pad.pad}`} key={pad.pad}>
            <strong>{pad.pad}</strong>
            <span>{pad.label}</span>
          </article>
        ))}
      </section>
      <aside aria-label="Style queue">
        {model.style_queue.queue_cards.map((card) => (
          <article key={card.queue_key}>
            <h2>{card.move_name}</h2>
            <span>{card.risk_status}</span>
          </article>
        ))}
      </aside>
      <section aria-label="Analog Four set plan">
        <h2>{a4Plan?.set_name ?? 'A4 set plan unavailable'}</h2>
        <p>{a4Plan?.current_macro ?? 'review only'}</p>
        {(a4Plan?.up_next_macros ?? []).map((macro) => (
          <span key={macro}>{macro}</span>
        ))}
      </section>
      <section data-testid="console-blocked-actions" aria-label="Blocked active actions">
        {model.blocked_active_actions.map((action) => (
          <span key={action}>{action}</span>
        ))}
      </section>
    </main>
  );
}
```

- [x] **Step 4: Export component and leave Cockpit fallback unchanged**

`desktop/web/src/cockpit/Cockpit.tsx` remains unchanged because no runtime state source exists yet for the composed console packet. The new `PerformanceConsole` component and protocol type are exported for the future wiring step.

- [x] **Step 5: Run frontend tests and typecheck**

Run:

```powershell
Push-Location desktop\web
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
Pop-Location
```

Expected: test and typecheck pass.

## Task 5: Docs And Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Add README command note**

Near the passive report command list, add:

```markdown
python -m rytm_randomizer.cli live-gui-performance-console-report --json
```

Then add:

```markdown
The live GUI performance console report composes the Rytm 12-pad snapshot
surface, Style Crates queue, Mutation Journal snapshot history, command queue,
safety checklist, and Analog Four set-plan review into one Cockpit packet.
It is passive/mock-safe: it opens no MIDI port, sends no MIDI, and keeps
hardware sends and A4 outbound macro sends represented as blocked actions.
```

- [x] **Step 2: Add STATUS entry only when implementation ships**

At the top of `docs/STATUS.md`, add:

```markdown
- 2026-06-12: Cockpit performance console bundle prepared after PR #161. The
  passive console report composes Rytm 12-pad state, Style Crates/Queue/Journal,
  snapshot history, command queue, safety checklist, and A4 set-plan review into
  one GUI-ready packet. It remains passive/mock-safe and keeps hardware sends,
  queue dispatch, and A4 outbound macro send blocked.
```

- [x] **Step 3: Run docs checks**

Run:

```powershell
python -m pytest tests\architecture\test_readme_freshness.py tests\architecture\test_plan_doc_status_truth.py tests\architecture\test_plan_requirements_referenced.py -q -n 0
```

Expected: docs checks pass.

## Task 6: Verification And PR

**Files:**
- All files touched above.

- [x] **Step 1: Run focused backend tests**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py -n 0
```

Expected: all tests pass.

- [x] **Step 2: Run frontend test/typecheck**

Run:

```powershell
Push-Location desktop\web
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
Pop-Location
```

Expected: Vitest and typecheck pass.

- [x] **Step 3: Run architecture and lint gates**

Run:

```powershell
python -m pytest tests\architecture\ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all pass.

- [x] **Step 4: Run full test suite**

Run:

```powershell
python -m pytest
```

Expected: full suite passes.

- [x] **Step 5: Run touched-file coverage and vulture**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov-branch --cov-fail-under=100 --cov-report=term-missing -n 0
python -m vulture rytm_randomizer\reports\live_gui_performance_console_model.py tests\test_live_gui_performance_console_model.py --min-confidence 80
```

Expected: 100% branch coverage and no vulture findings.

- [ ] **Step 6: Open one PR after #161 merges**

Run:

```powershell
git push -u origin codex/post-161-cockpit-performance-console
python scripts/create_pr.py --title "feat: add Cockpit performance console packet" --body-file docs\superpowers\plans\2026-06-12-cockpit-performance-console-pr-body.md
```

Expected: one PR against `modularize-v1.34`; no stacked base.

## Self-Review

- Spec coverage: the plan covers the cinematic console direction, 12-pad Rytm visibility, A4 set-plan review, queue/journal/history surfaces, safety/blocked actions, docs, and verification.
- Placeholder scan: no unresolved blanks; code snippets identify exact imports, commands, and expected outputs.
- Type consistency: Python builder returns `LiveGuiPerformanceConsoleModelDict`; TypeScript mirrors `LiveGuiPerformanceConsoleModelDict`.
- Abstraction reuse: existing report builders remain the data sources; the new module is an aggregation layer only.
- Safety: no command opens ports, sends MIDI, launches sidecars, dispatches queues, or promotes A4 outbound macro sending.
