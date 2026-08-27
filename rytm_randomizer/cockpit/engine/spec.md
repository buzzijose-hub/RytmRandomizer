# Cockpit Mutation Engine — Normative Algorithm Specification

**Status:** Phase 1 normative — must be implemented byte-identically by every reference implementation (Python today; C99 / Rust on the Phase 4 hardware runtime).
**Authority:** This document. The Python implementation in `mutate.py` + `prng.py` conforms to this spec; the JSON conformance corpus under `tests/cockpit/fixtures/engine_conformance/` is the byte-frozen reference output.

This file is the **single source of truth** for how `mutate(snapshot, profile, depth, seed, target_pad_ids=()) → MutationCandidate` produces its output. Any disagreement between this file and a reference implementation is a spec defect (file an issue and reconcile in this document first; the implementation follows).

A C99 or Rust port that satisfies the entire conformance corpus (`tests/cockpit/test_engine_conformance.py`) is *by construction* conformant.

---

## 1. Inputs and types

The mutation engine is a pure function:

```text
mutate : (Snapshot, ProfileModel, depth: float, seed: uint32, target_pad_ids: Set<pad_id> = {}) → MutationCandidate
```

| Input | Type | Constraints |
| --- | --- | --- |
| `snapshot` | `Snapshot` | `pads` sorted ascending by `pad_id`; no duplicates. |
| `profile` | `ProfileModel` | Every `pad_mappings[i].trait` must exist in `traits`. |
| `depth` | IEEE-754 double | `0.10 ≤ depth ≤ 0.90` (UI-snapped range). |
| `seed` | uint32 | Any 32-bit unsigned value. `0` is a documented special case (see §3). |
| `target_pad_ids` | set of uint8 | Optional explicit include-list in `1..12`. Empty means all snapshot pads, preserving the original behavior. |

Every dataclass field used by the engine is round-trip-serializable; see `rytm_randomizer/cockpit/data/`.

---

## 2. Outputs

The engine produces a `MutationCandidate` with:

