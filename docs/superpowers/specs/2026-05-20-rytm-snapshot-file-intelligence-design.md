# Rytm Snapshot File Intelligence Design

## Context

PRs #49, #50, and #51 landed the passive Rytm snapshot readiness stack:

- the 12-pad machine matrix identifies legal pad/machine combinations,
- snapshot machine values route to V1.34-backed mutable profiles where known,
- the in-memory snapshot intelligence report summarizes promoted facts, blocked facts, routed pads, and mutation readiness.

The missing operator step is file ingestion. Jose has real C6 SysEx kit and project dumps from the Analog Rytm MKII, including `ANALOGRYTMKITS2.syx`, which contains performance kits he actively uses. The next useful milestone is a passive command that can read one `.syx` file and print the existing snapshot intelligence report without opening MIDI ports or requiring the hardware to be on.

## Recommended Approach

Add a passive CLI command:

```powershell
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path>
```

The command reads bytes from the provided path, strips normal SysEx framing when present, decodes the first supported Rytm kit record through `AnalogRytmDevice.decode_snapshot`, and formats the result through the existing `format_rytm_snapshot_intelligence_report` function.

This is the recommended approach because it converts the merged snapshot intelligence core into something Jose can run against real kit dumps immediately, while preserving the repo's safety model: no MIDI sends, no port opens, no hardware mutation, no `mido` import, and no new runtime behavior.

## Alternatives Considered

### Snapshot-to-mutation preview

This would turn decoded kit facts into a passive mutation plan preview. It is exciting, but it depends on reliable file ingestion first. Building it before a file command would force tests to bypass the exact operator path Jose needs.

### Analog Four snapshot intelligence first

Analog Four support is important for the dual-machine dream project, but the Rytm has the immediate 12-pad performance-kit blocker. Analog Four should follow once the Rytm file-ingestion path proves the CLI/report pattern.

## Scope

This slice includes:

- one passive Rytm snapshot intelligence CLI command,
- a small file-decoding adapter that turns a `.syx` file into a `RytmKitSnapshot`,
- support for standard `F0 ... F7` framed SysEx bytes and already-stripped bytes,
- clear errors for missing files, directories, malformed SysEx, negative slots, and unsupported slot-indexed lookup,
- CLI help text and README/docs/status updates,
- tests proving the command stays passive and deterministic.

This slice does not include:

- real MIDI input capture,
- sending mutations to hardware,
- mutating from the decoded snapshot,
- continuous tracking of hand tweaks,
- multi-kit bank iteration across all 128 kits,
- Analog Four file decoding.

The first command intentionally reports only the first supported kit record because `snapshot.envelope.find_kit_record` currently supports `slot=0` only. The command accepts `--slot 0` as the default and rejects non-zero slots with a clear unsupported-slot error until the real bank offset table lands.

## Architecture

The code should stay inside existing boundaries:

- `rytm_randomizer/reports/rytm_snapshot_intelligence.py` owns the operator-facing report and can grow the `CliCommand` registration plus CLI argument parsing.
- A focused helper under `rytm_randomizer/snapshot/` owns file-to-raw-payload decoding if adding that helper keeps `reports/` from owning low-level SysEx framing details.
- `rytm_randomizer/devices/analog_rytm.py` and its existing decoder strategy remain the canonical path from raw Rytm SysEx bytes to `RytmKitSnapshot`.
- `rytm_randomizer/cli.py` lazily imports the command module, matching the existing passive report pattern.
- `rytm_randomizer/help_text.py`, README, and docs describe the command.

No new top-level package or module is needed. No device-family code should be duplicated. The shared Elektron framing rules continue to live in `rytm_randomizer/snapshot/envelope.py`.

## Data Flow

1. Operator runs `rytm-snapshot-intelligence-report <syx-path>`.
2. CLI parser validates the path argument and optional `--slot 0`.
3. File reader loads the bytes from disk.
4. Framing helper strips one outer `F0`/`F7` pair when both are present.
5. `AnalogRytmDevice.decode_snapshot(raw, slot=0)` decodes the payload.
6. `format_rytm_snapshot_intelligence_report(snapshot)` builds deterministic output.
7. CLI writes lines to stdout and returns `0`.

Error exits return `2` for command misuse or unreadable/malformed input, write a concise message to stderr, and never print a Python traceback for expected operator mistakes.

## Safety

The command is passive by construction:

- reads a local file only,
- imports no `mido`, `rtmidi`, `mido_provider`, `real_midi_adapter`, engines, shell, group runner, scene runner, or MIDI send path,
- sends no MIDI,
- opens no MIDI input or output port,
- mutates no hardware state,
- does not require hardware to be connected.

## Testing

Use TDD. The first tests should fail before implementation:

- decoding a temporary framed `.syx` file prints the snapshot intelligence report and includes the kit name,
- unframed bytes are accepted for tests and developer workflows,
- missing path returns exit code `2` with a readable error,
- directory path returns exit code `2`,
- malformed SysEx returns exit code `2` without traceback,
- `--slot 1` returns a clear unsupported-slot error while `--slot 0` succeeds,
- passive MIDI safety tests include the new command,
- help text fixture includes the new command,
- the command is deterministic across repeated runs.

Verification before PR must include focused tests, architecture tests, full pytest, lint trio, coverage, and the code-review gate required by the repo.

## Follow-Up Sequence

1. Rytm snapshot file intelligence CLI.
2. Rytm bank offset table for selecting and reporting more than the first kit in a kit-bank dump.
3. Passive snapshot-to-mutation preview from decoded kit facts.
4. Mock-safe snapshot mutation routing from decoded facts.
5. Analog Four snapshot file intelligence using the same Device Strategy boundary.
6. Dual-machine snapshot mode where Rytm, Analog Four, or both can be captured and mutated independently.

## Approval State

Jose approved the recommended direction in the chat before this spec was written. This spec records the agreed scope so the implementation can proceed as one clean PR from `origin/modularize-v1.34`.
