# RytmRandomizer Architecture

> Canonical, human-readable architecture standard for the modular
> RytmRandomizer package. **Authoritative**. The machine-enforced version lives
> in `tests/architecture/`; the agent-facing distillation is in
> `.claude/rules/architecture.md`. If any of those documents disagrees with
> this one, this one wins and the others get updated.

This document is the result of Waves 1-4 of the modularization (the V1.34
monolith decomposition). It describes the FINAL shape of the codebase and the
rules that future work must respect so the architecture cannot be eroded.

---

## 1. Module layer diagram

```mermaid
flowchart TD
    app["app.py - entry point<br/>(--arm flag, top of stack)"]
    cli["cli.py - passive report CLI<br/>(no mido, no engines, no runtime)"]
    shell["shell.py - interactive command loop"]
    sceneRunner["scene_runner.py"]
    groupRunner["group_runner.py"]
    engines["engines/pad{1,2,3,4}.py"]
    reports["reports.py + inspection.py<br/>(passive read-only formatters)"]
    midi["midi_io.py + randomization.py"]
    realAdapter["real_midi_adapter.py - Protocol boundary"]
    midoProvider["mido_provider.py - lazy mido provider"]
    mockMidi["mock_midi.py"]
    state["state/* - frozen per-domain state"]
    data["data/* - shared fact tables"]
    parityGoldens["tests/fixtures/v134_parity/*.json<br/>(frozen V1.34 reference, tests only)"]

    app --> shell
    app --> cli
    app --> midoProvider
    app --> realAdapter

    shell --> sceneRunner
    shell --> groupRunner
    shell --> engines
    shell --> midi
    shell --> data
    shell --> reports

    sceneRunner --> groupRunner
    sceneRunner --> data

    groupRunner --> midi
    groupRunner --> data
    groupRunner --> state

    engines --> midi
    engines --> data
    engines --> state

    midi --> data
    midi --> mockMidi
    realAdapter --> mockMidi

    midoProvider --> realAdapter

    cli --> reports
    cli --> data

    reports --> data

    state -.- |stdlib only| state
    data -.- |stdlib only| data

    parityGoldens -. parity tests only .-> parityGoldens

    style data fill:#eef,stroke:#447
    style state fill:#eef,stroke:#447
    style parityGoldens fill:#fee,stroke:#a44,stroke-dasharray: 5 5
    style app fill:#efe,stroke:#474
    style cli fill:#ffe,stroke:#774
    style midoProvider fill:#fef,stroke:#747
```

Arrows point in the **allowed import direction**. There are no cycles. Lower
layers know nothing about higher layers.

---

## 2. Module-responsibility map

One line per module. If you are about to add a responsibility that doesn't fit
on one line for an existing module, you probably need a new module instead.

### Bottom (leaves)

| Module                | Responsibility                                                                  |
| --------------------- | ------------------------------------------------------------------------------- |
| `data/param_maps.py`  | Per-machine CC maps, anchors, safe ranges, deltas, zones. Pure data.            |
| `data/profiles.py`    | The `PROFILES` discovery registry. Composed from `param_maps`.                  |
| `data/scenes.py`      | The 14 V1.34 `SCENE_PRESETS`. Pure data.                                        |
| `data/plans.py`       | Group layout, intensity plans, page plans, per-pad mode rotations. Pure data.  |
| `state/anchor.py`     | Frozen single-pad anchor/current/previous runtime state + transitions.          |
| `state/group.py`      | Frozen group / active-pad / four-pad anchor state + transitions.                |
| `state/pad_mode.py`   | Frozen per-pad mode-rotation index state + transitions.                         |
| `state/scene.py`      | Frozen current-scene-name state + transitions.                                  |
| `state/selection.py`  | Frozen target-pad / channel / isolated-pad selection state + transitions.       |

### Middle (runtime core)

| Module                       | Responsibility                                                              |
| ---------------------------- | --------------------------------------------------------------------------- |
| `midi_io.py`                 | Leaf MIDI primitives: build CC, send param, apply state. `mido` is lazy.    |
| `randomization.py`           | Pure randomization core: zone/depth mutation, waveform pick.                |
| `mock_midi.py`               | In-memory `MockMidiSender` and `MidiMessage` for tests + passive paths.     |
| `real_midi_adapter.py`       | Protocol boundary: `RealMidiPortProvider`, `RealMidiSender`. NO `mido`.     |
| `mido_provider.py`           | Concrete `mido`-backed provider. `mido` imported lazily INSIDE methods.     |
| `engines/pad1..4.py`         | Per-pad interactive engines. Dependencies injected, no module globals.      |

