# Show Kit Forge maintainer-review reconciliation

Status: software repairs verified locally; identified studio build and required GitHub review pending.

The existing [PR #238](https://github.com/buzzijose-hub/RytmRandomizer/pull/238)
and [implementation plan](superpowers/plans/2026-09-04-show-kit-forge.md) remain
the delivery boundary. This ledger addresses the
[maintainer review](https://github.com/buzzijose-hub/RytmRandomizer/pull/238#pullrequestreview-5133649443)
against the actual starting head `6cfde1fcd306fa2f5a30ca4a8f2869ec369d9914`.
Green CI or an agent verdict cannot substitute for required maintainer review.

## Requested findings

| Finding | Required repair and evidence | Disposition |
| --- | --- | --- |
| C1: pre-authentication panel dispatch | Preserve the shared-store authenticated session generation; rerun valid/missing/wrong-token browser journeys and reconnect/remount regressions. | Verified: real-sidecar browser suite 21 passed, including valid/missing/wrong-token journeys; remount/reconnect unit tests pass. |
| I1: discarded calibration offset | Use the canonical calibration result; reject drift before producing any candidate bytes. | Verified in the final full suite and 100% touched-file coverage. |
| I2: export/import identifier mismatch | The alleged 74-character package-name rejection is not reproduced: package ID does not become bank ID. Centralize the existing 64/96 contracts and test default74/explicit96 names through export/verify/import. Fix the reproduced maximum-revision import failure by starting the new catalog at revision0 while preserving its source manifest. | Verified in the final full suite and 100% touched-file coverage. |
| I3: duplicated per-field Q8.8 renderer | Reuse the existing saved-KIT field schema and typed field codec while preserving exact representability and unknown bytes. | Verified in the final full suite and 100% touched-file coverage. |
| I4: flat per-field facts | Put offset/encoding/range/scale facts on the canonical calibration record and consume them consistently. | Verified in the final full suite and 100% touched-file coverage. |
| I5: duplicated validation hidden by aliases | Consolidate primitives behind an appropriate shared boundary and remove the renamed-definition/short-alias pattern. Preserve each public error contract. | Verified in the final full suite and 100% touched-file coverage. |
| I6: device vocabulary and domain duplication | Alias canonical device types and derive supported domains from the established device facts/registry. | Verified in the final full suite and 100% touched-file coverage. |
| I7: unbounded free-form blocker prose | Publish closed reason tokens; keep operator identifiers separate from machine-readable reasons and render human explanations in the UI. | Verified in the final full suite and 100% touched-file coverage. |
| I8: missing architecture inventory/enforcement | Add the workspace responsibility row and rule-10 import-matrix enforcement entry; reconcile diagrams after the refactor. | Verified: 805 architecture cases pass; scoped docs/diagram review has no open Important findings. |

## Additional review observations

The closeout also inspected frozen handler results, SysEx marker reuse, opened-file
identity checks, canonical JSON encoders, rejection assertions, and panel
cohesion. The handler envelope is now frozen; store/export/report identities reuse one
canonical JSON encoder. New rejection tests assert the specific boundary reason
and the existing sanitized wire error. The standard F0/F7 marker constants remain
local to framing modules: exposing a new public API for two protocol bytes is
not necessary for correctness, and the full new candidate codec is shared. The
existing large main panel remains a documented readability minor; the new A4
review is a separate component with explicit stale-response tests.

The opened-file identity minor is retained with a specific boundary rationale:
the bounded store reader and streaming export reader each verify that the
opened descriptor still identifies the inspected file. Their byte limits,
post-read checks and error contracts differ. Export also checks directory
identity during atomic publication and cleanup; those are different phases,
not extra copies of a file reader. A future public checked-open helper may
reduce the two reader checks, but this closeout retains their protection.
All nine broad `ValueError` sites in the four new Show Bank validation test
files now assert case-specific refusal reasons; existing structured `DataError`
checks and pre-existing unrelated rejection tests are preserved.

The coverage advisory is not reproduced: the original dotted-module command
passes 13 Forge tests at 100% (128 statements/34 branches). The rule's stale 98%
reference is corrected to 99%, and its final-closeout guidance now names the
existing CI touched-file checker. Neither coverage gate is weakened.

## Regression evidence

- Calibration drift, exact conversion and byte isolation:
  [`test_analog_four_sysex_calibration.py`](../tests/test_analog_four_sysex_calibration.py)
  and [`test_devices_strategies_analog_four_filter1_frequency_candidate.py`](../tests/test_devices_strategies_analog_four_filter1_frequency_candidate.py).
- Default and maximum package identifiers, catalog imports and shared validation:
  [`test_validation_closeout.py`](../tests/cockpit/show_bank/test_validation_closeout.py)
  and [`test_readiness.py`](../tests/cockpit/show_bank/test_readiness.py).
- Inert A4 preparation and authenticated request boundaries:
  [`test_a4_preparation.py`](../tests/cockpit/show_bank/test_a4_preparation.py)
  and [`test_a4_preparation_ws.py`](../tests/cockpit/show_bank/test_a4_preparation_ws.py).
- Authenticated session generation, remount and stale async results:
  [`ShowKitForgePanel.test.tsx`](../desktop/web/tests/cockpit/ShowKitForgePanel.test.tsx),
  [`A4PreparationPanel.test.tsx`](../desktop/web/tests/cockpit/A4PreparationPanel.test.tsx)
  and the real-sidecar [`handshake_token.spec.ts`](../desktop/web/e2e/handshake_token.spec.ts).

## A4 and studio-build boundary

The completed inert preparation builder and authenticated UI/WS review distinguish
software evidence from missing hardware evidence. They reuse canonical candidate,
capture, scope and serialization contracts and perform zero physical output. The generated Filter 1 Frequency scratch
artifact is not a grant of A4 SEND authority. No unobserved load, sound, save,
recapture, source restoration, or destination behavior will be marked verified.

The final handoff will identify the exact launch executable, Git source revision,
build manifest and hashes, self-contained sidecar, smoke-test result, remaining
review state, and the smallest operator-present
[studio procedure](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md).

## Current local verification

Full Python: 8,926 passed, 5 skipped in 272.28s. All 32 touched production
modules cover 6,458 statements and 1,558 branches at 100%; whole-package pure
branch coverage is 99.3597%. All 805 architecture and 685 frozen parity cases
pass. Frontend: 809 tests in 62 files, all coverage metrics 100%; typecheck,
lint and production build pass. Full Playwright: 21 passed, 2 existing skips
in 50.2s with disabled/fake MIDI; the three generated screenshots were inspected.

Ruff, stricter new-module rules, Black, isort, strict Pyright 1.1.411, touched
Vulture80/whole-package70, touched coverage/ratchet, diff and state-schema
checks pass. The fast and Cockpit aggregates preceded three final logging
regressions; the final full run covers those regressions. Earlier diagnostics
exposed data-root function exports, a WS dependency edge, stale test imports
and a lifecycle marker; all were corrected without weakening their gates.

The final scoped review also closed duplicate boolean validators, literal UI
scope counts, unbounded WS diagnostics and build-variable documentation gaps.
The existing PR comment records post-push dimension review, hosted checks and
the exact studio artifact/smoke receipt as those external steps complete.
