# Cockpit Web Frontend (WS-I scaffold)

Vite + React 18 + TypeScript 5 scaffold for the RytmRandomizer cockpit. Talks to the
Python sidecar over WebSocket (`ws://127.0.0.1:4317/ws` by default; override with
`RYTM_RAND_WS_PORT` on the sidecar side).

This directory is the **scaffold only** (WS-I). The v10 cockpit UI components land in
`src/cockpit/**` from **WS-J**.

## Layout

```
desktop/web/
├── index.html               # Vite entry
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .eslintrc.json
├── README.md
├── src/
│   ├── main.tsx             # React root bootstrap
│   ├── App.tsx              # Placeholder — "Connecting…" until first session_status
│   ├── ws/
│   │   ├── client.ts        # Typed WebSocket client (Command / Event)
│   │   └── protocol.ts      # TS types one-to-one with Python dataclasses
│   ├── state/
│   │   ├── store.ts         # Zustand store: snapshot / preview / history / profile / session
│   │   └── index.ts         # bindClientToStore + re-exports
│   └── types/
│       └── index.ts         # Public type re-exports
└── tests/
    ├── ws-client.test.ts    # Vitest with mocked WebSocket — 100% branch
    ├── store.test.ts        # Vitest — 100% branch
    └── setup.ts             # @testing-library/jest-dom matchers
```

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Build | Vite 5 | Fast dev loop, ESM-first, Rollup under the hood |
| UI | React 18 | Ecosystem + concurrent rendering for ghost-overlay perf |
| Lang | TypeScript 5 (strict) | Mirrors the Python dataclass types end-to-end |
| State | Zustand 4 | Tiny, no provider, perfect for "one slice per event" |
| Test | Vitest 2 + jsdom + @testing-library/react | Vite-native, fast |
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
npm run test:coverage     # vitest --run --coverage  (≥ 100% on ws/** and state/**)
```

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
| `send` | `{}` | Applies candidate to device |
| `save` | `{label?}` | Promote current snapshot to device kit |
| `load_snapshot` | `{snapshot_id}` | Jump to a past snapshot |
| `undo` | `{}` | Walk history back one |
| `export_profile_model` | `{profile_id, target}` | `"binary"` or `"json"` |

### Event catalog (sidecar → UI, push)

| Event | Payload | Renders |
|---|---|---|
| `snapshot_changed` | `{snapshot}` | Pad cards |
| `mutation_previewed` | `{candidate \| null}` | Ghost overlay |
| `history_updated` | `{history}` | History strip |
| `profile_changed` | `{profile \| null}` | Profile card |
| `session_status` | `{armed, midi_port, mode, unsaved_sends}` | Header status |

## State store

`src/state/store.ts` exposes a Zustand store with five slices, one per event type, plus
typed setters and a `reset()`. Selectors live alongside (`selectIsConnected`,
`selectIsArmed`, `selectUnsavedSends`, `selectPadCount`, `selectHasHistory`,
`selectCanUndo`).

`bindClientToStore(client, store?)` wires a `CockpitClient` instance's event stream to
the store. Returns an unsubscribe function.

## Coverage policy

`vite.config.ts` enforces **100% branch / line / function / statement** coverage on
`src/ws/**` and `src/state/**`. CI fails if it slips below.

## WS-J handoff

`src/cockpit/**` is reserved for WS-J. This scaffold leaves the directory untouched and
exposes everything WS-J needs through:

- `src/types/index.ts` — full type surface
- `src/state/index.ts` — store + binder
- `src/ws/client.ts` — `CockpitClient` + `ConnectionStatus`
- `src/App.tsx` — replace contents with `<Cockpit />` mount when WS-J lands
