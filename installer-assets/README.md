# installer-assets/

Assets consumed by **BeeWare briefcase** when building the native
end-user installers (Windows `.msi`, macOS `.pkg`, Linux AppImage / `.deb` / `.rpm`).

`pyproject.toml` points `[tool.briefcase.app.rytm-randomizer] icon` at the
base name `installer-assets/icon` — briefcase appends the right extension
per platform.

## What's here today

- `icon.svg` — **placeholder** text-mark of "RR / RANDOMIZER" on a dark
  square. Hand-rolled, under 30 lines, no binary dependencies. Briefcase
  does not consume `.svg` directly, but the file is committed so the repo
  visibly carries the icon intent. Briefcase falls back to its built-in
  defaults during `briefcase create` if no per-platform raster is present,
  which is fine for development and CI smoke-test builds.

## What still has to land before a signed release

A designer needs to deliver rendered raster icons. Drop them into this
directory next to `icon.svg`:

| File | Purpose | Source format |
|------|---------|---------------|
| `icon.ico` | Windows `.msi` installer + app entry | multi-resolution `.ico` (16, 32, 48, 64, 128, 256) |
| `icon.icns` | macOS `.app` / `.pkg` | Apple icon-set `.icns` (16 - 1024) |
| `icon-16.png` | Linux AppImage / system package | 16x16 PNG |
| `icon-32.png` | Linux AppImage / system package | 32x32 PNG |
| `icon-64.png` | Linux AppImage / system package | 64x64 PNG |
| `icon-128.png` | Linux AppImage / system package | 128x128 PNG |
| `icon-256.png` | Linux AppImage / system package | 256x256 PNG |
| `icon-512.png` | Linux AppImage / system package | 512x512 PNG |

Briefcase auto-picks the right file for each backend; no `pyproject.toml`
change is needed when these land — just drop them next to `icon.svg`.

## Why placeholder and not generated PNGs

We deliberately do **not** ship hand-generated PNGs in the repo:

- A text-mark PNG is worse than the briefcase default for evaluating UX
  during dev (designers can't review what isn't theirs).
- Committing fake binary art guarantees the placeholder ships in a signed
  release if the icon work slips. A glaring SVG-only state is the
  forcing function.

## See also

- `docs/BUILDING_INSTALLERS.md` — the full release-engineer workflow.
- `pyproject.toml` `[tool.briefcase.app.rytm-randomizer]` — where the icon
  path is referenced.
