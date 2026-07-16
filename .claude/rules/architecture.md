# Architecture rules (agent-facing distillation)

> Short, enforceable summary of `docs/ARCHITECTURE.md`. If you are an agent
> editing this repo, follow these rules. Violations are caught by
> `tests/architecture/`.

## Layer order (lowest -> highest)

```
data/    state/             <-- leaves, stdlib only
midi_io  randomization  mock_midi  real_midi_adapter
engines/pad{1..4}
group_runner  scene_runner
shell.py
app.py                              <-- top, imports everything
cli.py                              <-- PASSIVE; sibling of app; NO mido, NO engines
mido_provider.py                    <-- only constructed by app under --arm
```

`reports.py` + `inspection.py` are passive read-only formatters; treat them as
a side-branch off `data/` consumed by `cli.py` and the shell.

## Direction rules (mechanically enforced)

1. `data/*` imports nothing from `rytm_randomizer` (only stdlib + sibling
   data modules).
2. `state/*` imports only stdlib. No `engines`, no runners, no `mido`.
3. `engines/*` may import `data`, `state`, `midi_io`, `randomization`,
   `mock_midi`. NOT `cli`, `shell`, `app`, `scene_runner`, `group_runner`,
   `mido_provider`.
4. `scene_runner` and `group_runner` may import engines + state + data +
   `midi_io` + `randomization`. NOT `cli`, `shell`, `app`.
5. `shell.py` may import everything below it. NOT `app`, NOT `cli`.
6. `app.py` may import anything; nothing imports `app`.
7. `cli.py` is **passive**. It may import `reports`, `inspection`, `data`,
   `validation`, metadata lookups, and `mock_midi`. It MUST NOT import
   `mido`, `mido_provider`, `real_midi_adapter`, any `engines/*`, `shell`,
   `app`, `scene_runner`, `group_runner`, `midi_io`, or `randomization`.
8. The retired V1.34 monolith stays buried. No package module -- and no test
   helper -- may import `rytm_hybrid_randomizer_v134`. The V1.34 reference
   behavior is now the JSON goldens under `tests/fixtures/v134_parity/`.
9. No `import mido` / `from mido` at module top level anywhere in the
   package. `mido` must be lazy, inside the methods that need it.
10. `app.py --arm` is the sole real input/output boundary. Standalone tools,
    including RUSH01 compile and observation-report tools, must not construct
    `MidoMidiPortProvider`, discover or open ports, or transmit MIDI.

## House style (mechanically enforced)

* Frozen dataclasses for everything in `state/` and for DTOs.
* Full type annotations on every public (non-underscore) signature.
* `typing.Protocol` for cross-layer boundaries (real-MIDI provider, sender).
* No module-level mutable globals in the package. Only `Final` / constants /
  `MappingProxyType` / frozen instances / immutable tuples-or-frozensets /
  callables.
* No I/O at import time: no stdout, no port opens, no `input()`, no
  `mido`/`rtmidi` pulled into `sys.modules` by importing the package.
* Data, not code. Fact tables live under `data/` once. No other module
  re-types them; wrappers re-export from `data/`.

## Parity discipline

* The V1.34 reference behavior lives as JSON goldens under
  `tests/fixtures/v134_parity/`. Do not regenerate them casually; running
  with `PARITY_CAPTURE_MODE=1` rewrites every golden from the current engine
  output, which is only appropriate when an intentional reference-output
  change is being committed.
* No new MIDI CCs, profiles, pads (5-12), parameter ranges, or command
  behaviors without explicit approval. See `CONTRIBUTING.md` and
  `docs/ARCHITECTURE.md` section 5.

## Hard "do not" list for agents

* Do not put `import mido` at the top of any package file.
* Do not give `cli.py` runtime behavior (no engines, no sends, no `--arm`).
* Do not create an independently armed top-level tool; route active input or
  output through a guarded `app.py --arm` operation.
* Do not redefine a name that already exists in `data/`.
* Do not introduce a mutable module-level dict / list / set in the package.
* Do not let a lower-layer module import from a higher layer.
* Do not resurrect `rytm_hybrid_randomizer_v134.py`. The monolith was
  retired; the JSON goldens under `tests/fixtures/v134_parity/` are the
  reference now.

## Before merging architectural changes

Run `pytest tests/architecture/ -q`. Then run the full suite.
If `tests/architecture/` is red, the merge is blocked at CI.

See also `.claude/rules/skill-routing.md` for which skill to invoke for which
change type, and `docs/ARCHITECTURE.md` for the full diagram.
