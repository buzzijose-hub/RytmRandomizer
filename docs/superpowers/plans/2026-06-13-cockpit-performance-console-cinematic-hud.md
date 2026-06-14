# Cockpit Performance Console Cinematic HUD

> Status: in-flight

## Goal

Turn the existing passive Cockpit Performance Console packet into the visual
operator surface Jose has been steering toward: a dense dark HUD with a top
safety bar, device rail, all-12-pad Rytm snapshot deck, Style Crates and queue
mutation panel, blocked hardware actions, command queue, safety checklist, and
bottom session strip.

## Product Rules Captured

- This is a frontend composition slice. It consumes the already-merged passive
  `LiveGuiPerformanceConsoleModelDict`; it does not invent a second data model.
- The operator must see both devices at a glance: Analog Rytm MKII as the
  12-pad sound-design surface and Analog Four MKII as the four-track
  review-only synth surface.
- The Rytm view must show all 12 pads in one deck, not a four-pad-only mock and
  not a tab-per-pad workflow.
- Style Crates, queued moves, mutation journal, depth/profile, action buttons,
  blocked hardware actions, safety, and command queue stay visible together so
  the cockpit reads like a live performance console.
- Every active hardware action remains disabled in this route. Real sends stay
  in the explicitly armed snapshot shell.

## Scope

- Reshape `desktop/web/src/cockpit/PerformanceConsole.tsx` into HUD regions:
  topbar, device rail, snapshot deck, mutation panel, review boards, command
  queue/safety, and bottom strip.
- Add CSS for the cinematic dark operator layout using the existing cockpit
  token palette and responsive constraints.
- Preserve all existing passive section IDs and test IDs so prior report
  coverage remains valid.
- Extend React tests to pin the new HUD regions, disabled controls, 12-pad deck,
  and safe fallback rendering.
- Update README/status/PR docs.

## Non-Goals

- No MIDI behavior change.
- No WebSocket command dispatch or sidecar command execution.
- No audio analyzer execution.
- No installer/package change.
- No new Python protocol field.

## Verification

- `npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run test:run`
- `npm.cmd run test:coverage`
- `npm.cmd run typecheck`
- `npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run build`
- Playwright render sanity at 1672x944 and 390x844
- `python -m pytest tests/architecture/ -q`
- `git diff --check`
