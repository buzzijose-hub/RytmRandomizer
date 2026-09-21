"""Drift guard — every config-dir JSON writer registers a ``schema_version``.

Spec §11 Contract A (``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md``)
makes exactly one demand of a feature author who adds persisted operator
state: **declare your schema_version in the registry.** The update system
then swaps the binary underneath that state without eating it.

A contract enforced by review vigilance is a contract that lasts until
the first busy week. So this module mechanizes it. The check is
structural, not behavioral:

  A package module that **serialises JSON**, **commits bytes to disk**,
  and reaches a **platform config-dir path** — either by resolving one
  itself or by defining a class the boot wiring hands one to — is
  persisting operator state under the config dir, and must appear in
  :data:`rytm_randomizer.data.persisted_state.PERSISTED_STATE_STORES`
  as some store's ``owner_module`` — or in the drainable legacy
  allowlist below, whose documented goal is **empty**.

Why JSON and write are both required
====================================

Neither signal alone works. Resolving a config dir alone catches the
boot wiring in ``cockpit/__main__.py``, which merely *hands* directories
to the stores and persists nothing itself. Writing JSON alone catches
sixty-odd report and export modules that write to an operator-supplied
``--output`` path, which the update system does not own and must not
claim to. And config-dir + JSON without a *write* catches the read-only
rehearsal report, which resolves the profiles dir only to mirror the
cockpit's default. Together they name exactly "this module keeps state
in the place the installer will swap around".

Why config-dir reach needs two detection paths
==============================================

The two stores that exist today reach the config dir by *different*
mechanisms, and a guard that understood only one of them would have
shipped with a hole in it:

* ``cockpit/library/store.py`` calls ``default_library_dir()`` itself.
* ``cockpit/profiles/registry.py`` calls **nothing** — ``ProfileRegistry``
  takes an injected ``Path``, and ``cockpit/__main__.py`` supplies
  ``default_profiles_dir()`` at composition time.

Dependency injection is the *better* of the two shapes and the one this
repo prefers, so the guard must not be blind to it. It therefore also
reads the boot module and treats any class constructed there with a
config-dir helper's result as a config-dir store — see
:func:`_boot_wired_store_classes`. A future store copying the registry's
shape is caught; a one-path guard would have waved it through.

Test inventory (the three-test ratchet this repo uses for allowlists —
mirrors ``test_no_unreferenced_top_level_symbols.py``):

1. :func:`test_every_config_dir_json_writer_is_registered` — the floor.
   A new unregistered writer turns this red.
2. :func:`test_legacy_writer_allowlist_has_no_ghosts` — an allowlist
   entry whose file is gone must be pruned.
3. :func:`test_legacy_writer_allowlist_has_no_registered_entries` — an
   entry that has since registered must be removed, so the list only
   shrinks.

Plus :func:`test_both_detection_paths_are_live` — a scan that detects
*nothing* would satisfy test 1 vacuously forever, so both paths are
pinned against the store each one exists to catch. Plus registry
self-consistency checks: owner modules resolve to real files, migration
chains are contiguous, ids are unique and path-free, and the registry's
code vocabulary matches the metrics label vocabulary (so a refusal can
always be counted).

**Mutation-proved.** Both detection paths were observed failing before
being trusted — see :func:`test_both_detection_paths_are_live` for the
recorded procedure and results. A drift guard that has never been
observed red is not a guard.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.data.persisted_state import (
    PERSISTED_STATE_CODES,
    PERSISTED_STATE_STORES,
    PERSISTED_STATE_VERSION_FIELD,
    PersistedStateMigration,
    PersistedStateStore,
    classify_payload,
    current_schema_version,
    registered_store,
    registered_store_ids,
    require_schema_version,
)
from rytm_randomizer.observability.metrics import get_metrics, reset_metrics

# WS-M4 convention: architecture checks belong to the fast suite.
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME: Final[str] = "rytm_randomizer"


# ---------------------------------------------------------------------------
# The AST signals.
# ---------------------------------------------------------------------------

_CONFIG_DIR_RESOLVERS: Final[frozenset[str]] = frozenset(
    {
        # The per-platform config-dir helpers in the package. A new one
        # must be added here in the same PR that introduces it —
        # otherwise its callers become invisible to this guard.
        "default_profiles_dir",
        "default_library_dir",
        "default_captures_dir",
        "default_export_dir",
    }
)
"""Function names whose call means "this module resolved the config dir"."""

_BOOT_WIRING_MODULE: Final[str] = "rytm_randomizer/cockpit/__main__.py"
"""Repo-relative path of the module that composes the cockpit's stores.