| Field | Computed by |
| --- | --- |
| `candidate_id` | Fresh ULID (the **only** non-deterministic field; conformance fixtures **exclude** it from byte-equality). |
| `source_snapshot_id` | Copied from `snapshot.snapshot_id`. |
| `profile_id` | Copied from `profile.profile_id`. |
| `depth` | Copied from input. |
| `seed` | Copied from input (the raw value the caller passed — the engine's internal PRNG normalisation in §3 is invisible). |
| `pad_deltas` | One `PadDelta` per targeted pad, or per snapshot pad when the include-list is empty, in `pad_id` order; see §6. |
| `safety_status` | Derived from `depth`; see §7. |
| `estimated_midi_msgs` | Sum of `len(pd.changed_keys)` across all pad deltas. |

---

## 3. PRNG — xorshift32

**Algorithm:** xorshift32 (Marsaglia 2003, "Xorshift RNGs", *Journal of Statistical Software*).

**State:** one `uint32_t`. Never zero — zero is a fixed point of the shift sequence.

**Reference Python source** (also valid C if the implicit masks are made explicit):

```python
def xorshift32(state: int) -> tuple[int, int]:
    state ^= (state << 13) & 0xFFFFFFFF
    state ^= state >> 17
    state ^= (state << 5) & 0xFFFFFFFF
    return state & 0xFFFFFFFF, state & 0xFFFFFFFF
```

**Equivalent C99:**

```c
uint32_t xorshift32(uint32_t *state) {
    uint32_t s = *state;
    s ^= s << 13;
    s ^= s >> 17;
    s ^= s << 5;
    *state = s;
    return s;
}
```

**Seed normalisation.** If the caller passes `seed == 0`, the engine substitutes `0x12345678` before the first call (a literal, no entropy needed; the value is documented and locked). Non-zero seeds pass through unchanged after a `& 0xFFFFFFFF` mask. If after masking the value is still zero (the caller passed a multiple of `2**32`), the substitute applies.

**PRNG warm-up.** After normalisation, the engine discards the first **8** xorshift32 outputs before sampling for the algorithm. Small seeds (e.g. `1`, `7`, `42`) produce xorshift32 states whose first 1–2 outputs are dominated by low-order bits, yielding `r` values in `[0.0, 0.02)` and biasing the first delta heavily negative. The 8-step warm-up mixes the state. The C port **must** discard the same number of outputs before its first sampled draw.

**Reference sequence for seed=1 (first 10 outputs):**

```
iter 0: 270369
iter 1: 67634689
iter 2: 2647435461
iter 3: 307599695
iter 4: 2398689233
iter 5: 745495504
iter 6: 632435482
iter 7: 435756210
iter 8: 2005365029
iter 9: 2916098932
```

Locked by `tests/cockpit/test_engine_prng.py::test_xorshift32_known_sequence_seed_1`.

---

## 4. Iteration order

Determinism requires every reference implementation to traverse the inputs in the **same** order. Two ordering rules apply:

1. **Pad iteration order:** ascending by `pad_id`. The Python implementation calls `sorted(snapshot.pads, key=lambda p: p.pad_id)` defensively; the data model already enforces the order at construction, but the explicit sort survives any future contract loosening.
2. **Parameter iteration order:** ascending by key (lexicographic Unicode-codepoint comparison, the natural Python `sorted()` order for `str`). The C-port author must iterate a sorted key array.

Within each pad, **one** `xorshift32` value is drawn per parameter. The PRNG state threads through the entire candidate — every draw uses the state left behind by the previous draw. There is no per-pad re-seeding.

Target filtering happens **after** every pad's parameter draws are consumed.
An untargeted pad is omitted from `pad_deltas` and from
`estimated_midi_msgs`, but it advances the PRNG exactly as it would in the
default all-pad call. Therefore a selected pad's proposed values are identical
for the same snapshot/profile/depth/seed regardless of which neighboring pads
are included.

---

## 5. Per-pad bias

The bias multiplier captures how strongly the active profile pulls the pad toward its style. It is computed once per pad, before any PRNG draws:

```text
total_weight = Σ { weight | (trait, pid, weight) ∈ profile.pad_mappings, pid == pad.pad_id }
weighted_sum = Σ { trait_value(t) * weight | (t, pid, weight) ∈ profile.pad_mappings, pid == pad.pad_id }
bias         = 0.0                                          if total_weight == 0.0
             = weighted_sum / max(total_weight, 0.001)      otherwise
```

`trait_value(t)` is `traits[i].value` for the unique `i` such that `traits[i].name == t`. The data model's `ProfileModel.__post_init__` already enforces that every mapping's trait name exists in `traits`, so the lookup is total.

`bias` lies in `[0.0, 1.0]` (each `trait.value` ∈ `[0,1]` and each `weight` ∈ `[0,1]`).

---

## 6. Per-parameter delta

For each parameter `key` in `sorted(pad.params)`:

```text
raw, state = xorshift32(state)
r          = raw / 2^32                         # half-open [0.0, 1.0)
scale      = depth * 127.0 * (0.5 + bias)       # scaled by depth and bias
delta      = (r - 0.5) * 2.0 * scale
new_value  = clamp(0, current + round_half_away_from_zero(delta), 127)
```

* **Float type:** IEEE-754 double precision (Python `float`, C `double`). The reordering of operations matters — the spec'd expression `(r - 0.5) * 2.0 * scale` avoids `r * 2 * scale - scale` (which can lose precision when `scale` dominates).
* **Rounding:** `round_half_away_from_zero` (C's `round()` behavior, NOT Python's banker's rounding). The Python implementation provides this explicitly because `round(0.5) == 0` in Python but `1` in C. See §6a "Rounding & Negative Zero" for the boundary contract and IEEE-754 caveats that govern every reference implementation.
* **Clamping:** standard min/max to `[0, 127]`.

---

## 6a. Rounding & Negative Zero

The half-away-from-zero rounding helper is small but **load-bearing**: it is the single point where IEEE-754 sign quirks can fork the byte output between language ports. The contract below is normative; pinned by `tests/cockpit/test_engine_conformance_edge_cases.py`.

### Python reference (the canonical implementation)

```python
def _round_half_away_from_zero(value: float) -> int:
    if value >= 0.0:
        return int(value + 0.5)
    return -int(-value + 0.5)
```

The branch predicate is **`value >= 0.0`**, NOT a "sign bit" check. This is deliberate.

### IEEE-754 negative zero

Negative zero (`-0.0`) is a distinct IEEE-754 bit pattern from positive zero (`+0.0`), but the two are equal under `==` and `>=`. In every reference language we care about:

| Predicate | Returns for `-0.0` | Returns for `+0.0` |
| --- | --- | --- |
| `value == 0.0` | `true` | `true` |
| `value >= 0.0` | `true` | `true` |
| `value > 0.0` | `false` | `false` |
| `signbit(value)` / `is_sign_negative` | `true` | `false` |
| `is_sign_positive` (Rust `f64`) | **`false`** | `true` |

The helper's branch predicate is `value >= 0.0`, so `-0.0` takes the **positive** branch:

* `_round_half_away_from_zero(-0.0)` → `int(-0.0 + 0.5)` → `int(0.5)` → `0`.
* `_round_half_away_from_zero(+0.0)` → `int(0.0 + 0.5)` → `int(0.5)` → `0`.

Both zeros round to integer `0`. Good.

### The Rust gotcha (**read this**)

Rust's `f64::is_sign_positive` returns `false` for `-0.0`. A port that writes

```rust
// WRONG — diverges from the Python reference on -0.0 and ALL of (-0.5, 0.0).
fn round_half_away_from_zero(value: f64) -> i32 {
    if value.is_sign_positive() {
        (value + 0.5) as i32
    } else {
        -((-value + 0.5) as i32)
    }
}
```

…will take the **negative** branch for `-0.0` (still returns 0 by coincidence) and for every value in `(-0.5, 0.0)` (returns 0 there too, so the bug stays latent until someone supplies `-0.0` via the inverse cosine of `1.0` or any other operation that materializes the negative zero — then the byte-equality with Python/C breaks).

**Always use `value >= 0.0` as the branch predicate.** Python, C, and Rust all evaluate `(-0.0) >= 0.0` as `true`; that's the semantic the reference implementation depends on.

### Worked boundary examples

| Input | Python branch | Result | Notes |
| --- | --- | --- | --- |
| `+0.0` | `value >= 0.0` ⇒ positive | `int(0.0 + 0.5)` ⇒ `0` | Trivial. |
| `-0.0` | `value >= 0.0` ⇒ positive (Python/C/Rust all agree under `>=`) | `int(-0.0 + 0.5)` ⇒ `int(0.5)` ⇒ `0` | Diverges from `is_sign_positive`-based Rust. |
| `+0.5` | positive | `int(0.5 + 0.5)` ⇒ `1` | Ties round AWAY from zero. C's `round(0.5)` is `1`. Python's built-in `round(0.5)` is `0` (banker's) — we deliberately disagree. |
| `-0.5` | `value >= 0.0` ⇒ false ⇒ negative branch | `-int(0.5 + 0.5)` ⇒ `-int(1.0)` ⇒ `-1` | Ties round AWAY from zero. C's `round(-0.5)` is `-1`. Python's built-in `round(-0.5)` is `0` — again, we disagree. |
| `+1.5` | positive | `int(1.5 + 0.5)` ⇒ `2` |  |
| `-1.5` | negative | `-int(1.5 + 0.5)` ⇒ `-2` |  |
| `+2.5` | positive | `int(2.5 + 0.5)` ⇒ `3` | Banker's would give `2`. |
| `-2.5` | negative | `-int(2.5 + 0.5)` ⇒ `-3` | Banker's would give `-2`. |

### C99 reference implementation

```c
#include <stdint.h>
#include <math.h>  /* round() also works, but spelling it out is clearer for portability. */

int32_t round_half_away_from_zero(double value) {
    if (value >= 0.0) {
        return (int32_t)(value + 0.5);
    } else {
        return -(int32_t)(-value + 0.5);
    }
}
```

C's `(int)` cast truncates toward zero, so `(int)(0.5 + 0.5) == 1` and `(int)(-0.5 + 0.5) == 0`. C99 `round()` from `<math.h>` already implements round-half-away-from-zero and is allowable as a drop-in if the port author confirms the platform libm respects C99 semantics (most do; embedded toolchains sometimes don't — use the explicit form above to be safe).

### Rust reference implementation

```rust
pub fn round_half_away_from_zero(value: f64) -> i32 {
    // Branch on `value >= 0.0`, NOT `value.is_sign_positive()`.
    // `(-0.0) >= 0.0` is `true` in Rust; `(-0.0).is_sign_positive()` is `false`.
    // The former matches the Python and C reference implementations bit-for-bit.
    if value >= 0.0 {
        (value + 0.5) as i32
    } else {
        -((-value + 0.5) as i32)
    }
}
```

Rust's `as i32` truncates toward zero just like C's `(int)` cast, so the formulas are line-for-line equivalent across the three languages.

### Reachability through the engine PRNG path

For completeness: the cockpit engine's PRNG (`xorshift32` from a non-zero state) cannot produce `raw == 0`, so `r = raw / 2^32` lies strictly in `(0.0, 1.0)`. Consequently `(r - 0.5) * 2.0` is in `(-1.0, 1.0)` — neither `-0.5` nor `-0.0` is reachable at the unit level — and with the smallest realistic `scale ≈ 6.35` the product `(r - 0.5) * 2.0 * scale` has magnitude ≥ `2^-28`, far above the subnormal-underflow threshold that would be required to materialize `-0.0`. The helper still must handle these boundary inputs correctly because a future spec extension (or a unit-test driving the helper directly) can supply them; the table-driven test pins the contract regardless of which inputs the engine itself can reach. See `tests/cockpit/test_engine_conformance_edge_cases.py::test_mutate_reaches_negative_zero_via_prng`.

**Result rules:**

* Every `key` in `pad.params` appears in `pad_delta.proposed_params` (whether changed or not). The dictionary preserves the full pad state so the device adapter does not need to re-merge with the snapshot.
* Only keys where `new_value != value` appear in `pad_delta.changed_keys`. The cardinality of `changed_keys` summed across pads becomes `estimated_midi_msgs`.

---

## 7. Safety status

After the per-pad loop completes, the candidate's `safety_status` is derived from `depth` alone:

| Depth range | Status |
| --- | --- |
| `depth < 0.30` | `"safe"` |
| `0.30 ≤ depth < 0.65` | `"armed"` |
| `depth ≥ 0.65` | `"high_risk"` |

The thresholds are exclusive at the lower bound and inclusive at the upper bound of the previous category (canonical half-open intervals).

---

## 8. Worked example

**Inputs:**

* `snapshot.snapshot_id = "SNAP1"`, two pads:
  * `PadState(pad_id=1, machine="bd_classic", params={"tun": 60, "dec": 40})`
  * `PadState(pad_id=2, machine="sd_classic", params={"tun": 50, "dec": 80})`
* `profile.profile_id = "PROF1"`, two traits:
  * `StyleTrait("low_end", 0.8)`, `StyleTrait("texture", 0.3)`
  * `pad_mappings`:
    * `TraitPadWeight("low_end", 1, 0.9)`
    * `TraitPadWeight("texture", 2, 0.5)`
* `depth = 0.5`
* `seed = 42`

**Step-by-step trace:**

1. **PRNG seed:** `42` is non-zero, mask to `42`, use directly.
2. **Pad 1 (pad_id=1):**
   * Bias: only `(low_end, 1, 0.9)` matches → `weighted_sum = 0.8 * 0.9 = 0.72`, `total_weight = 0.9`. `bias = 0.72 / 0.9 = 0.8`.
   * `scale = 0.5 * 127 * (0.5 + 0.8) = 82.55`.
   * Sorted keys: `["dec", "tun"]`.
   * `"dec"`: draw `(value=raw_0, state=raw_0)` from `xorshift32(42)`; compute `r`, `delta`, `new_value`.
   * `"tun"`: draw `(value=raw_1, state=raw_1)` from `xorshift32(raw_0)`.
3. **Pad 2 (pad_id=2):**
   * Bias: only `(texture, 2, 0.5)` matches → `weighted_sum = 0.3 * 0.5 = 0.15`, `total_weight = 0.5`. `bias = 0.15 / 0.5 = 0.3`.
   * `scale = 0.5 * 127 * (0.5 + 0.3) = 50.8`.
   * Sorted keys: `["dec", "tun"]`. Two more `xorshift32` draws.
4. **Safety status:** `depth = 0.5`, falls in `[0.30, 0.65)` → `"armed"`.
5. **estimated_midi_msgs:** sum of `len(changed_keys)` across the two pads.

The exact numeric output for this example is captured in
`tests/cockpit/fixtures/engine_conformance/worked_example_seed42_depth050.json`
and is byte-locked. Any reference implementation must reproduce
`pad_deltas` exactly.

---

## 9. Conformance corpus

The Python implementation generates `tests/cockpit/fixtures/engine_conformance/*.json` programmatically at test-authoring time (see `tests/cockpit/test_engine_conformance.py`'s generator) and the files are committed. The C99 / Rust port loads every fixture and asserts byte-equal `MutationCandidate.to_dict()` output (excluding `candidate_id`, which is non-deterministic by design).

**Fixture format** (one file per case):

```json
{
  "name": "<descriptive case name>",
  "snapshot": { ... full Snapshot.to_dict ... },
  "profile":  { ... full ProfileModel.to_dict ... },
  "depth":    0.5,
  "seed":     42,
  "expected": {
    "source_snapshot_id": "...",
    "profile_id":         "...",
    "depth":              0.5,
    "seed":               42,
    "pad_deltas":         [ ... ],
    "safety_status":      "armed",
    "estimated_midi_msgs": 3
  }
}
```

Note the `expected` object excludes `candidate_id`. Implementations populate that field with a fresh ULID per call and the conformance test compares the rest.

---

## 10. Non-goals (what this spec does NOT define)

* **Streaming / progressive mutation.** `ProfileModel.transition_curve` is reserved for the Phase 2 progressive-mutation extension; today the engine produces a single-shot candidate (equivalent to `transition_curve="linear"`).
* **Locked pads.** The cockpit applies pad-lock semantics at the device adapter (WS-F), not in the mutation engine — a locked pad still gets a `PadDelta`; the device adapter chooses to ignore it.
* **Multiple candidates (REGEN).** REGEN is implemented at the WS-E command-handler layer: it calls `mutate(...)` again with a fresh seed. The engine itself is single-call.
* **The `candidate_id` field.** A fresh ULID is the engine's only non-deterministic output, intentionally excluded from conformance comparison.

---

## 11. Cross-references

* `rytm_randomizer/cockpit/engine/mutate.py` — Python reference implementation.
* `rytm_randomizer/cockpit/engine/prng.py` — Python xorshift32 implementation.
* `tests/cockpit/test_engine_prng.py` — locks the PRNG reference sequence.
* `tests/cockpit/test_engine_mutate.py` — determinism, variance, scaling, clamping tests.
* `tests/cockpit/test_engine_conformance.py` — drives the JSON fixture corpus.
* `tests/cockpit/test_engine_conformance_edge_cases.py` — pins the §6a rounding contract (±0.0, ±0.5, table-driven boundary matrix) and the P6 defensive-sort guards.
* `tests/cockpit/fixtures/engine_conformance/*.json` — the byte-frozen reference output.
* `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md` — parent design doc.
