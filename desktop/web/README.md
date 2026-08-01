# Cockpit Web Frontend

Vite + React 18 + TypeScript 5 frontend for the RytmRandomizer cockpit. Talks to the
Python sidecar over WebSocket (`ws://127.0.0.1:4317/ws` by default; override with
`RYTM_RAND_WS_PORT` on the sidecar side).

The WS-I scaffold grew into the full cockpit surface: the performance console
(`src/cockpit/**`), the schema-driven panel platform (`src/cockpit/panels/**`), the
profile wizard (`src/wizard/**`), and the shared a11y utilities (`src/a11y/**`).

## Layout

```
desktop/web/
├── index.html               # Vite entry
├── package.json
├── tsconfig.json
├── vite.config.ts           # Vite + Vitest config (coverage thresholds live here)
├── playwright.config.ts     # e2e (axe-core accessibility sweeps included)
├── .eslintrc.json
├── README.md
├── src/
│   ├── main.tsx             # React root bootstrap
│   ├── App.tsx              # Hash router: Cockpit by default, #/wizard for the wizard
│   ├── a11y/                # LiveRegion announcer, focus + title hooks, sr-only css
│   ├── ws/
│   │   ├── client.ts        # Typed WebSocket client (Command / Event)
│   │   └── protocol.ts      # TS types one-to-one with Python dataclasses
│   ├── state/
│   │   ├── store.ts         # Zustand store: snapshot / preview / send plan / history / profile / session
│   │   └── index.ts         # bindClientToStore + re-exports
│   ├── cockpit/             # Performance console + cockpit components
│   │   ├── PerformanceConsole.tsx
│   │   ├── panels/          # Schema-driven panel platform (see below)
│   │   └── styles.css       # Documented color tokens (WCAG AA checked in CI)
│   ├── wizard/              # Guardrail-profile wizard
│   └── types/
│       ├── index.ts             # Public type re-exports
│       ├── live_gui_protocol.ts # GENERATED — see below
│       ├── style_crate_rehearsal_deck.ts
│       └── wizard_protocol.ts
├── tests/                   # Vitest + @testing-library/react (jsdom)
│   ├── cockpit/             # incl. panels/ tests + fixtures/performance_console.json (GENERATED)
│   ├── wizard/
│   ├── a11y/
│   └── setup.ts
└── e2e/                     # Playwright specs
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Build | Vite 8 | Fast dev loop, ESM-first, Rollup under the hood |
| UI | React 18 | Ecosystem + concurrent rendering for ghost-overlay perf |
| Lang | TypeScript 5 (strict) | Mirrors the Python dataclass types end-to-end |
| State | Zustand 4 | Tiny, no provider, perfect for "one slice per event" |
| Test | Vitest 4 + jsdom + @testing-library/react | Vite-native, fast |
| e2e | Playwright + @axe-core/playwright | Real-browser + accessibility sweeps |
| Lint | ESLint 8 + @typescript-eslint | Standard |

## Develop

```bash
npm install
npm run dev               # serves on http://127.0.0.1:5173
npm run build             # tsc -b && vite build → dist/
npm run typecheck         # tsc -b --noEmit
npm run lint              # eslint . --max-warnings 0
npm run test              # vitest watch
npm run test:run          # vitest --run (CI)
npm run test:coverage     # vitest --run --coverage (100% — see Coverage policy)
npm run e2e               # playwright test
```

## Generated protocol types

`src/types/live_gui_protocol.ts` and `tests/cockpit/fixtures/performance_console.json`
are **generated artifacts** of `scripts/generate_live_gui_protocol_ts.py` (repo root).
The source of truth is the Python TypedDict contracts in
`rytm_randomizer/reports/live_gui_*_model.py` and
`rytm_randomizer/reports/panel_spec.py`. Regenerate with:

```bash
python scripts/generate_live_gui_protocol_ts.py --fixture
```

`tests/architecture/test_live_gui_protocol_is_generated.py` pins both files
byte-for-byte — hand edits fail CI.

## Schema-driven panels

New cockpit UI elements are data, not bespoke components. A panel is:

1. a `PanelSpecDict` built in Python (`rytm_randomizer/reports/panel_spec.py`;
   `panel_spec_from_report_spec()` bridges an existing `ReportSpec` so one spec
   feeds both the passive text report and the cockpit panel),
2. a pure selector `(console packet) -> PanelSpecDict` in `src/cockpit/panels/`,
3. one entry in `src/cockpit/panels/registry.ts` (`id`, `region`, `selector`,
   `component: PanelRenderer`).

`PanelHost` renders every registered panel for its region
(`topbar | left-rail | deck | bottom`); the generic `PanelRenderer` handles badges
(icon + text, never hue alone), row/table/chip sections, required/blocked actions
(blocked = disabled buttons), and safety lines. The analyzer panel
(`panels/analyzerPanel.ts`) is the worked example. Full recipe + accessibility
acceptance checklist: `.claude/skills/add-cockpit-panel/SKILL.md`.

## Wire protocol

The WS client emits JSON messages of two shapes:

1. **Command envelope** (UI → sidecar):
   ```json
   { "request_id": "req_abc_xyz", "command": { "type": "set_depth", "depth": 0.55 } }
   ```
2. **Event** (sidecar → UI, push, no `request_id`):
   ```json
   { "type": "snapshot_changed", "snapshot": { ... } }
   ```

Acks (sidecar → UI, response) carry `request_id` + `ok` + optional payload.

Full type catalog: `src/ws/protocol.ts`.

### Command catalog (UI → sidecar)

| Command | Payload | Notes |
|---|---|---|
| `select_profile` | `{profile_id}` | Sets active profile |
| `set_depth` | `{depth}` | 0.10..0.90 |
| `set_pad_lock` | `{pad_id, locked}` | Per-pad lock |
| `toggle_preview` | `{on}` | Enables/disables ghost overlay |
| `regen` | `{}` | New seed, same depth |
| `prepare_send_plan` | `{}` | Preflights candidate into an inert SEND plan |
| `send` | `{}` | Applies the ready SEND plan to the device |
| `save` | `{label?}` | Promote current snapshot to device kit |
| `load_snapshot` | `{snapshot_id}` | Jump to a past snapshot |
| `undo` | `{}` | Walk history back one |
| `export_profile_model` | `{profile_id, target}` | `"binary"` or `"json"` |

### Event catalog (sidecar → UI, push)

| Event | Payload | Renders |
|---|---|---|
| `snapshot_changed` | `{snapshot}` | Pad cards |
| `mutation_previewed` | `{candidate \| null}` | Ghost overlay |
| `send_plan_changed` | `{send_plan \| null}` | SEND readiness / preflight gate |
| `history_updated` | `{history}` | History strip |
| `profile_changed` | `{profile \| null}` | Profile card |
| `session_status` | `{armed, midi_port, mode, unsaved_sends}` | Header status |

## State store

`src/state/store.ts` exposes a Zustand store with six slices, one per event type, plus
typed setters and a `reset()`. Selectors live alongside (`selectIsConnected`,
`selectIsArmed`, `selectUnsavedSends`, `selectPadCount`, `selectHasHistory`,
`selectCanUndo`, `selectSendPlanReady`, `selectCanSend`, `selectPreparedPadCount`).

`bindClientToStore(client, store?)` wires a `CockpitClient` instance's event stream to
the store. Returns an unsubscribe function.

## Coverage policy

`vite.config.ts` enforces **100% branch / line / function / statement** coverage on
`src/ws/**`, `src/state/**`, `src/cockpit/**`, `src/wizard/**`, and
`src/types/wizard_protocol.ts`. CI fails if it slips below.