### Mid-upper (orchestration)

| Module                | Responsibility                                                                  |
| --------------------- | ------------------------------------------------------------------------------- |
| `group_runner.py`     | Four-pad group + isolated-pad orchestration. Drives `randomization` + `midi_io`.|
| `scene_runner.py`     | Scene/preset thin layer on top of `group_runner`.                               |

### Upper (entry points)

| Module                | Responsibility                                                                  |
| --------------------- | ------------------------------------------------------------------------------- |
| `shell.py`            | Interactive command loop. Owns the V1.34 command alphabet. Injected deps.       |
| `cli.py`              | **Passive** report-only CLI. NEVER imports `mido`, `mido_provider`, or engines. |
| `app.py`              | Top-of-stack entry point. `--arm` wires the `mido_provider` into `shell`.       |
| `reports.py`          | Consolidated passive in-memory report dispatcher.                               |
| `inspection.py`       | Consolidated passive command-metadata inspection + preview + audit.             |

### Frozen reference (NOT in the layered graph)

| File                                  | Responsibility                                                       |
| ------------------------------------- | -------------------------------------------------------------------- |
| `tests/fixtures/v134_parity/*.json`   | Frozen V1.34 reference behavior, one golden per parity request. Used ONLY by parity tests via `tests/_parity_worker.py`. (The original `rytm_hybrid_randomizer_v134.py` monolith was retired in 2026-05-17.) |

The remaining files (`commands.py`, `profile_lookup.py`, `help_text.py`,
`validation.py`, `audit.py`, `preview.py`, `registry.py`, etc.) are passive,
in-memory, no-I/O metadata helpers that follow the same direction rules: they
may read from `data/` and `state/` but they may not import `engines`, `shell`,
`app`, or `cli`.

---

## 3. Dependency direction rules (machine-enforced)

These are the rules that `tests/architecture/test_import_direction.py`
verifies. If you change a rule, change it here first, then update the test.

1. **`data/` is a leaf.**
   `data/*` may import only Python stdlib and other `data/*` modules.
   It MUST NOT import anything else from `rytm_randomizer`.

2. **`state/` is a leaf.**
   `state/*` may import only Python stdlib. It MUST NOT import `engines`,
   `scene_runner`, `group_runner`, `shell`, `app`, `cli`, `midi_io`,
   `randomization`, `mido`, or `mido_provider`.

3. **`engines/` is mid-layer.**
   `engines/*` MAY import `data/`, `state/`, `midi_io`, `randomization`,
   `mock_midi`, and the `real_midi_adapter` Protocol. They MUST NOT import
   `cli`, `shell`, `app`, `scene_runner`, `group_runner`, or `mido_provider`.

4. **`scene_runner` / `group_runner` are orchestration.**
   May import `engines`, `state`, `data`, `midi_io`, `randomization`,
   `mock_midi`. MUST NOT import `cli`, `shell`, or `app`.

5. **`shell.py` may import everything below it BUT NOT `app` or `cli`.**

6. **`app.py` is the top.**
   May import anything. Nothing imports `app`.

7. **`cli.py` is the PASSIVE entry point.**
   It MAY import `reports`, `inspection`, `data`, `validation`, metadata
   lookups, and `mock_midi`. It MUST NOT import `mido`, `mido_provider`,
   `real_midi_adapter`, any `engines/*`, `shell`, `app`, `scene_runner`,
   `group_runner`, `midi_io`, or `randomization`.

8. **The retired V1.34 monolith stays buried.**
   No module inside the `rytm_randomizer` package -- and no test helper --
   may import `rytm_hybrid_randomizer_v134`. The monolith was retired and
   the only authoritative source of V1.34 reference behavior is the JSON
   goldens under `tests/fixtures/v134_parity/`.

9. **`mido` is lazy and behind `--arm`.**
   `mido` must not be imported at module load time anywhere in the package.
   The only legitimate `mido` import sites are inside methods of
   `mido_provider.py` and inside conditional branches of `midi_io.py` that
   fire only when a real sender is constructed. Static `import mido` /
   `from mido` at module top level is forbidden in the package.

---

## 4. House-style rules (machine-enforced)

These are verified by `tests/architecture/test_house_style.py` and
`tests/architecture/test_no_side_effects.py`.

