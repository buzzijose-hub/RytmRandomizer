"""Gate 12 — module-level constants must be annotated with ``Final[T]``.

Per ``docs/PLAN_REQUIREMENTS.md`` Gate 12 (Module-level constants use
``Final`` (or frozen dataclass)):

    Every new module-level constant must be annotated with
    ``typing.Final[T]`` (or be a ``@dataclass(frozen=True)`` instance for
    grouped constants). Extends the existing house-style rule in
    ``docs/ARCHITECTURE.md`` §4.

    Bare assignments at module level (``X = 5``) that look like
    constants but lack ``Final`` are flagged by ``python-reviewer`` in
    code review.

The python-reviewer agent already nags about this in code review. This
test **mechanizes** the rule so it lands at PR time without depending on
the reviewer agent being run.

**What this test catches:**

* ``DEFAULT_PORT = 4317`` — bare literal, looks-like-a-constant name,
  no annotation at all.
* ``DEFAULT_PORT: int = 4317`` — explicitly typed but missing
  ``Final[...]``.
* ``CHANNELS: list[int] = [1, 2, 3]`` — annotated container, missing
  ``Final``.

**What this test deliberately does NOT catch (and must not):**

* ``__all__`` / ``__version__`` / other dunders — module export
  metadata, conventionally bare.
* ``_logger = logging.getLogger(__name__)`` — logger instance, not a
  literal. ``ast.Call`` RHS is always exempt.
* ``MyType = int | None`` — type alias (BinOp ``|`` RHS).
* ``Sender = Union[A, B]`` — type alias (``Union[...]`` Subscript RHS).
* Function bodies, class bodies, nested scopes — top-level only.
* ``Foo = _internal.Foo`` — re-exports (Name/Attribute RHS, not a
  literal).
* Anything whose name doesn't match ``^_?[A-Z][A-Z0-9_]*$`` (i.e.
  doesn't look like a constant).

**Allowlist:** the test ships with a grandfather floor
(:data:`_GRANDFATHERED_BARE_CONSTANTS`) of every offender that already
existed at the time the test landed. The set is **intended to shrink
monotonically**:

1. NEVER add a new entry. New code must use ``Final[T]`` from day one.
2. REMOVE an entry once you annotate it. The third sub-test below auto-fails
   if you forget the bookkeeping change.
3. The second sub-test auto-prunes entries whose file no longer exists
   (rename or delete the file -> remove the allowlist entry too).

Mirrors the ratchet pattern in ``test_plan_doc_status_truth.py``.

See also:
* ``test_no_any_escape_hatches.py`` — Gate 6 (no bare ``X = Any`` aliases).
* ``test_no_string_literal_mode_dispatch.py`` — Gate 10 (no string-literal
  mode dispatch).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# Names that look like constants by convention. ``_LEADING`` underscore
# is permitted (module-private constants follow the same Final rule).
_CONST_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^_?[A-Z][A-Z0-9_]*$")

# Dunder module-level assignments that are NEVER constants in this sense
# (they're module metadata; Python tooling expects them bare).
_EXEMPT_DUNDER_NAMES: Final[frozenset[str]] = frozenset(
    {
        "__all__",
        "__version__",
        "__author__",
        "__doc__",
        "__email__",
        "__license__",
        "__copyright__",
        "__title__",
    }
)

# Logger-instance names (``logger``, ``_logger``, ``LOGGER``, ``_LOGGER``).
# ``getLogger()`` is a call (already exempt) but contributors sometimes
# assign loggers via a name that survives our constant-name regex; this
# is a belt-and-braces filter.
_LOGGER_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^_?(?:logger|LOGGER)$")

# Typing-related names that signal "this is a type alias, not a literal".
# Used to recognise ``MyType = Union[...]`` / ``MyType = Optional[X]``
# style aliases and skip them.
_TYPING_ALIAS_HEADS: Final[frozenset[str]] = frozenset(
    {
        "Union",
        "Optional",
        "TypeAlias",
        "Literal",
        "Callable",
        "Tuple",
        "List",
        "Dict",
        "Set",
        "FrozenSet",
        "Type",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "Iterable",
        "Iterator",
        "Awaitable",
        "Coroutine",
        "Generator",
        "Protocol",
        "TypeVar",
        "ParamSpec",
        "Any",
        "NewType",
        "ClassVar",
    }
)


def _is_literal_value(value: ast.expr) -> bool:
    """Return True if ``value`` is a pure-literal expression we expect ``Final`` on.

    Captures ``ast.Constant`` (the obvious case: int / str / bytes /
    float / bool / None), plus literal containers built only of other
    literals (``[1, 2, 3]``, ``("a", "b")``, ``{"k": 1}``, ``{1, 2}``).
    Also accepts unary +/- on literals so ``X = -1`` is treated as a
    literal.

    Crucially returns ``False`` for ``ast.Call`` (``DEFAULT = Foo()``),
    ``ast.Name`` (``X = some_other_const`` — re-export), and any
    expression that mixes in names / attributes. Those have their own
    Gate-12 story (the precompiled-object bucket mentioned in
    CODE_REVIEW.md PR 12) and are not in scope for this test.
    """

    if isinstance(value, ast.Constant):
        return True
    if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        return all(_is_literal_value(e) for e in value.elts)
    if isinstance(value, ast.Dict):
        return all(
            (k is not None and _is_literal_value(k)) and _is_literal_value(v)
            for k, v in zip(value.keys, value.values, strict=False)
        )
    if isinstance(value, ast.UnaryOp) and isinstance(value.op, (ast.USub, ast.UAdd)):
        return _is_literal_value(value.operand)
    return False


def _looks_like_type_alias(value: ast.expr) -> bool:
    """Heuristic: is this RHS a typing expression (``Union[...]``, ``int | None``)?

    Type aliases are intentionally NOT constants and should not carry
    ``Final``. Detect the two common forms:

    * ``MyType = Union[A, B]`` / ``MyType = Optional[X]`` / etc. —
      ``ast.Subscript`` whose head is in :data:`_TYPING_ALIAS_HEADS`.
    * ``MyType = int | None`` — PEP 604 union, ``ast.BinOp(op=BitOr)``.
    """

    if isinstance(value, ast.Subscript):
        head = value.value
        if isinstance(head, ast.Name) and head.id in _TYPING_ALIAS_HEADS:
            return True
        if isinstance(head, ast.Attribute) and head.attr in _TYPING_ALIAS_HEADS:
            return True
    return bool(isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr))


def _annotation_has_final(annotation: ast.expr | None) -> bool:
    """Return True iff the unparsed annotation source contains the name ``Final``.

    Robust to ``Final``, ``typing.Final``, ``t.Final``, ``Final[int]``,
    ``Final[tuple[str, ...]]``, etc. — we string-match the name. A
    contributor who creates a local variable literally named ``Final``
    that isn't ``typing.Final`` would slip past this test, but that
    pathology is not worth the parsing complexity.
    """

    if annotation is None:
        return False
    try:
        text = ast.unparse(annotation)
    except (AttributeError, ValueError, TypeError):
        return False
    return re.search(r"\bFinal\b", text) is not None


def _scan_module_for_bare_constants(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, name)`` for every top-level bare constant in ``path``.

    Walks ONLY ``tree.body`` (i.e. module top level). Class bodies,
    function bodies, and nested scopes are intentionally ignored —
    constants inside those scopes follow different rules.
    """

    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        # Don't fail the whole arch test if a module is mid-edit; the
        # test that runs the build will catch the syntax error on its own.
        return []
    out: list[tuple[int, str]] = []
    for node in tree.body:
        violation = _violation_for_node(node)
        if violation is not None:
            out.append(violation)
    return out


