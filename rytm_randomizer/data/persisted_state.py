"""Persisted-state registry — spec §11 Contract A (auto-update change resilience).

WHAT
====

The single fact table naming every module that writes **operator state**
into the platform config dir, together with the ``schema_version`` that
module currently writes. Registering here is the *entire* interface
between a new feature and the auto-update system: declare your version,
and the binary can swap underneath your state without eating it.

The module also owns the pure **load policy** every registered store
routes its on-disk payload through:

* :func:`classify_payload` — decides, without touching the filesystem
  and without raising, what a loader should do with one decoded payload.
* :func:`plan_migration` — resolves the explicit, ordered migration
  chain from the on-disk version to the app's current version.
* :func:`apply_migration_plan` — runs that chain, recording each step so
  the caller can journal it.

WHY IT IS SHAPED THIS WAY
=========================

``rytm_randomizer/data/`` is a **strict leaf** — it may import stdlib and
sibling ``data`` modules and nothing else
(``tests/architecture/test_import_direction.py``
``test_data_layer_does_not_import_from_package``). That rules out
importing the taxonomy errors in
:mod:`rytm_randomizer.observability.errors` or the counters in
:mod:`rytm_randomizer.observability.metrics` from here.

So this module is **decision-returning, not exception-raising**: every
policy function returns a frozen :class:`PersistedStateDecision` carrying
a bounded taxonomy ``code`` from :data:`PERSISTED_STATE_CODES` (the spec
§5.1 vocabulary — ``persisted_state.schema_newer_than_app``,
``persisted_state.migration_failed``, …). The *caller* — which lives
above the leaf boundary and may import ``observability`` freely — turns a
refusing decision into a taxonomy error and a
``get_metrics().record_persisted_state_refusal(...)`` /
``record_persisted_state_migration(...)`` increment.

That split is deliberate and is the only shape that satisfies the leaf
rule, the ``raise``-taxonomy rule, and Gate 7 simultaneously. It also
makes the policy exhaustively unit-testable with zero I/O.

THE RULES (all fail-closed, spec §11 Contract A)
================================================

1. **Never silently reset.** An unreadable file, an unknown shape, or a
   failed migration produces a *refusal* — the operator is told, the
   bytes on disk are left alone. A show bank outliving an update is a
   product promise.
2. **Downgrade refusal.** A payload whose ``schema_version`` is NEWER
   than the app's registered version is refused with
   ``persisted_state.schema_newer_than_app``. An operator who tried a
   newer build and rolled back must not have their state truncated to
   whatever the older app understands.
3. **A missing version field means version 1**, not corruption. Files
   written before a store adopted the envelope are legitimate v1 state
   and must migrate forward, never be discarded.
4. **Migrations are explicit and ordered.** A store declares one
   :class:`PersistedStateMigration` per ``from_version -> from_version+1``
   step; there are no implicit or skipped steps, and the chain is
   validated at registration time.
5. **No absolute paths in any emitted detail.** Details carry the store
   id, integers, and bounded codes only — the #224/#238 hygiene standard.

REFERENCES
==========

* ``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`` §11
  (Contract A) and §5.1 (the taxonomy code vocabulary).
* ``.claude/rules/update-compatibility.md`` — the developer contract.
* ``tests/architecture/test_persisted_state_registry.py`` — the drift
  guard that fails when a new config-dir writer forgets to register.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

__all__ = [
    "PERSISTED_STATE_CODES",
    "PERSISTED_STATE_STORES",
    "PERSISTED_STATE_VERSION_FIELD",
    "PersistedStateCode",
    "PersistedStateDecision",
    "PersistedStateMigration",
    "PersistedStateMigrationFn",
    "PersistedStateStore",
    "apply_migration_plan",
    "classify_payload",
    "current_schema_version",
    "plan_migration",
    "read_schema_version",
    "registered_store",
    "registered_store_ids",
    "require_schema_version",
]


PERSISTED_STATE_VERSION_FIELD: Final[str] = "schema_version"
"""Envelope key every persisted operator-state payload carries."""

_IMPLICIT_FIRST_VERSION: Final[int] = 1
"""Version assumed for a payload that predates the envelope (rule 3).