* **Frozen dataclasses.** Every `@dataclass` in `state/` and every DTO in the
  package is `frozen=True`. Mutation happens by returning a new instance, not
  by reassigning a field. The single allow-listed exception is bridge DTOs in
  `mock_runtime_active_bridge.py` and similar reporting shims, which are
  documented explicitly.

* **Type annotations on public signatures.** Every function and method whose
  name does not start with `_` has type annotations on all parameters and a
  return annotation.

* **Protocol for boundaries.** Cross-layer boundaries (real-MIDI providers,
  senders) are defined as `typing.Protocol` interfaces, not abstract base
  classes. Concrete implementations live one layer up.

* **No module-level mutable globals in the package.** A module-level name in
  `rytm_randomizer/*` is one of: a `Final`/constant, a frozen dataclass
  instance, a `MappingProxyType`, an immutable tuple/frozenset, a callable
  (function/class), or appears in an explicit allow-list defined by the
  test.

* **No I/O at import time.** Importing any `rytm_randomizer.*` submodule must
  produce no stdout, must not open any MIDI port, must not call `input()`,
  and must not pull `mido` / `rtmidi` into `sys.modules`. The runtime stack
  is constructed explicitly from `app.py`.

* **Data, not code, for fact tables.** Anything that is "a table of facts"
  (CC numbers, anchors, deltas, zones, scenes, profiles, mutation plans, the
  four-pad layout) lives under `data/` exactly once. No other module is
  allowed to re-type these tables. Wrapper modules (`profiles.py`,
  `scenes.py`, `constants.py`) MUST derive their values from `data/`.

* **Unified logging through `observability/`.** Production log lines should go
  through the `observability/` helpers (placeholder; WS-U owns the build-out).
  Until then, the `print()` calls inside `shell.py` are the historical
  interactive UI surface and are exempt; `print()` outside `shell.py`,
  `cli.py`, and the report formatters is a smell.

---

## 5. Parity discipline (V1.34)

The hardware-validated V1.34 behavior is the baseline of truth. It is frozen
as JSON goldens under `tests/fixtures/v134_parity/`, one per parity request,
and the parity tests run the extracted engines/runners against those goldens.

* Do not regenerate the V1.34 goldens casually. `PARITY_CAPTURE_MODE=1 pytest`
  rewrites them from the current engine output -- only do this when an
  intentional reference-output change is being committed, with reviewer
  sign-off.
* Do not introduce new MIDI CCs, new profiles, new pads (5-12), new parameter
  ranges, or new command behavior without explicit approval. See
  `CONTRIBUTING.md`.
* If you change an engine, scene runner, or group runner, the parity tests
  must still pass byte-for-byte against the monolith.

---

## 6. Where to put new work

| Change type                          | Where it goes                                          | Skill to invoke           |
| ------------------------------------ | ------------------------------------------------------ | ------------------------- |
| Add a new V1.34-equivalent command   | `shell.py` (dispatch) + relevant runner/engine.        | `add-pad-command`         |
| Add new fact table                   | A new module under `data/` + re-export in `__init__`.  | `extend-data-layer`       |
| Change MIDI primitives               | `midi_io.py`. Keep `mido` lazy.                        | (architecture review)     |
| Add new passive report               | `reports.py` (or `inspection.py`) + CLI wire-up.       | (none, follow existing)   |
| Add a new state domain               | A new module under `state/` (frozen + transitions).    | (architecture review)     |
| **Add a new Elektron device family** (Analog Four, Digitakt, ...) | One module at `devices/<family>.py` registering a `Device` instance + three Strategy modules under `devices/strategies/`. See §6.1. | (architecture review)     |
| Music-analysis or guardrail change   | See `.claude/skills/MusicLibraryGuardrails/SKILL.md`. | `MusicLibraryGuardrails`  |

---

## 6.1 Device Protocol + Strategy seam (WS-S5 + Strategy)

The `rytm_randomizer.devices.Device` Protocol is the single cross-machine
boundary. Every Elektron device family — Rytm today, Analog Four next —
exposes exactly one registered `Device` instance and routes its behavior
through three Strategy sub-Protocols.