The second detection path (see :func:`_boot_wired_store_classes`) reads
it. Constructing a class here with a config-dir helper's result as an
argument is what makes that class a config-dir store, even though the
class's own module never names a directory. If the boot path is ever
split or renamed, update this constant in the same PR — otherwise the
injected-store detection goes dark, which
:func:`test_both_detection_paths_are_live` turns red.
"""

_JSON_SERIALISERS: Final[frozenset[str]] = frozenset({"dump", "dumps"})
"""``json.<name>`` calls that mean "this module serialises JSON"."""

_WRITE_CALLS: Final[frozenset[str]] = frozenset(
    {
        # The package's sanctioned durable-write helpers.
        "atomic_write",
        "atomic_write_set",
        # Raw stdlib writes, in case a future store bypasses the helper.
        "write_bytes",
        "write_text",
    }
)
"""Call names that mean "this module actually commits bytes to disk".

The third signal, and the one that separates a *store* from a *reader*.
``reports/cockpit_export_rehearsal.py`` resolves ``default_profiles_dir()``
to mirror the cockpit's default and ``json.dumps`` its findings to
stdout — it reads operator state and persists none, so the update system
owns nothing of its behaviour. Without this signal the guard flagged it,
and allowlisting it would have taught the next contributor that the
allowlist is where you put things the rule does not really mean.
"""


def _package_modules() -> list[Path]:
    """Every ``.py`` file under the package, sorted for stable failures."""

    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _dotted_name(path: Path) -> str:
    """``rytm_randomizer/cockpit/library/store.py`` -> the dotted module path."""

    relative = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _called_name(func: ast.expr) -> str | None:
    """The bare callee name for ``f()`` and ``obj.f()``; ``None`` otherwise."""

    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _module_signals(path: Path) -> tuple[bool, bool, bool]:
    """``(resolves_config_dir, serialises_json, commits_bytes)`` for one module.

    Purely syntactic: it reads call names, not dataflow. That makes it
    cheap and stable, and it errs toward flagging — a module hitting the
    signals for unrelated reasons must either register or be allowlisted
    with a note, which is the safe direction for a fail-closed contract.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    resolves_config_dir = False
    serialises_json = False
    commits_bytes = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _called_name(node.func)
        if name is None:
            continue
        if name in _CONFIG_DIR_RESOLVERS:
            resolves_config_dir = True
        elif name in _WRITE_CALLS:
            commits_bytes = True
        elif (
            name in _JSON_SERIALISERS
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "json"
        ):
            serialises_json = True
    return resolves_config_dir, serialises_json, commits_bytes


