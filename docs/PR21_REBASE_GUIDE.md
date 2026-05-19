# PR #21 Rebase Guide — superseded; PR #21 is closed

> **Status as of 2026-05-19:** PR #21 was closed (see GitHub history) in favor of
> PR #36 (`codex/dual-machine-subpackage-cleanup`) as the dual-machine redo target.
> PR #43 then extended the `Device` Protocol with three Strategy capability
> sub-Protocols (`SnapshotDecoder`, `MutationPlanner`, `MessageRenderer`) plus a
> `report_header` attribute, and added seven CI-enforced architecture tests that
> mechanically reject the patterns this guide's migration plan predates.
>
> **For the current redo path on PR #36, see:**
>
> - **[Architecture review on PR #36](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526)** — authoritative, includes the file-by-file plan, the 7 architecture-test gates, and the open questions.
> - **[`docs/ARCHITECTURE.md` §6.1](ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy)** — Device + Strategy seam contract.
> - **[`CONTRIBUTING.md`](../CONTRIBUTING.md)** — strict rules, PR-bundling rule (no stacked cascades), plan-document trigger conditions, and the 16 plan-requirement gates.
> - **[`docs/PR21_MODULE_MAPPING.md`](PR21_MODULE_MAPPING.md)** — also superseded; same pointers as this file.
>
> The "expected diff ~5-8k LOC after rebase" claim below is no longer accurate —
> the Strategy seam means the new dual-machine PR's analog-four work is "one
> registered Device class + three strategy modules + a bundled set of
> `AnalogFour*` tests", measured in low single-digit-thousand LOC for the device
> path itself.
>
> **The historical body below is kept for the public-record diff only. Do not use
> it to plan new work.**

---

## Historical (pre-Strategy) rebase plan — DO NOT USE FOR NEW WORK

(Original content preserved for archaeology. Reviewers planning the PR #36 redo
should ignore this and follow the [PR #36 architecture review](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526) instead.)