def _violation_for_node(node: ast.stmt) -> tuple[int, str] | None:
    """Inspect a single top-level statement; return ``(lineno, name)`` or ``None``."""

    if isinstance(node, ast.AnnAssign):
        # Already annotated. If the annotation contains ``Final`` we're
        # happy (Gate 12 satisfied). If it doesn't, AND the RHS is a
        # literal, AND the name looks like a constant -> flag.
        if _annotation_has_final(node.annotation):
            return None
        if not isinstance(node.target, ast.Name):
            return None
        name = node.target.id
        if name in _EXEMPT_DUNDER_NAMES or _LOGGER_NAME_RE.match(name):
            return None
        if not _CONST_NAME_RE.match(name):
            return None
        if node.value is None:
            return None
        if not _is_literal_value(node.value):
            return None
        return (node.lineno, name)

    if isinstance(node, ast.Assign):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            # Multi-target / tuple-unpack assignments are not constants in
            # the Gate-12 sense; skip.
            return None
        name = node.targets[0].id
        if name in _EXEMPT_DUNDER_NAMES or _LOGGER_NAME_RE.match(name):
            return None
        if not _CONST_NAME_RE.match(name):
            return None
        value = node.value
        if isinstance(value, ast.Call):
            # ``MAGIC = struct.Struct(">H")`` — precompiled object, not
            # a literal. These would benefit from ``Final`` too, but
            # CODE_REVIEW.md PR 12 calls them out as a separate finding
            # bucket; deliberately out of scope here.
            return None
        if _looks_like_type_alias(value):
            return None
        if not _is_literal_value(value):
            # ``Foo = _internal.Foo`` (Attribute), ``X = OTHER_CONST``
            # (Name), and similar non-literal RHS forms reach here.
            # They're re-exports / aliases, not constants.
            return None
        return (node.lineno, name)

    return None