def _boot_wired_store_classes() -> frozenset[str]:
    """Class names the boot path constructs *with* a config-dir helper result.

    The second detection path, and the reason this guard catches
    ``cockpit/profiles/registry.py``.

    ``ProfileRegistry`` never names a directory: it takes an injected
    ``Path`` and the boot wiring supplies ``default_profiles_dir()``. A
    resolver-call scan of the registry's own source therefore sees
    nothing, and a future store copying that (entirely correct,
    dependency-injected) shape would slip past a one-path guard
    silently — the worst possible failure for a fail-closed contract.

    So the scan also reads the boot module and collects every class
    instantiated there with a config-dir helper's result as a positional
    or keyword argument. Those classes' defining modules are config-dir
    stores by construction, whatever their own source says.
    """

    boot_path = PROJECT_ROOT / _BOOT_WIRING_MODULE
    assert boot_path.is_file(), (
        f"the boot wiring module {_BOOT_WIRING_MODULE} is missing — the "
        "injected-store detection path cannot run; update _BOOT_WIRING_MODULE "
        "if the boot path moved"
    )
    tree = ast.parse(boot_path.read_text(encoding="utf-8"), filename=str(boot_path))
    wired: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        constructed = _called_name(node.func)
        # A class, by convention: CamelCase. Filters out the helper calls
        # themselves and every lowercase function call in the boot path.
        if constructed is None or not constructed[:1].isupper():
            continue
        arguments = list(node.args) + [keyword.value for keyword in node.keywords]
        for argument in arguments:
            if isinstance(argument, ast.Call) and _called_name(argument.func) in (
                _CONFIG_DIR_RESOLVERS
            ):
                wired.add(constructed)
                break
    return frozenset(wired)


