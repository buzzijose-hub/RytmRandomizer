"""Architecture-conformance tests.

The tests in this package mechanically enforce the rules documented in
``docs/ARCHITECTURE.md`` (the canonical human-readable architecture standard)
and ``.claude/rules/architecture.md`` (the agent-facing distillation).

If a test in this package fails, the architecture has been eroded: either
* a module was added that violates a layer-direction rule,
* a house-style rule (frozen dataclass, type hints, no mutable global) was
  broken,
* an I/O side effect was introduced at module import time,
* ``mido`` was imported eagerly somewhere it should be lazy,
* a fact table was defined outside ``rytm_randomizer/data/`` or redefined,
* the expected package layout was changed.

The package layout itself ensures that ``pytest tests/architecture/`` runs all
of these tests as a single gated check. The CI workflow under
``.github/workflows/test.yml`` runs them alongside the full suite.
"""
