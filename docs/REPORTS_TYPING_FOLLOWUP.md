# Reports layer: TypedDict now, dataclasses next

**Status:** in progress (TypedDict conversion) · fast-follow agreed for dataclasses.

## The abstraction problem this fixes

The seven `build_*_report()` functions under `rytm_randomizer/reports/_core/`
each return a nested `dict[str, object]` whose key set is **fixed and known**
but was never declared. `object` means "could be anything", so every read
needs a runtime narrowing check, and `Unknown` propagates into every consumer.

That is what a strict type checker reports as hundreds of errors. The errors
were a symptom; the missing type declaration was the cause.

The repo had already solved this elsewhere: the newer
`reports/live_gui_*_model.py` modules use **frozen dataclasses + `TypedDict`
payloads** and typecheck with zero errors. The `_core` modules are simply the
older, pre-pattern style.

### Measured, on `registry.py`

| Approach | Strict errors | Runtime narrowing helpers |
| --- | --- | --- |
| `dict[str, object]` + `_section` / `_rows` / `_text` | 50 → 3 | 3 per module |
| `TypedDict` | **0** | **none** |

The `TypedDict` version is also shorter: declaring the shape deletes the
helpers rather than adding them.

## Why `TypedDict` first, not dataclasses directly

The end state is dataclasses, matching `live_gui_*_model.py`. But a dataclass
changes the **return type** of every builder, so every caller that does
`report["title"]` or hands the value to `json.dumps` breaks.

`TypedDict` gets the full static type safety while the values stay plain
dicts, so nothing downstream changes and the conversion is verifiable
step-by-step against byte-identical report output. It is the safe increment,
not the destination.

## Fast-follow: convert to frozen dataclasses

Once every `_core` module is `TypedDict`-typed, convert each report to the
`live_gui_*_model.py` shape:

1. A frozen dataclass per report and per repeated row (`RegistryReport`,
   `ProfileSummaryRow`, …).
2. The matching `TypedDict` retained as the **JSON-ready payload contract**,
   produced by a `*_payload()` function — exactly as
   `live_gui_device_inventory_model.py` does with
   `LiveGuiDeviceInventoryModel` / `LiveGuiDeviceInventoryCardDict`.
3. `build_*` returns the dataclass; `format_*` reads attributes instead of
   string keys; the CLI/JSON path goes through `*_payload()`.
4. Callers migrate from `report["key"]` to `report.key`. This is the breaking
   step and the reason it is a separate PR.

Benefits over `TypedDict` alone: attribute access instead of string keys
(typo-proof), immutability by construction, `__eq__`/`__repr__` for free, and
one obvious place to hang per-report behavior instead of module-level helper
functions keyed by convention.

## Verification contract for both steps

Every conversion must keep report output byte-identical. The check used
throughout:

```python
build_*_report()  # for all seven reports
# → json.dumps(..., sort_keys=True, default=str) compared against a
#   snapshot captured before the first edit
```

Plus the report golden fixtures under `tests/fixtures/report_goldens/` and
the full suite. A conversion that changes output is a behavior change, not a
refactor, and must be rejected.

## Related

- `tests/architecture/test_reports_max_module_size.py` — the 1500-LOC cap that
  forced the `_core/` split this typing work sits on top of.
- `rytm_randomizer/reports/live_gui_device_inventory_model.py` — the
  reference implementation of the target pattern.
- `pyrightconfig.strict.json` + `scripts/typecheck_touched.py` — the
  incremental strict-typing gate that surfaced the problem.