def _defines_a_boot_wired_store(path: Path, wired_classes: frozenset[str]) -> bool:
    """True when ``path`` defines one of the boot-wired store classes."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, ast.ClassDef) and node.name in wired_classes
        for node in ast.iter_child_nodes(tree)
    )


def _writes_json_into_config_dir(path: Path, wired_classes: frozenset[str]) -> bool:
    """True when ``path`` persists JSON operator state under the config dir.

    Two detection paths, either of which is sufficient — a store may
    reach the config dir directly or have it injected:

    1. **Direct.** The module resolves a config-dir helper itself, AND
       serialises JSON, AND commits bytes to disk. This catches
       ``cockpit/library/store.py``.
    2. **Injected.** The module defines a class the boot path constructs
       with a config-dir helper's result, AND serialises JSON, AND
       commits bytes. This catches ``cockpit/profiles/registry.py``.

    In both paths the JSON + write signals are required, which is what
    separates a *store* from a *reader* or a *router*. Without the write
    signal the guard flags ``reports/cockpit_export_rehearsal.py``, which
    resolves the profiles dir only to mirror the cockpit's default and
    serialises its findings to stdout — allowlisting that would have
    taught the next contributor that the allowlist is where you put
    things the rule does not really mean. Without the config-dir signal
    it flags sixty-odd export modules writing to an operator-supplied
    ``--output`` path, which the update system does not own.
    """

    resolves_config_dir, serialises_json, commits_bytes = _module_signals(path)
    if not (serialises_json and commits_bytes):
        return False
    return resolves_config_dir or _defines_a_boot_wired_store(path, wired_classes)


# ---------------------------------------------------------------------------
# The drainable legacy allowlist. GOAL: EMPTY.
# ---------------------------------------------------------------------------
#
# An entry here is a module that writes JSON under the config dir WITHOUT
# declaring a schema_version — i.e. state the update system cannot
# promise to preserve. Adding an entry requires explicit reviewer
# approval recorded in the PR body (the standing rule for every drained
# allowlist in this repo); removing one requires only that the module
# register. The direction is one-way: this set shrinks.
#
# It is EMPTY at the time this guard landed — every config-dir JSON
# writer in the tree registered in the same change. Keep it that way.

_LEGACY_UNREGISTERED_WRITERS: Final[frozenset[str]] = frozenset()
"""Modules grandfathered without a ``schema_version``. Goal: empty."""


def _registered_owner_modules() -> frozenset[str]:
    """Dotted owner-module paths named by the registry."""

    return frozenset(store.owner_module for store in PERSISTED_STATE_STORES.values())


def _detected_config_dir_writers() -> frozenset[str]:
    """Every package module the AST scan flags as a config-dir JSON writer."""

    wired_classes = _boot_wired_store_classes()
    return frozenset(
        _dotted_name(path)
        for path in _package_modules()
        if _writes_json_into_config_dir(path, wired_classes)
    )


# ---------------------------------------------------------------------------
# Test 1 — the floor.
# ---------------------------------------------------------------------------


def test_every_config_dir_json_writer_is_registered() -> None:
    """A module persisting JSON under the config dir must declare a version."""

    unregistered = sorted(
        _detected_config_dir_writers() - _registered_owner_modules() - _LEGACY_UNREGISTERED_WRITERS
    )
    assert not unregistered, (
        "These modules write JSON under the platform config dir but declare no "
        "schema_version, so an app update cannot promise to preserve the state "
        "they persist (spec §11 Contract A). Register each one in "
        "rytm_randomizer/data/persisted_state.py (PERSISTED_STATE_STORES) and "
        "route its loads through classify_payload(); see "
        ".claude/rules/update-compatibility.md. Offenders:\n  " + "\n  ".join(unregistered)
    )


# ---------------------------------------------------------------------------
# Tests 2 and 3 — the allowlist may only shrink.
# ---------------------------------------------------------------------------


def test_legacy_writer_allowlist_has_no_ghosts() -> None:
    """Every allowlisted module must still exist and still be a writer."""

    detected = _detected_config_dir_writers()
    ghosts = sorted(_LEGACY_UNREGISTERED_WRITERS - detected)
    assert not ghosts, (
        "These allowlist entries are stale — the module no longer exists, was "
        "renamed, or no longer writes JSON under the config dir. Remove them "
        "so the allowlist cannot harbour ghosts:\n  " + "\n  ".join(ghosts)
    )


def test_legacy_writer_allowlist_has_no_registered_entries() -> None:
    """An allowlisted module that has since registered must leave the list."""

    redundant = sorted(_LEGACY_UNREGISTERED_WRITERS & _registered_owner_modules())
    assert not redundant, (
        "These modules are BOTH allowlisted as legacy AND registered with a "
        "schema_version. The grandfather entry is now redundant — delete it so "
        "the allowlist keeps shrinking:\n  " + "\n  ".join(redundant)
    )


# ---------------------------------------------------------------------------
# Anti-vacuity — the scan must actually detect the stores it exists for.
# ---------------------------------------------------------------------------


def test_both_detection_paths_are_live() -> None:
    """The scan detects both store shapes, so test 1 cannot pass vacuously.

    Test 1 asserts ``detected - registered == set()``. A scan that
    detected nothing at all would satisfy it forever while catching no
    drift whatsoever — the classic silently-dead guard. This test pins
    the floor from the other side: each of the two detection paths must
    still find the store it was written for.

    Path 1 (direct resolution) is pinned by the library store, which
    calls ``default_library_dir()`` in its own module. Path 2 (boot-wired
    injection) is pinned by the profile registry, which calls no resolver
    and is only reachable through ``cockpit/__main__.py``'s
    ``ProfileRegistry(default_profiles_dir())``.

    **Mutation proof, both paths, recorded 2026-09-07:**

    * *Path 1.* A probe module ``rytm_randomizer/cockpit/_drift_probe_store.py``
      calling ``default_profiles_dir()``, ``json.dumps(...)`` and
      ``atomic_write(...)`` was added.
      :func:`test_every_config_dir_json_writer_is_registered` failed,
      naming ``rytm_randomizer.cockpit._drift_probe_store``. Deleting the
      probe returned it to green.
    * *Path 2.* Deleting the ``_defines_a_boot_wired_store`` clause from
      :func:`_writes_json_into_config_dir` made *this* test fail on the
      profile-registry assertion — proving the injected path is load
      bearing and not decoration. Restoring it returned it to green.
    """

    detected = _detected_config_dir_writers()
    assert "rytm_randomizer.cockpit.library.store" in detected, (
        "Detection path 1 (a module resolving a config-dir helper itself) went "
        "dark — the library store is no longer detected, so the guard would "
        "wave through any new store of that shape."
    )
    assert "rytm_randomizer.cockpit.profiles.registry" in detected, (
        "Detection path 2 (a store class the boot path hands a config dir) went "
        "dark — the profile registry is no longer detected. Any new store using "
        "dependency injection, the shape this repo prefers, would slip past."
    )


# ---------------------------------------------------------------------------
# Registry self-consistency.
# ---------------------------------------------------------------------------


def test_registry_is_not_empty() -> None:
    """The registry must name at least the stores that exist today."""

    assert registered_store_ids(), "PERSISTED_STATE_STORES must not be empty"


@pytest.mark.parametrize("store_id", sorted(PERSISTED_STATE_STORES))
def test_registered_owner_module_resolves_to_a_real_file(store_id: str) -> None:
    """Each declared ``owner_module`` must be a real module in the package."""

    store = PERSISTED_STATE_STORES[store_id]
    assert store.owner_module.startswith(f"{PACKAGE_NAME}."), (
        f"{store_id}: owner_module must be a rytm_randomizer module, " f"got {store.owner_module!r}"
    )
    relative = Path(*store.owner_module.split("."))
    module_file = PROJECT_ROOT / relative.with_suffix(".py")
    package_file = PROJECT_ROOT / relative / "__init__.py"
    assert (
        module_file.is_file() or package_file.is_file()
    ), f"{store_id}: owner_module {store.owner_module!r} does not resolve to a file"


@pytest.mark.parametrize("store_id", sorted(PERSISTED_STATE_STORES))
def test_store_id_is_its_own_key_and_is_path_free(store_id: str) -> None:
    """Ids are journal/metric labels — never paths, never separators."""

    store = PERSISTED_STATE_STORES[store_id]
    assert store.store_id == store_id, "PERSISTED_STATE_STORES key must match store_id"
    assert store_id and store_id.replace("_", "").isalnum(), (
        f"store id {store_id!r} must be a bare snake_case label (it appears in "
        "journal rows and metric keys — a path would leak the operator's home dir)"
    )


@pytest.mark.parametrize("store_id", sorted(PERSISTED_STATE_STORES))
def test_declared_version_is_reachable_by_the_migration_chain(store_id: str) -> None:
    """The chain must run ``1 -> ... -> schema_version`` with no gaps."""

    store = PERSISTED_STATE_STORES[store_id]
    expected = 1
    for migration in store.migrations:
        assert (
            migration.from_version == expected
        ), f"{store_id}: migration chain has a gap at version {expected}"
        expected = migration.to_version
    assert expected == store.schema_version, (
        f"{store_id}: declares schema_version {store.schema_version} but its "
        f"migration chain reaches {expected}"
    )


def test_registry_codes_cover_the_metrics_refusal_vocabulary() -> None:
    """Every refusal code must have a bounded metrics label available.

    The registry's ``persisted_state.*`` codes and the metrics module's
    :data:`PersistedStateRefusalCode` literals are the same vocabulary
    with the shared prefix stripped. If they drift, a refusal becomes
    uncountable — the Gate 7 floor this guard also protects.
    """

    from rytm_randomizer.observability import metrics as metrics_module

    refusal_labels = set(metrics_module.PersistedStateRefusalCode.__args__)
    registry_refusals = {
        code.removeprefix("persisted_state.")
        for code in PERSISTED_STATE_CODES
        if code not in {"persisted_state.ok", "persisted_state.migrated"}
    }
    assert registry_refusals == refusal_labels, (
        "The persisted-state refusal vocabulary drifted between "
        "data/persisted_state.py and observability/metrics.py. Registry-only: "
        f"{sorted(registry_refusals - refusal_labels)}; metrics-only: "
        f"{sorted(refusal_labels - registry_refusals)}"
    )


# ---------------------------------------------------------------------------
# The store modules actually honour their declaration.
# ---------------------------------------------------------------------------


def test_registered_stores_source_their_version_from_the_registry() -> None:
    """A store's module constant must equal its registry row, not a copy.

    Spec §11 forbids a store re-typing its version: the registry is the
    single declaration, so a bump lands in exactly one place.
    """

    from rytm_randomizer.cockpit.library import store as library_store
    from rytm_randomizer.cockpit.profiles import registry as profile_registry

    assert (
        current_schema_version(library_store.LIBRARY_STORE_ID)
        == library_store.LIBRARY_STORE_SCHEMA_VERSION
    )
    assert (
        current_schema_version(profile_registry.PROFILE_REGISTRY_STORE_ID)
        == profile_registry.PROFILE_REGISTRY_SCHEMA_VERSION
    )


def test_require_schema_version_refuses_an_unregistered_store() -> None:
    """An owner that forgets its registry row fails loudly at import time."""

    with pytest.raises(ValueError, match="not registered"):
        require_schema_version("no_such_store_id")


# ---------------------------------------------------------------------------
# The contract's headline behaviours, asserted at the registry boundary.
# ---------------------------------------------------------------------------


def test_a_file_without_a_version_field_is_treated_as_version_one() -> None:
    """Rule 3: pre-envelope files are v1 state, never corruption."""

    store_id = registered_store_ids()[0]
    decision = classify_payload(store_id, {"anything": 1})
    assert decision.accepted, "a file lacking schema_version must not be refused"
    assert decision.from_version == 1


def test_newer_state_is_refused_rather_than_truncated() -> None:
    """Rule 2: the downgrade-refusal rule, at the registry boundary."""

    store_id = registered_store_ids()[0]
    version = current_schema_version(store_id)
    assert version is not None
    decision = classify_payload(store_id, {PERSISTED_STATE_VERSION_FIELD: version + 1})
    assert decision.code == "persisted_state.schema_newer_than_app"
    assert decision.payload is None, "a refusal must never hand back partial state"


def test_no_refusal_detail_contains_a_filesystem_path() -> None:
    """Gate 7 hygiene: details carry ids, ints, and codes — never paths."""

    store = registered_store(registered_store_ids()[0])
    assert store is not None
    probes = (
        classify_payload("unregistered_store", {}),
        classify_payload(store.store_id, None, readable=False),
        classify_payload(store.store_id, ["not", "a", "mapping"]),
        classify_payload(store.store_id, {PERSISTED_STATE_VERSION_FIELD: "one"}),
        classify_payload(store.store_id, {PERSISTED_STATE_VERSION_FIELD: 99}),
    )
    for decision in probes:
        assert decision.refused, f"{decision.code} should be a refusal"
        rendered = repr(dict(decision.detail))
        assert (
            "/" not in rendered and "\\" not in rendered
        ), f"refusal detail for {decision.code} leaked a path-like string: {rendered}"


def test_metrics_surface_records_migrations_and_refusals() -> None:
    """Gate 7: both counters exist and reach ``format_summary()``."""

    reset_metrics()
    metrics = get_metrics()
    metrics.record_persisted_state_migration("probe_store", 1, 2)
    metrics.record_persisted_state_refusal("probe_store", "schema_newer_than_app")
    summary = metrics.format_summary()
    assert "persisted_state_migrations={probe_store:1->2:1}" in summary
    assert "persisted_state_refusals={probe_store:schema_newer_than_app:1}" in summary
    reset_metrics()
    assert "persisted_state_migrations={}" in get_metrics().format_summary()


def test_a_declared_migration_chain_runs_in_order() -> None:
    """Rule 4: migrations are explicit, ordered, and recorded."""

    store = PersistedStateStore(
        store_id="probe",
        schema_version=3,
        owner_module="rytm_randomizer.data.persisted_state",
        description="probe",
        migrations=(
            PersistedStateMigration(1, lambda p: {**p, "one": True}, "add one"),
            PersistedStateMigration(2, lambda p: {**p, "two": True}, "add two"),
        ),
    )
    from rytm_randomizer.data.persisted_state import apply_migration_plan

    decision = apply_migration_plan(store, {"seed": 1}, from_version=1)
    assert decision.code == "persisted_state.migrated"
    assert decision.steps == ("add one", "add two")
    assert decision.payload == {
        "seed": 1,
        "one": True,
        "two": True,
        PERSISTED_STATE_VERSION_FIELD: 3,
    }