A file written before its store adopted ``schema_version`` is genuine
version-1 state, not a corrupt file — treating it as corrupt would reset
exactly the operator state this contract exists to preserve.
"""


PersistedStateCode: TypeAlias = Literal[
    "persisted_state.ok",
    "persisted_state.migrated",
    "persisted_state.unreadable",
    "persisted_state.unknown_shape",
    "persisted_state.unknown_store",
    "persisted_state.schema_newer_than_app",
    "persisted_state.migration_failed",
]
"""Closed taxonomy vocabulary for a persisted-state load outcome (spec §5.1).

``ok`` and ``migrated`` are the two accepting outcomes; every other code
is a **refusal** — the caller raises a taxonomy error and leaves the
bytes on disk untouched.
"""

PERSISTED_STATE_CODES: Final[frozenset[PersistedStateCode]] = frozenset(
    {
        "persisted_state.ok",
        "persisted_state.migrated",
        "persisted_state.unreadable",
        "persisted_state.unknown_shape",
        "persisted_state.unknown_store",
        "persisted_state.schema_newer_than_app",
        "persisted_state.migration_failed",
    }
)
"""Every member of :data:`PersistedStateCode`, for runtime membership checks."""

_ACCEPTING_CODES: Final[frozenset[PersistedStateCode]] = frozenset(
    {"persisted_state.ok", "persisted_state.migrated"}
)
"""The two outcomes that yield usable state; everything else refuses."""


PersistedStateMigrationFn: TypeAlias = Callable[[Mapping[str, object]], Mapping[str, object]]
"""One explicit forward migration: old payload in, next payload out.

Implementations must be pure with respect to the filesystem — they
transform a decoded mapping and return a new one. Raising
:class:`ValueError` / :class:`TypeError` / :class:`KeyError` signals an
un-migratable payload and is turned into ``persisted_state.migration_failed``
by :func:`apply_migration_plan`.
"""

_MIGRATION_FAILURES: Final[tuple[type[BaseException], ...]] = (
    ValueError,
    TypeError,
    KeyError,
    IndexError,
)
"""Exception families a migration raises for a payload it cannot convert.