def _all_package_files() -> list[Path]:
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _key_for(rel_path: str, name: str) -> str:
    """Allowlist key format: ``<relpath>:<name>``.

    Path + name (not path + line) so the entry survives line-number
    drift but breaks on rename — forcing the bookkeeping ratchet.
    """

    return f"{rel_path}:{name}"


# ---------------------------------------------------------------------------
# Grandfathered allowlist — the ratchet floor.
# ---------------------------------------------------------------------------
#
# Every entry below is a module-level constant that pre-dated this test
# (captured 2026-05-25). Each entry is ``<relpath>:<NAME>``.
#
# **How to use this set:**
#
# 1. NEVER add a new entry. New code must annotate constants with
#    ``Final[T]`` from the first commit. The main test below will reject
#    any new bare constant whose key isn't already in this set.
#
# 2. REMOVE an entry once you have Finalised it. Replace
#    ``DEFAULT_PORT = 4317`` with ``DEFAULT_PORT: Final[int] = 4317``,
#    then delete its line from this set. The third test below
#    (``..._actually_still_need_grandfathering``) will fail until you do
#    the bookkeeping, so the ratchet floor moves up automatically.
#
# 3. The second test (``..._still_exist``) verifies every entry's file
#    still exists on disk; renaming/deleting a file forces you to also
#    prune its allowlist entries. (You'll also want to migrate the
#    constants on the way out, but that's a separate diff.)
#
# Initial size at landing time: 282 entries across 44 files.
# Goal: shrink to zero over the next dozen PRs as we annotate each one.
_GRANDFATHERED_BARE_CONSTANTS: Final[frozenset[str]] = frozenset(
    {
        "rytm_randomizer/active_boundary.py:ACTIVE_BOUNDARY_NAME",
        "rytm_randomizer/active_boundary.py:SUPPORTED_SOURCE_KEY",
        "rytm_randomizer/active_boundary.py:SUPPORTED_SOURCE_KIND",
        "rytm_randomizer/behavior/anchor_profile.py:PACKET_2A_ANCHOR_PROFILE_KEYS",
        "rytm_randomizer/behavior/anchor_profile.py:PACKET_2B_ANCHOR_PROFILE_KEYS",
        "rytm_randomizer/behavior/anchor_profile.py:PACKET_2C_ANCHOR_PROFILE_KEYS",
        "rytm_randomizer/behavior/anchor_profile.py:_COMMAND_ANCHOR_NAMES",
        "rytm_randomizer/behavior/anchor_profile.py:_COMMAND_PROFILE_KEYS",
        "rytm_randomizer/behavior/menu_utility.py:DEFERRED_UTILITY_SESSION_KEYS",
        "rytm_randomizer/behavior/menu_utility.py:PACKET_1A_MENU_STATUS_KEYS",
        "rytm_randomizer/behavior/menu_utility.py:PACKET_1B_UTILITY_SESSION_KEYS",
        "rytm_randomizer/behavior/menu_utility.py:_SPECIAL_SCOPES",
        "rytm_randomizer/behavior/mutation_depth.py:DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:DEFERRED_PACKET_5_PAD1_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:DEFERRED_PACKET_6_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:DEFERRED_PACKET_7_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:DEFERRED_PACKET_8_PAD4_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_5A_PAD1_CURRENT_ENGINE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_5B_PAD1_BD_FM_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_5C_PAD1_BD_PLASTIC_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_5D_PAD1_BD_SILKY_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_5E_PAD1_BD_ACOUSTIC_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6A_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6B_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6C_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6D_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6E_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6F_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6G_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6H_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6I_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_6J_PAD2_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7A_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7B_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7C_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7D_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7E_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7F_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7G_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_7H_PAD3_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_8A_PAD4_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_8B_PAD4_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:PACKET_8C_PAD4_LANE_KEYS",
        "rytm_randomizer/behavior/pad_lane.py:_DEP_FM_DISCOVERY",
        "rytm_randomizer/behavior/pad_lane.py:_DEP_PLASTIC_DISCOVERY",
        "rytm_randomizer/behavior/pad_lane.py:_DEP_SAFE_MUTATION",
        "rytm_randomizer/behavior/pad_lane.py:_DEP_SILKY_DISCOVERY",
        "rytm_randomizer/behavior/pad_lane.py:_NO_PROMPT_TAIL",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_ACOUSTIC",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_CURRENT",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_FM_ANCHOR",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_FM_DISCOVERY",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_PLASTIC",
        "rytm_randomizer/behavior/pad_lane.py:_PAD1_INTENT_SILKY",
        "rytm_randomizer/behavior/pad_lane.py:_PAD2_LANE",
        "rytm_randomizer/behavior/pad_lane.py:_PAD3_LANE",
        "rytm_randomizer/behavior/pad_lane.py:_PAD4_LANE",
        "rytm_randomizer/behavior/pad_lane.py:_REGISTRY",
        "rytm_randomizer/behavior/scene_group.py:PACKET_4B_GROUP_MUTATION_INTENT_KEYS",
        "rytm_randomizer/behavior/scene_group.py:PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS",
        "rytm_randomizer/behavior/scene_group.py:PACKET_4D_GROUP_ANCHOR_INTENT_KEYS",
        "rytm_randomizer/behavior/scene_group.py:_FORBIDDEN_EARLY_HARDWARE_ACTIONS",
        "rytm_randomizer/behavior/scene_group.py:_FORBIDDEN_EARLY_HARDWARE_GROUP_MUTATION_KEYS",
        "rytm_randomizer/behavior/scene_group.py:_GROUP_ANCHOR_INTENT_DETAILS",
        "rytm_randomizer/behavior/scene_group.py:_GROUP_MUTATION_INTENT_DETAILS",
        "rytm_randomizer/behavior/scene_group.py:_LANE_AWARE_GROUP_MUTATION_INTENT_DETAILS",
        "rytm_randomizer/behavior/selected_isolated_pad.py:DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS",
        "rytm_randomizer/behavior/selected_isolated_pad.py:PACKET_11A_SELECTED_ISOLATED_PAD_KEYS",
        "rytm_randomizer/behavior/selected_isolated_pad.py:PACKET_11B_SELECTED_ISOLATED_PAD_KEYS",
        "rytm_randomizer/behavior/selected_profile.py:DEFERRED_PACKET_10_SELECTED_PROFILE_KEYS",
        "rytm_randomizer/behavior/selected_profile.py:PACKET_10A_SELECTED_PROFILE_KEYS",
        "rytm_randomizer/behavior/selected_profile.py:PACKET_10B_SELECTED_PROFILE_KEYS",
        "rytm_randomizer/behavior/undo_commit_state.py:DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS",
        "rytm_randomizer/behavior/undo_commit_state.py:PACKET_9A_UNDO_COMMIT_STATE_KEYS",
        "rytm_randomizer/behavior/undo_commit_state.py:PACKET_9B_UNDO_COMMIT_STATE_KEYS",
        "rytm_randomizer/behavior/undo_commit_state.py:PACKET_9C_UNDO_COMMIT_STATE_KEYS",
        "rytm_randomizer/behavior/undo_commit_state.py:PACKET_9D_UNDO_COMMIT_STATE_KEYS",
        "rytm_randomizer/cli_registry.py:_COMMANDS",
        "rytm_randomizer/cockpit/__main__.py:_DEFAULT_BPM",
        "rytm_randomizer/cockpit/__main__.py:_DEFAULT_DEVICE",
        "rytm_randomizer/cockpit/__main__.py:_DEFAULT_HOST",
        "rytm_randomizer/cockpit/__main__.py:_DEFAULT_PORT",
        "rytm_randomizer/cockpit/__main__.py:_PORT_ENV_VAR",
        "rytm_randomizer/commands.py:CURRENT_PROFILE_PAGE_MUTATION_COMMANDS",
        "rytm_randomizer/commands.py:FORBIDDEN_ACTIONS",
        "rytm_randomizer/commands.py:GROUP_COMMANDS",
        "rytm_randomizer/commands.py:ISOLATED_PAD_MUTATION_COMMANDS",
        "rytm_randomizer/commands.py:ISOLATED_PAD_UTILITY_COMMANDS",
        "rytm_randomizer/commands.py:LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS",
        "rytm_randomizer/commands.py:MENU_COMMANDS",
        "rytm_randomizer/commands.py:PROFILE_WORKFLOW_COMMANDS",
        "rytm_randomizer/commands.py:STATE_UTILITY_COMMANDS",
        "rytm_randomizer/commands.py:UTILITY_COMMANDS",
        "rytm_randomizer/commands.py:_PAD1_SCAFFOLD",
        "rytm_randomizer/commands.py:_PAD2_SCAFFOLD",
        "rytm_randomizer/commands.py:_PAD3_SCAFFOLD",
        "rytm_randomizer/commands.py:_PAD4_SCAFFOLD",
        "rytm_randomizer/constants.py:DEFAULT_MIDI_CHANNEL",
        "rytm_randomizer/constants.py:DEFAULT_TARGET_PAD",
        "rytm_randomizer/constants.py:GUARDED_MAIN_PROMPT_DEPTH_COMMANDS",
        "rytm_randomizer/constants.py:OUT_OF_SCOPE_PADS",
        "rytm_randomizer/constants.py:PAD1_DEFAULT_HOME",
        "rytm_randomizer/constants.py:PAD_SELECTION_LABELS",
        "rytm_randomizer/constants.py:PAD_TO_MIDI_CHANNEL",
        "rytm_randomizer/constants.py:SUPPORTED_PADS",
        "rytm_randomizer/data/param_maps.py:BD_ACOUSTIC_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_ACOUSTIC_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_ACOUSTIC_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_ACOUSTIC_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_ACOUSTIC_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_CLASSIC_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_CLASSIC_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_CLASSIC_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_CLASSIC_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_CLASSIC_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_EXTRA_MACHINES",
        "rytm_randomizer/data/param_maps.py:BD_FM_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_FM_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_FM_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_FM_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_FM_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_HARD_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_HARD_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_HARD_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_HARD_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_HARD_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_PLASTIC_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_PLASTIC_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_PLASTIC_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_PLASTIC_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_PLASTIC_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_SHARP_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_SHARP_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_SHARP_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_SHARP_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_SHARP_ZONES",
        "rytm_randomizer/data/param_maps.py:BD_SILKY_DELTAS",
        "rytm_randomizer/data/param_maps.py:BD_SILKY_ORDER",
        "rytm_randomizer/data/param_maps.py:BD_SILKY_PARAMS",
        "rytm_randomizer/data/param_maps.py:BD_SILKY_SAFE",
        "rytm_randomizer/data/param_maps.py:BD_SILKY_ZONES",
        "rytm_randomizer/data/param_maps.py:MACHINE_CC",
        "rytm_randomizer/data/param_maps.py:MY_BD_ACOUSTIC_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_CLASSIC_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_FM_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_HARD_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_PLASTIC_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_SHARP_ANCHOR",
        "rytm_randomizer/data/param_maps.py:MY_BD_SILKY_ANCHOR",
        "rytm_randomizer/data/param_maps.py:PAD2_SD_CLASSIC_ANCHOR",
        "rytm_randomizer/data/param_maps.py:PAD2_SD_FM_ANCHOR",
        "rytm_randomizer/data/param_maps.py:PAD2_SD_HARD_ANCHOR",
        "rytm_randomizer/data/param_maps.py:PAD_3_SY_RAW_ANCHOR",
        "rytm_randomizer/data/param_maps.py:SD_CLASSIC_DELTAS",
        "rytm_randomizer/data/param_maps.py:SD_CLASSIC_ORDER",
        "rytm_randomizer/data/param_maps.py:SD_CLASSIC_PARAMS",
        "rytm_randomizer/data/param_maps.py:SD_CLASSIC_SAFE",
        "rytm_randomizer/data/param_maps.py:SD_CLASSIC_ZONES",
        "rytm_randomizer/data/param_maps.py:SD_FM_DELTAS",
        "rytm_randomizer/data/param_maps.py:SD_FM_ORDER",
        "rytm_randomizer/data/param_maps.py:SD_FM_PARAMS",
        "rytm_randomizer/data/param_maps.py:SD_FM_SAFE",
        "rytm_randomizer/data/param_maps.py:SD_FM_ZONES",
        "rytm_randomizer/data/param_maps.py:SD_HARD_DELTAS",
        "rytm_randomizer/data/param_maps.py:SD_HARD_ORDER",
        "rytm_randomizer/data/param_maps.py:SD_HARD_PARAMS",
        "rytm_randomizer/data/param_maps.py:SD_HARD_SAFE",
        "rytm_randomizer/data/param_maps.py:SD_HARD_ZONES",
        "rytm_randomizer/data/param_maps.py:SY_RAW_DELTAS",
        "rytm_randomizer/data/param_maps.py:SY_RAW_ORDER",
        "rytm_randomizer/data/param_maps.py:SY_RAW_PARAMS",
        "rytm_randomizer/data/param_maps.py:SY_RAW_SAFE_LIMITS",
        "rytm_randomizer/data/param_maps.py:SY_RAW_ZONES",
        "rytm_randomizer/data/plans.py:GLOBAL_PAGE_PLANS",
        "rytm_randomizer/data/plans.py:GROUP_LAYOUT",
        "rytm_randomizer/data/plans.py:INTENSITY_PLANS",
        "rytm_randomizer/data/plans.py:PAD1_BD_MUTATION_PLANS",
        "rytm_randomizer/data/plans.py:PAD1_BD_ROTATION_ORDER",
        "rytm_randomizer/data/plans.py:PAD2_MUTATION_PLANS",
        "rytm_randomizer/data/plans.py:PAD2_PROFILE_KEYS",
        "rytm_randomizer/data/plans.py:PAD2_PROFILE_LABELS",
        "rytm_randomizer/data/plans.py:PAD3_MODE_LABELS",
        "rytm_randomizer/data/plans.py:PAD3_MODE_MUTATION_PLANS",
        "rytm_randomizer/data/plans.py:PAD3_MODE_ORDER",
        "rytm_randomizer/data/plans.py:PAD4_MODE_LABELS",
        "rytm_randomizer/data/plans.py:PAD4_MODE_MUTATION_PLANS",
        "rytm_randomizer/data/plans.py:PAD4_MODE_ORDER",
        "rytm_randomizer/data/plans.py:SY_RAW_FILTER_NAMES",
        "rytm_randomizer/data/scene_display.py:_SCENE_RUNNER_NAME_SUFFIX",
        "rytm_randomizer/data/scene_display.py:_SHELL_NAME_SUFFIX",
        "rytm_randomizer/data/scenes.py:SCENE_PRESETS",
        "rytm_randomizer/devices/registry.py:_DEVICES",
        "rytm_randomizer/engines/pad2.py:DEFAULT_PAD2_PROFILE_KEY",
        "rytm_randomizer/engines/pad3.py:DEFAULT_ISOLATED_PAD",
        "rytm_randomizer/engines/pad3.py:DEFAULT_PAD3_MODE_KEY",
        "rytm_randomizer/engines/pad3.py:SY_RAW_PROFILE_KEY",
        "rytm_randomizer/engines/pad3.py:_PAD3_TOOLS_SNAPSHOT_NAMES",
        "rytm_randomizer/engines/pad3.py:_SY_RAW_MENU_SNAPSHOT_NAMES",
        "rytm_randomizer/engines/pad4.py:BD_ACOUSTIC_PROFILE_KEY",
        "rytm_randomizer/engines/pad4.py:DEFAULT_ISOLATED_PAD",
        "rytm_randomizer/engines/pad4.py:DEFAULT_PAD4_MODE_KEY",
        "rytm_randomizer/engines/pad4.py:_PAD4_TOOLS_SNAPSHOT_NAMES",
        "rytm_randomizer/group_runner.py:DEFAULT_ISOLATED_PAD",
        "rytm_randomizer/group_runner.py:PROFILE_SELECT_MAP",
        "rytm_randomizer/guardrails/resolver.py:MODE_EXPERIMENTAL",
        "rytm_randomizer/guardrails/resolver.py:MODE_LIVE_SAFE",
        "rytm_randomizer/guardrails/resolver.py:MODE_STUDIO_DISCOVERY",
        "rytm_randomizer/guardrails/schema.py:SCHEMA_VERSION",
        "rytm_randomizer/guardrails/validation.py:PAD_PROFILE_KEY",
        "rytm_randomizer/help_text.py:USAGE",
        "rytm_randomizer/help_text.py:_COCKPIT_EXPORT_PROFILE_MODEL_SAFETY_LINES",
        "rytm_randomizer/inspection.py:SAFETY_SUMMARY",
        "rytm_randomizer/mock_message_mapper.py:SUPPORTED_GROUP_PROFILE_KEYS",
        "rytm_randomizer/observability/logging.py:JSON_FORMAT_NAME",
        "rytm_randomizer/observability/logging.py:LOG_FORMAT",
        "rytm_randomizer/observability/logging.py:PACKAGE_LOGGER_NAME",
        "rytm_randomizer/profiles.py:_GROUP_PROFILE_KEYS",
        "rytm_randomizer/profiles.py:_PAD_3_SY_RAW_CC_NAMES",
        "rytm_randomizer/runtime_plan.py:REASON_EXECUTION_NOT_IMPLEMENTED",
        "rytm_randomizer/runtime_plan.py:REASON_MISSING_ARMING",
        "rytm_randomizer/runtime_plan.py:REASON_PROFILE_4_PARKED",
        "rytm_randomizer/runtime_plan.py:REASON_UNSUPPORTED_KEY",
        "rytm_randomizer/runtime_plan.py:REASON_UNSUPPORTED_SOURCE_KIND",
        "rytm_randomizer/scene_runner.py:DEFAULT_SCENE_NAME",
        "rytm_randomizer/scenes.py:_SCAFFOLD_METADATA",
        "rytm_randomizer/state/pad_mode.py:DEFAULT_PAD2_PROFILE_KEY",
        "rytm_randomizer/state/pad_mode.py:DEFAULT_PAD3_MODE_KEY",
        "rytm_randomizer/state/pad_mode.py:DEFAULT_PAD4_MODE_KEY",
        "rytm_randomizer/state/scene.py:DEFAULT_SCENE_NAME",
        "rytm_randomizer/state/selected_isolated_pad_validation.py:DEFAULT_OPERATION_KIND",
        "rytm_randomizer/state/selected_target_validation.py:SELECTED_TARGET_DEFAULT_COMMAND_KEY",
        "rytm_randomizer/state/selection.py:DEFAULT_ISOLATED_PAD",
        "rytm_randomizer/state/selection.py:DEFAULT_TARGET_PAD",
        "rytm_randomizer/state/selection.py:VALID_PADS",
        "rytm_randomizer/style_analysis/library.py:_AUDIO_EXTENSIONS",
    }
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_top_level_constants_are_final_or_grandfathered() -> None:
    """Every top-level literal constant must be ``Final[T]``, or grandfathered.

    Enforces Gate 12 of ``docs/PLAN_REQUIREMENTS.md``. A bare
    module-level assignment of a literal whose name matches the constant
    convention is rejected unless its key is already in
    :data:`_GRANDFATHERED_BARE_CONSTANTS`.

    Failure prints one line per violation in the form
    ``rytm_randomizer/foo.py:42 — NAME``. The fix is one of:

    * Annotate with ``Final[T]``:
        ``DEFAULT_PORT: Final[int] = 4317``
    * If the value is a grouped constant set, hoist to a frozen
      dataclass and annotate the instance with ``Final``.
    * If this is a type alias, give it a ``TypeAlias`` annotation
      (``MyType: TypeAlias = Union[A, B]``) — that path is detected
      separately and won't trip this test.

    Do NOT add new entries to :data:`_GRANDFATHERED_BARE_CONSTANTS`. The
    set is frozen at its initial size (282 entries on 2026-05-25) and
    every entry should be Finalised over time.
    """

    violations: list[str] = []
    for path in _all_package_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for lineno, name in _scan_module_for_bare_constants(path):
            key = _key_for(rel, name)
            if key in _GRANDFATHERED_BARE_CONSTANTS:
                continue
            violations.append(f"{rel}:{lineno} — {name}")

    assert not violations, (
        "Gate 12 (module-level constants use `Final`) — these top-level "
        "literal constants are missing a `Final[T]` annotation. Annotate "
        "each one:\n"
        "    DEFAULT_PORT: Final[int] = 4317\n"
        "and ensure `from typing import Final` is imported.\n"
        "Do NOT add the entry to _GRANDFATHERED_BARE_CONSTANTS — that "
        "set is frozen at the size it had on 2026-05-25 and is intended "
        "to shrink, never grow.\n"
        "  Violations:\n    " + "\n    ".join(violations)
    )


def test_grandfathered_constants_still_exist() -> None:
    """Every key in :data:`_GRANDFATHERED_BARE_CONSTANTS` must still resolve to a real file.

    Regression guard: when a module is renamed or deleted, its
    grandfather entries become ghosts. This test forces the
    rename/delete commit to also prune the allowlist, so the set keeps
    shrinking instead of accumulating stale entries.
    """

    existing_files = {p.relative_to(PROJECT_ROOT).as_posix() for p in _all_package_files()}
    ghosts: list[str] = []
    for key in _GRANDFATHERED_BARE_CONSTANTS:
        rel_path, _, _name = key.partition(":")
        if rel_path not in existing_files:
            ghosts.append(key)
    assert not ghosts, (
        "Grandfathered allowlist references files that no longer exist "
        "— remove these entries from _GRANDFATHERED_BARE_CONSTANTS:\n  "
        + "\n  ".join(sorted(ghosts))
    )


def test_grandfathered_constants_actually_still_need_grandfathering() -> None:
    """A grandfathered constant that has *since* been Finalised must be removed from the allowlist.

    Regression guard: the whole point of the allowlist is to shrink
    over time. If a contributor annotates ``DEFAULT_PORT`` with
    ``Final[int]``, the entry no longer represents a real bare
    constant — leaving it in the allowlist is dead bookkeeping that
    masks future regressions (a future PR could re-introduce a bare
    ``DEFAULT_PORT`` and the allowlist would silently absorb it).

    This test scans every package file fresh; for each grandfathered
    key, it verifies the offending constant is still bare in the source.
    If the constant has been Finalised (or the name no longer appears
    as a module-level bare assignment for any reason), the allowlist
    entry must be deleted.
    """

    # Build a set of current real-bare-constant keys.
    actually_bare: set[str] = set()
    for path in _all_package_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for _lineno, name in _scan_module_for_bare_constants(path):
            actually_bare.add(_key_for(rel, name))

    # Entries that exist in the allowlist but no longer appear as bare
    # constants in source -> they've been Finalised (or removed) and the
    # allowlist entry is stale.
    redundant = sorted(_GRANDFATHERED_BARE_CONSTANTS - actually_bare)
    # Subtract ghost entries (handled by the previous test) so we don't
    # double-report the same key.
    existing_files = {p.relative_to(PROJECT_ROOT).as_posix() for p in _all_package_files()}
    redundant = [key for key in redundant if key.partition(":")[0] in existing_files]
    assert not redundant, (
        "These grandfathered constants no longer exist as bare literals "
        "in source — they have been Finalised (or otherwise resolved). "
        "Remove them from _GRANDFATHERED_BARE_CONSTANTS so the allowlist "
        "shrinks:\n  " + "\n  ".join(redundant)
    )
