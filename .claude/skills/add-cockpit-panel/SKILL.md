---
name: add-cockpit-panel
description: |
  Add a new schema-driven panel to the cockpit web frontend. Use when the
  user asks to "add a panel", "add a cockpit UI element", "surface a report
  in the cockpit", "add a section to the performance console", or to render
  any new operator-facing surface in desktop/web. Every new UI element goes
  through the PanelSpec platform: a Python PanelSpecDict builder feeds the
  generated TypeScript protocol, and one registry entry renders it via the
  generic PanelRenderer — no bespoke React section per report.
---

# Add a cockpit panel (schema-driven)

New cockpit UI elements are **data, not components**. The platform pieces:

| Piece | Path |
|---|---|
| PanelSpec vocabulary (source of truth) | `rytm_randomizer/reports/panel_spec.py` |
| ReportSpec -> PanelSpec bridge | `panel_spec_from_report_spec()` in the same module |
| TS protocol (GENERATED — never hand-edit) | `desktop/web/src/types/live_gui_protocol.ts` |
| Generator | `scripts/generate_live_gui_protocol_ts.py` |
| Generic renderer | `desktop/web/src/cockpit/panels/PanelRenderer.tsx` |
| Region host | `desktop/web/src/cockpit/panels/PanelHost.tsx` |
| Registry (one line per panel) | `desktop/web/src/cockpit/panels/registry.ts` |
| Worked example | `desktop/web/src/cockpit/panels/analyzerPanel.ts` + `tests/cockpit/panels/analyzerPanel.test.tsx` |

## Steps

1. **Model the panel in Python.** Build the panel content as a
   `PanelSpecDict` using the builders in
   `rytm_randomizer/reports/panel_spec.py` (`badge`, `rows_section`,
   `table_section`, `chips_section`, `panel_spec`). If the content already
   exists as a `reports.core.ReportSpec`, call
   `panel_spec_from_report_spec(spec)` so ONE spec feeds both the passive
   text report and the cockpit panel. Never invent a parallel panel schema.
2. **If (and only if) you extended the TypedDict vocabulary**, extend the
   generator tables in `scripts/generate_live_gui_protocol_ts.py`, then
   regenerate the protocol + fixture:
   ```bash
   .venv/bin/python scripts/generate_live_gui_protocol_ts.py --fixture
   ```
   `tests/architecture/test_live_gui_protocol_is_generated.py` pins both
   artifacts byte-for-byte — hand edits to the `.ts` file will fail CI.
3. **Write the selector** in `desktop/web/src/cockpit/panels/<name>Panel.ts`:
   a pure function `(model: LiveGuiPerformanceConsoleModelDict) =>
   PanelSpecDict`. No React, no fetch, no state.
4. **Register the panel** — one entry in
   `desktop/web/src/cockpit/panels/registry.ts`:
   ```ts
   { id: '<name>', region: 'deck', selector: <name>PanelSpec, component: PanelRenderer }
   ```
   Regions: `'topbar' | 'left-rail' | 'deck' | 'bottom'`. The `PanelHost`
   for that region renders it automatically; do not add JSX to
   `PerformanceConsole.tsx`.
5. **Test it** in `desktop/web/tests/cockpit/panels/<name>Panel.test.tsx`,
   consuming the committed JSON fixture
   (`tests/cockpit/fixtures/performance_console.json` via
   `performanceConsoleFixture.ts`). Cockpit coverage thresholds are 100%
   lines/branches/functions/statements — cover every selector branch.
6. **Python tests** for any new builder/bridge behavior go in
   `tests/test_panel_spec.py` (`pytest.mark.fast`, 100% branch on touched
   files).

## Gates (run all before finishing)

```bash
.venv/bin/python -m pytest tests/test_panel_spec.py tests/architecture/ -q
.venv/bin/python -m ruff check . && .venv/bin/python -m black --check --target-version=py311 . \
  && .venv/bin/python -m isort --profile black --check-only .
cd desktop/web && npm run typecheck && npm run lint && npx vitest run --coverage
```

## Per-panel accessibility acceptance checklist

Every panel must satisfy ALL of these before it ships (the generic
`PanelRenderer` gives you most of them for free — do not bypass it):

- [ ] **Labels.** The panel is a `<section>` with `aria-labelledby` pointing
      at its `<h2>`; every chip row / action strip carries an `aria-label`
      derived from the panel title; form fields (if any) have `<label>`s
      (`tests/architecture/test_a11y_every_form_field_has_label.py`).
- [ ] **Keyboard.** Everything interactive is a real `<button>` / `<a>` /
      form control — never a `div` with `onClick`
      (`test_a11y_no_div_onclick.py`). Blocked hardware actions render as
      `disabled` buttons so they are announced but not operable.
- [ ] **Contrast tones.** Badge tones (`ok`/`warn`/`risk`/`neutral`) always
      pair an icon glyph with text — never hue alone. Colors come only from
      the documented tokens in `src/cockpit/styles.css`
      (`test_a11y_color_palette_aa.py` checks the token pairs).
- [ ] **aria-live rules.** Panels are passive renders — no `aria-live` on
      panel content. If a panel must announce a state change, route it
      through the shared announcer (`src/a11y/`, see
      `test_a11y_announcer_is_wired.py`); never add a second live region.
- [ ] **No redundant roles** on semantic elements
      (`test_a11y_no_role_attribute_redundancy.py`), and decorative glyphs
      are `aria-hidden="true"`.

## Hard boundaries

- The panel is **passive**: selectors read the console packet only. No
  WebSocket sends, no port opens, nothing that could reach the `senders`
  ArmedApply seam (`.claude/rules/live-but-passive-midi.md`).
- `desktop/web/src/types/live_gui_protocol.ts` is generated output — edit
  the Python TypedDicts and re-run the generator instead.
- Report-shape censuses in
  `tests/architecture/test_report_module_shape.py` only shrink: new Python
  panel builders use the shared helpers (`reports.formatter.require_nonblank`,
  `reports.core`), never local copies.