Deliberately narrow and named (the repo forbids bare ``except``): an
unexpected family propagates rather than being laundered into a refusal.
"""


@dataclass(frozen=True)
class PersistedStateMigration:
    """One ordered ``from_version -> from_version + 1`` forward migration."""

    from_version: int
    migrate: PersistedStateMigrationFn
    summary: str

    @property
    def to_version(self) -> int:
        """The version this migration produces (always ``from_version + 1``)."""

        return self.from_version + 1


@dataclass(frozen=True)
class PersistedStateStore:
    """One registered writer of operator state under the config dir.

    Attributes:
        store_id: Stable, filename-safe identifier used in journal rows,
            metric labels, and this registry's key. Never a path.
        schema_version: The version the owning module writes **today**.
            Bumping it requires adding the matching migration below.
        owner_module: Dotted module path of the owning writer, so the
            drift guard can cross-reference an AST scan against this
            table without importing anything.
        description: One line of operator-facing context.
        migrations: Explicit, ordered forward migrations. Must form an
            unbroken ``1 -> 2 -> ... -> schema_version`` chain.
    """

    store_id: str
    schema_version: int
    owner_module: str
    description: str
    migrations: tuple[PersistedStateMigration, ...] = field(default=())

    def __post_init__(self) -> None:
        """Validate the declaration at construction (fail at import, not at load)."""

        if self.schema_version < _IMPLICIT_FIRST_VERSION:
            raise ValueError(
                f"persisted store {self.store_id!r} schema_version must be >= "
                f"{_IMPLICIT_FIRST_VERSION}, got {self.schema_version}"
            )
        expected = _IMPLICIT_FIRST_VERSION
        for migration in self.migrations:
            if migration.from_version != expected:
                raise ValueError(
                    f"persisted store {self.store_id!r} migrations must form an "
                    f"unbroken chain; expected a migration from version {expected}, "
                    f"got {migration.from_version}"
                )
            expected = migration.to_version
        if expected != self.schema_version:
            raise ValueError(
                f"persisted store {self.store_id!r} declares schema_version "
                f"{self.schema_version} but its migration chain reaches {expected}; "
                "every version bump needs its forward migration"
            )


@dataclass(frozen=True)
class PersistedStateDecision:
    """The outcome of classifying or migrating one persisted payload.

    Attributes:
        code: A member of :data:`PersistedStateCode`.
        store_id: The store the decision is about (``""`` when the store
            itself is unknown).
        from_version: The version found on disk, or ``None`` when it
            could not be determined.
        to_version: The app's registered version, or ``None`` when the
            store is unknown.
        payload: The usable payload on an accepting decision; ``None`` on
            every refusal (there is deliberately no partial state).
        steps: Human-readable summaries of the migrations that ran, in
            order — empty unless ``code`` is ``persisted_state.migrated``
            or the run failed part-way.
        detail: Bounded, **path-free** diagnostic map for the journal.
    """

    code: PersistedStateCode
    store_id: str
    from_version: int | None = None
    to_version: int | None = None
    payload: Mapping[str, object] | None = None
    steps: tuple[str, ...] = field(default=())
    detail: Mapping[str, object] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        """True when the payload is usable (``ok`` or ``migrated``)."""

        return self.code in _ACCEPTING_CODES

    @property
    def refused(self) -> bool:
        """True when the caller must refuse — and must NOT reset the file."""

        return not self.accepted


# ---------------------------------------------------------------------------
# The fact table.
# ---------------------------------------------------------------------------
#
# Every module that writes operator state under the platform config dir
# appears here exactly once. Adding a config-dir writer without a row
# turns ``tests/architecture/test_persisted_state_registry.py`` red.
#
# Both current stores write their first envelope in this change, so each
# declares version 1 with an empty migration chain and an on-disk format
# that is byte-identical to what shipped before (rule 3: a file lacking
# the field IS version 1). Neither store is rewritten on read, so an
# operator who downgrades keeps files this build can still parse.

_REGISTERED_STORES: Final[tuple[PersistedStateStore, ...]] = (
    PersistedStateStore(
        store_id="profile_registry",
        schema_version=1,
        owner_module="rytm_randomizer.cockpit.profiles.registry",
        description="Operator-authored cockpit profiles under {config}/profiles/user.",
    ),
    PersistedStateStore(
        store_id="library_store",
        schema_version=1,
        owner_module="rytm_randomizer.cockpit.library.store",
        description="Captured kit/sound records under {config}/library.",
    ),
)
"""Declaration order. Collapsed into the read-only mapping below."""

PERSISTED_STATE_STORES: Final[Mapping[str, PersistedStateStore]] = MappingProxyType(
    {store.store_id: store for store in _REGISTERED_STORES}
)
"""Store id -> declaration. The registry the drift guard walks.

