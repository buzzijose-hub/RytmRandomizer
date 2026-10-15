# CodeQL Path-Injection Disposition

Scope: PR #254 at `7370d407eb1c39b3db3b393765e198d2907c9566`,
analysis `1940077933`, merge commit `a9352a08804f436d9503bb8a71ec2e76ca15f604`.
The delivered binaries use source `f67059ba844f34dfcec62d2b3d2a8d16f50ac9a9`;
the intervening receipt changes do not change production code.

All five dispositions were accepted by GitHub under `buzzijose-hub` at
2026-10-13T01:25:58Z through 01:26:02Z. The actual aggregate check
[`115079424161`](https://github.com/buzzijose-hub/RytmRandomizer/runs/115079424161)
then became **success**, with "No new alerts in code changed by this pull
request." No workflow, severity, branch protection or check result was edited.

## Findings And Evidence

| Alert | Sink | Disposition basis |
| --- | --- | --- |
| 21 | `cockpit/export/reader.py:37`, non-following stat | All reported reference-sound session and library-record flows pass the full-match ID guards below before constructing the path. |
| 22 | `cockpit/export/reader.py:57`, `os.open` | Same constrained IDs; the bounded reader also checks regular-file type, opened-file identity, size and available no-follow flags. |
| 23 | `cockpit/export/reader.py:66`, post-read stat | Same constrained IDs; the second stat compares identity/size/modification time and does not expand accepted IDs. |
| 24 | `cockpit/library/store.py:448`, `lexists` | `get` rejects invalid record IDs before its directory scan or this predicate; `_record_path` validates again. |
| 25 | `cockpit/library/store.py:448`, `Path.is_file` | The non-strict branch uses the same validation and configured root as alert 24. |

These are **false positives for the reported client-ID path-injection flows**,
not accepted vulnerabilities and not proof of security against every local
filesystem attack. Both the orchestrator and an independent read-only security
review inspected the reported flows and their validators.

- `LibraryStore.get` calls `_validate_record_id` before filesystem access.
  `_record_path` revalidates before joining the configured library directory.
  Only strings fully matching `[A-Za-z0-9][A-Za-z0-9_-]{0,127}` are accepted.
- `ReferenceSoundStore.load` calls `require_sound_session_id` before joining
  the configured sound directory. Only `sound-[a-f0-9]{32}` fully matches.
- Neither grammar admits dots, slashes, backslashes, drive prefixes, alternate
  data-stream colons, NULs, absolute paths or trailing newlines. There is no
  percent-decoding step that subsequently turns an accepted ID into a path.
- Roots are injected by application boot/configuration, not supplied by these
  WebSocket command fields. Artifact filenames are separately constrained by
  digest/extension validation. An allowed ID selects only its fixed child name.
- The earlier direct-DTO publication gap was separately reproduced and fixed
  in production `5db6e6de`: `_write_record` validates `_record_path` before
  metadata I/O. That is a real repair, not the reason to ignore these alerts.

## Reproducible Regression

Run from the assembly checkout with the existing environment and MIDI disabled:

```powershell
Set-Location "C:\Users\Jose Buzzi\.codex\worktrees\rytm-studio-mapping\RytmRandomizer"
$env:PYTHONPATH = (Get-Location).Path
$env:RYTM_RAND_MIDI_BACKEND = 'off'
$env:RYTM_RAND_UPDATES = 'off'
& "C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe" -m pytest tests/cockpit/test_library_original_source_diagnostics.py tests/cockpit/test_reference_sound_foundation.py tests/cockpit/test_artifact_reader.py tests/cockpit/test_export_writer.py tests/cockpit/test_reference_sound_handlers.py -n 2 -q
```

The existing 345-case selection passed before the new command regression;
the composed final selection passed **373 cases, 3 warnings, 6.12 seconds**.
The additional 28 cases exercise real `handle_command` routing for both device
fixtures, malformed `source_record_id`/`session_id`, `controls`/`reopen`, and
sentinels on stat/scan/create/open/lexists. They assert refusal before I/O,
redacted responses, unchanged source/session files and plan, no arm, and exact
reopen of the previously retained session. Existing successful full WebSocket
journeys are the positive controls.

An in-memory mutation replacing the library validator with an identity function
caused both device cases for a Windows absolute ID to fail at the filesystem
sentinel: **2 failed**, as expected. No production source was edited by that
probe. This proves the regression catches removal of the relevant guard.

## Disposition Boundary

Use GitHub's normal **false positive** alert disposition, with this evidence
linked in each alert. Do not disable CodeQL, alter severities, exclude readers,
change branch protection, forge a successful check or mark a finding fixed by
unrelated code. Verify the actual aggregate check after disposition/rescan.
[GitHub's triage guidance](https://docs.github.com/en/code-security/how-tos/manage-security-alerts/manage-code-scanning-alerts/triage-alerts-in-pull-requests)
allows dismissal of a false positive when a sanitizer is not modeled.
GitHub dispositions apply across branches; the reviewed source/flow scope
above is therefore part of the recorded justification, not a blanket waiver.

This assessment assumes the configured local storage namespace is controlled
by the local operator. It does not certify hostile replacement of ancestors,
Windows junction/reparse races, arbitrary local root injection or a compromised
OS account. Those require a separate local-filesystem threat model; they are
not introduced by the restricted client ID. Reopen these alerts if a future
change permits client paths, changes the grammar/decoding, or bypasses the
validators. The existing token-storage result is not among alerts 21-25 and
is not dismissed by this disposition.

Protected human approval, hardware observations and rehearsal remain separate.
No real MIDI/USB access was performed for this security verification.