**Visual reference:** [`docs/ARCHITECTURE_DIAGRAMS.md`](ARCHITECTURE_DIAGRAMS.md) has six mermaid diagrams that illustrate this section in detail — [§3 Device + Strategy Capability Stack](ARCHITECTURE_DIAGRAMS.md#3-device--strategy-capability-stack-ws-s5--strategy) (class diagram), [§4 Snapshot → Plan → Render Lifecycle](ARCHITECTURE_DIAGRAMS.md#4-snapshot--plan--render-lifecycle-one-rytm-cc) (sequence), [§5 Composition vs Stub](ARCHITECTURE_DIAGRAMS.md#5-device--strategy-composition-vs-old-stub-shape) (before/after), [§9 Snapshot Subpackage](ARCHITECTURE_DIAGRAMS.md#9-snapshot-subpackage-ws-s6-envelope--protocols) (WS-S6 helpers), [§18 Future Codex PR Shape](ARCHITECTURE_DIAGRAMS.md#18-future-codex-pr-shape-post-pr-43-dual-machine-redo) (where the next dual-machine work plugs in), and [§19 Registry Fan-Out](ARCHITECTURE_DIAGRAMS.md#19-registry-fan-out-dual-machine-orchestration-via-mappingstr-device).

**Protocol shape:**

| Attribute                   | Type / Protocol                                       | Role |
| --------------------------- | ----------------------------------------------------- | ---- |
| `device_id`                 | `str`                                                 | Stable, lowercase, snake_case registry key (`"analog_rytm_mk2"`) |
| `display_name`              | `str`                                                 | Operator-facing label |
| `default_midi_channel`      | `int`                                                 | 0-based MIDI channel |
| `track_count`               | `int`                                                 | Pads / tracks (4 for A4, 12 for Rytm) |
| `sysex_manufacturer_id`     | `bytes`                                               | 3-byte Elektron ID (`0x00 0x20 0x3C`) |
| `snapshot_decoder`          | `snapshot.SnapshotDecoder` Protocol                   | `decode(raw, slot)` → device-specific snapshot |
| `mutation_planner`          | `snapshot.MutationPlanner` Protocol                   | `plan(snapshot, depth)` → device-specific plan |
| `message_renderer`          | `devices.MessageRenderer` Protocol                    | `to_mock_message(event, plan)` + `to_cc_triple(event, plan)` |
| `report_header`             | `str`                                                 | Header line for guarded / hardware send reports |

The Protocol's four legacy convenience methods (`decode_snapshot`,
`plan_mutation`, `to_mock_messages`, `to_cc_messages`) remain for
backward compatibility — they delegate to the strategies.

**To add a device family:**