Wrapped in :class:`~types.MappingProxyType` per the repo's no-mutable-
module-globals house rule (``tests/architecture/test_house_style.py``
rule 3): the fact table is a table of facts, and nothing at runtime may
add a store to it. Tests that need a hypothetical store pass one
directly to :func:`classify_payload` via ``store=`` rather than mutating
this mapping.
"""


def registered_store_ids() -> tuple[str, ...]:
    """Every registered store id, sorted (stable for tests and journals)."""

    return tuple(sorted(PERSISTED_STATE_STORES))


def registered_store(store_id: str) -> PersistedStateStore | None:
    """Return one store declaration, or ``None`` when ``store_id`` is unknown."""

    return PERSISTED_STATE_STORES.get(store_id)


def current_schema_version(store_id: str) -> int | None:
    """The version ``store_id`` writes today, or ``None`` when unregistered."""

    store = PERSISTED_STATE_STORES.get(store_id)
    return None if store is None else store.schema_version


def require_schema_version(store_id: str) -> int:
    """The version ``store_id`` writes today; raises when it is unregistered.

    The registration entry point for a store module: calling it at import
    time means an owner that forgets its registry row fails loudly on
    import rather than writing unversioned state, which is the
    "compile error until you register" half of spec §11 Contract A.
    """

    version = current_schema_version(store_id)
    if version is None:
        raise ValueError(
            f"persisted store {store_id!r} is not registered in "
            "rytm_randomizer/data/persisted_state.py — every module that "
            "writes operator state under the config dir must declare a "
            "schema_version there (see .claude/rules/update-compatibility.md)"
        )
    return version


def read_schema_version(payload: Mapping[str, object]) -> int | None:
    """Extract the envelope version from ``payload``.

    Returns :data:`_IMPLICIT_FIRST_VERSION` when the field is absent —
    rule 3: a pre-envelope file is version 1, never corruption. Returns
    ``None`` only when the field is *present but not a usable integer*,
    which is a genuine shape problem.

    ``bool`` is rejected explicitly: it is an ``int`` subclass, and
    ``{"schema_version": True}`` is malformed state, not version 1.
    """

    if PERSISTED_STATE_VERSION_FIELD not in payload:
        return _IMPLICIT_FIRST_VERSION
    raw = payload[PERSISTED_STATE_VERSION_FIELD]
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    if raw < _IMPLICIT_FIRST_VERSION:
        return None
    return raw


def classify_payload(
    store_id: str,
    payload: object,
    *,
    readable: bool = True,
    store: PersistedStateStore | None = None,
) -> PersistedStateDecision:
    """Decide what a loader should do with one decoded persisted payload.

    This function performs no I/O and never raises. The caller reads and
    JSON-decodes the file itself, then passes the result here; a read or
    decode failure is signalled by ``readable=False``.

    Args:
        store_id: The registered store the payload belongs to.
        payload: The decoded payload — expected to be a mapping. Typed
            ``object`` because it arrives from disk and the
            ``isinstance`` check below is genuine runtime validation.
        readable: :data:`False` when the file could not be read or
            JSON-decoded at all, yielding ``persisted_state.unreadable``.
        store: An explicit declaration to classify against, bypassing the
            registry lookup. Production callers never pass it — it exists
            so a *hypothetical* store (a future version bump, a migration
            chain no shipped store has yet) can be exercised without
            mutating :data:`PERSISTED_STATE_STORES`, which is read-only
            by design. When given, ``store.store_id`` must match
            ``store_id``.

    Returns:
        A :class:`PersistedStateDecision`. On any refusal ``payload`` is
        :data:`None` and the caller must leave the file untouched —
        **never** reset it (rule 1).

    Raises:
        ValueError: ``store`` was supplied and its ``store_id`` disagrees
            with the ``store_id`` argument. This is a caller bug, not a
            data problem, so it is not laundered into a refusal.
    """

    if store is not None and store.store_id != store_id:
        raise ValueError(
            f"classify_payload store_id {store_id!r} disagrees with the supplied "
            f"declaration {store.store_id!r}"
        )
    if store is None:
        store = PERSISTED_STATE_STORES.get(store_id)
    if store is None:
        return PersistedStateDecision(
            code="persisted_state.unknown_store",
            store_id=store_id,
            detail={"reason": "store_not_registered"},
        )

    if not readable:
        return PersistedStateDecision(
            code="persisted_state.unreadable",
            store_id=store_id,
            to_version=store.schema_version,
            detail={"reason": "read_or_decode_failed"},
        )

    if not isinstance(payload, Mapping):
        return PersistedStateDecision(
            code="persisted_state.unknown_shape",
            store_id=store_id,
            to_version=store.schema_version,
            detail={"reason": "payload_not_a_mapping"},
        )

    mapping: Mapping[str, object] = payload
    found = read_schema_version(mapping)
    if found is None:
        return PersistedStateDecision(
            code="persisted_state.unknown_shape",
            store_id=store_id,
            to_version=store.schema_version,
            detail={"reason": "schema_version_not_a_positive_int"},
        )

    if found > store.schema_version:
        # The downgrade-refusal rule. An operator who tried a newer build
        # and rolled back keeps their state; the older app declines to
        # read it rather than truncating it to what it understands.
        return PersistedStateDecision(
            code="persisted_state.schema_newer_than_app",
            store_id=store_id,
            from_version=found,
            to_version=store.schema_version,
            detail={
                "reason": "state_written_by_newer_app",
                "found_version": found,
                "app_version": store.schema_version,
            },
        )

    if found == store.schema_version:
        return PersistedStateDecision(
            code="persisted_state.ok",
            store_id=store_id,
            from_version=found,
            to_version=store.schema_version,
            payload=mapping,
        )

    return apply_migration_plan(store, mapping, from_version=found)


def plan_migration(
    store: PersistedStateStore,
    from_version: int,
) -> tuple[PersistedStateMigration, ...]:
    """The ordered migration chain taking ``from_version`` to the current version.

    Returns an empty tuple when ``from_version`` already equals the
    store's version. Only migrations whose ``from_version`` is at or
    above the starting point participate, in declaration order — the
    chain's contiguity was already validated at registration.
    """

    return tuple(
        migration for migration in store.migrations if migration.from_version >= from_version
    )


def apply_migration_plan(
    store: PersistedStateStore,
    payload: Mapping[str, object],
    *,
    from_version: int,
) -> PersistedStateDecision:
    """Run the forward migration chain for ``payload``; never raises.

    Each step is recorded in ``steps`` so the caller can journal exactly
    which migrations ran. A step that raises one of
    :data:`_MIGRATION_FAILURES`, or that returns a non-mapping, yields
    ``persisted_state.migration_failed`` with the failing step's version
    in the detail — and no payload, because a half-migrated payload is
    worse than a refusal.

    A store with no declared migration for the on-disk version also
    fails closed: silently accepting an unmigrated payload is precisely
    the silent data loss rule 1 forbids.
    """

    chain = plan_migration(store, from_version)
    if not chain:
        return PersistedStateDecision(
            code="persisted_state.migration_failed",
            store_id=store.store_id,
            from_version=from_version,
            to_version=store.schema_version,
            detail={
                "reason": "no_migration_declared",
                "found_version": from_version,
                "app_version": store.schema_version,
            },
        )

    current: Mapping[str, object] = payload
    steps: list[str] = []
    for migration in chain:
        try:
            migrated = migration.migrate(current)
        except _MIGRATION_FAILURES:
            return PersistedStateDecision(
                code="persisted_state.migration_failed",
                store_id=store.store_id,
                from_version=from_version,
                to_version=store.schema_version,
                steps=tuple(steps),
                detail={
                    "reason": "migration_raised",
                    "failed_from_version": migration.from_version,
                    "failed_to_version": migration.to_version,
                },
            )
        if not isinstance(migrated, Mapping):
            return PersistedStateDecision(
                code="persisted_state.migration_failed",
                store_id=store.store_id,
                from_version=from_version,
                to_version=store.schema_version,
                steps=tuple(steps),
                detail={
                    "reason": "migration_returned_non_mapping",
                    "failed_from_version": migration.from_version,
                    "failed_to_version": migration.to_version,
                },
            )
        current = migrated
        steps.append(migration.summary)

    stamped = dict(current)
    stamped[PERSISTED_STATE_VERSION_FIELD] = store.schema_version
    return PersistedStateDecision(
        code="persisted_state.migrated",
        store_id=store.store_id,
        from_version=from_version,
        to_version=store.schema_version,
        payload=stamped,
        steps=tuple(steps),
        detail={"reason": "migrated_forward", "steps": len(steps)},
    )
