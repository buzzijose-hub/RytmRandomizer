# PR #21 Module Mapping — superseded by PR #43 + PR #36 review

> **Status as of 2026-05-19:** PR #21 was closed in favor of PR #36 as the dual-machine
> redo target. PR #43 then extended the `Device` Protocol with three Strategy capability
> sub-Protocols (`SnapshotDecoder`, `MutationPlanner`, `MessageRenderer`) plus a
> `report_header` attribute. **The mapping below is no longer accurate** — it predates
> the Strategy seam.
>
> For the current redo-path guidance, see:
>
> - **[Architecture review on PR #36](https://github.com/buzzijose-hub/RytmRandomizer/pull/36#issuecomment-4490858526)** — the authoritative file-by-file plan for the new dual-machine PR.
> - **[`docs/ARCHITECTURE.md` §6.1](ARCHITECTURE.md#61-device-protocol--strategy-seam-ws-s5--strategy)** — Device + Strategy seam contract and "how to add a new device family."
> - **[`CONTRIBUTING.md` § Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables)** + § PR bundling — non-negotiables every device-family PR must satisfy.
> - **`tests/architecture/test_device_protocol_enforcement.py`** — the 7 CI gates that mechanically reject the patterns this file's old mapping recommended migrating into.
>
> The historical mapping (per-file map of codex's pre-Strategy PR #21 into the WS-S5
> shape) is kept below for the public-record diff, but **do not use it to plan new
> work**.

---

## Historical (pre-Strategy) mapping — DO NOT USE FOR NEW WORK

This table was authored when the `Device` Protocol was 5 attrs + 4 methods (the WS-S5
shape). It told codex to merge a flat top-level `analog_four_*.py` cluster into one
file at `devices/analog_four.py`. **The new contract requires three Strategy modules
under `devices/strategies/` in addition to the device class**, so the right column
below is incomplete by today's standard.

The summary one-liner is still true: *flat sibling files at the package root must
become one `Device` registration plus per-capability strategies under
`devices/strategies/`*. The exact filename and division of work changed.