1. Create three strategy modules under `rytm_randomizer/devices/strategies/`:
   - `<family>_snapshot_decoder.py` — implements `SnapshotDecoder.decode`. Use the shared `snapshot/envelope.py` helpers; do NOT fork them per family.
   - `<family>_mutation_planner.py` — implements `MutationPlanner.plan`. The plan must carry `ready: bool` and `readiness_reason: str` so the generic guarded sender can refuse on an unfinished plan without device-specific introspection.
   - `<family>_message_renderer.py` — implements `MessageRenderer.{to_mock_message, to_cc_triple}`. Looks up CC numbers through `data/profiles.py` (or the family's own param map).
2. Create one device class at `rytm_randomizer/devices/<family>.py` that composes the three strategies in `__init__` and exposes the 9 Protocol attributes.
3. Register at import time: `registry.register_device(<Family>Device())`.
4. The `devices/__init__.py` must import the new module so the side-effect registration runs.

**What NOT to do:**

- Do NOT create a parallel `<family>/` subpackage at the package root with its own decoder / planner / renderer / sender — the architecture tests will reject it (see §7).
- Do NOT import private symbols (`_foo`, `_BAR`) from a sibling family's strategy module — same enforcement.
- Do NOT introduce a second registry; only `devices/registry.py` may define `register_device`.

`AnalogRytmDevice` is the reference implementation; `tests/test_devices.py` and `tests/test_devices_strategies_*.py` cover the contract.

---

## 7. Enforcement summary

The rules above are mechanically enforced by:

* `tests/architecture/test_import_direction.py` (rules 1-9)
* `tests/architecture/test_no_side_effects.py` (no I/O at import, no `mido`)
* `tests/architecture/test_house_style.py` (frozen dataclasses, type hints,
  no module-level mutable globals)
* `tests/architecture/test_layering_structure.py` (the expected module layout
  exists and the retired V1.34 monolith has not been resurrected)
* `tests/architecture/test_data_not_code.py` (fact tables live only in
  `data/`; no module re-defines a `data/` name)
* `tests/architecture/test_device_protocol_enforcement.py` (every Elektron
  device family registers through `devices/registry.py`; no cross-family
  private imports; `dual_machine/` consumes only the registry; only one
  device registry exists; every registered Device satisfies the Protocol;
  Protocol surface is pinned against accidental drift — see §6.1)

These tests are run by `pytest tests/architecture/` and are wired into the
`test` job of `.github/workflows/test.yml` so a violation fails the build.

---

## 8. V1.34 parity API surface

A handful of symbols in the package have no production callers — they exist
only because the parity tests need to assert on them, or because they are
documented public contracts the parity layer gates on, or because they are
the documented persistence lifecycle for the guardrails workstream.

A naive "no production caller -> dead code" audit will keep flagging them.
They are NOT dead. This section is the authoritative keep-list; if you are
running a dead-code audit and you find a symbol below, leave it alone.

Removing any of these requires a parity-layer change (or a guardrails design
change for the `ProfileStore` entries) and is out of scope for an audit-led
cleanup.

### Documented passive metadata + V1.34 parity helpers

| Symbol | Module | Why it stays |
| --- | --- | --- |
| `FORBIDDEN_ACTIONS` | `rytm_randomizer/commands.py` | Documented V1.34 controlled-mutation roadmap surface. `tests/test_scaffold.py` gates that the package never grows an executable path into one of these forbidden action categories. |
| `is_guarded_main_prompt_depth()` | `rytm_randomizer/commands.py` | Documented predicate the parity layer uses to assert that the bare main-prompt depth commands ("1", "2", "3") never send MIDI. Removing it would gut the parity assertion. |
| `DEFAULT_MIDI_CHANNEL`, `OUT_OF_SCOPE_PAD_GUARDRAIL`, `PAD_TO_MIDI_CHANNEL`, `PAD_SELECTION_LABELS` | `rytm_randomizer/constants.py` | The V1.34 channel and Pads-5-12 scope-guardrail constants. The parity layer asserts on these exact values; they are the documented contract between the modular package and the byte-frozen monolith. |
| `switch_pad1_extra_bd_machine_only()` | `rytm_randomizer/engines/pad1.py` | The V1.34 Pad-1 extra-BD machine-only switch routine. `tests/test_engines_pad1.py` byte-parity tests assert on its exact behaviour (including a parity subprocess invocation). |
| `mutate_group_with_depth()` | `rytm_randomizer/group_runner.py` | Mirrors the monolith's `mutate_group_with_depth` legacy fallback. Documented in the module docstring; the parity layer asserts byte-for-byte equality against the monolith. |
| `GroupRuntimeState.loaded` (property) | `rytm_randomizer/state/group.py` | The documented monolith-readiness gate ("all four pads have current state"). Used by parity tests to assert that the group runtime treats partial loads exactly as the monolith did. |
| `RealMidiSender.send_messages()` | `rytm_randomizer/real_midi_adapter.py` | The public outbound boundary of the real-MIDI adapter. `tests/test_real_midi_adapter_boundary.py` is the boundary contract test that asserts it translates and dispatches messages correctly. Removing it gets rid of the only documented "real-MIDI sender knows how to send" API. |
| `evaluate_mock_runtime_active_bridge()` | `rytm_randomizer/mock_runtime_active_bridge.py` | The bridge evaluator. The mock-runtime-active-bridge report (`rytm_randomizer/reports.py:BRIDGE_SUMMARY`) names it as a literal string in the report payload ("evaluator": "evaluate_mock_runtime_active_bridge"), so it must keep its exact public name. The CLI source-level test (`tests/test_cli.py`) also asserts that the symbol does not leak into `cli.py`, which means the symbol has to continue to exist to be checked-for. |

### Documented guardrails persistence lifecycle (WS-W)

| Symbol | Module | Why it stays |
| --- | --- | --- |
| `ProfileStore.save()` | `rytm_randomizer/guardrails/store.py` | The documented persistence write path for guardrail profiles. Part of the WS-W lifecycle (`save -> load -> list_profiles -> promote`). |
| `ProfileStore.list_profiles()` | `rytm_randomizer/guardrails/store.py` | The documented profile enumeration step of the WS-W lifecycle. |
| `ProfileStore.promote()` | `rytm_randomizer/guardrails/store.py` | The documented profile state-machine transition (DRAFT → VALIDATED → STUDIO_TESTED → LIVE_APPROVED → ARCHIVED) of the WS-W lifecycle. Implemented as a classmethod that returns a new immutable profile. |

The WS-W workstream owns these methods. They will gain production callers
once the guardrails CLI / promotion workflow lands; until then they are kept
alive by `tests/test_guardrails_store.py` as the documented lifecycle.
