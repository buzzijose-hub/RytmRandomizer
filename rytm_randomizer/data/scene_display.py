"""Data-driven scene-menu line generator.

The 14 V1.34 scene commands (``S0``..``S5`` + A/B variants) appear in two
hand-typed menus today:

* :meth:`rytm_randomizer.shell.InteractiveShell.print_commands` -- a flat
  no-indent listing of the form ``S0 = scene Home / Clean anchors``.
* :meth:`rytm_randomizer.scene_runner.SceneRunner.show_scene_tools` -- a
  2-space-indented listing of the form ``  S0  = Home / Clean anchors``.

Both menus are derived from the same canonical
:data:`rytm_randomizer.data.SCENE_PRESETS` source-of-truth dict but they each
re-typed the names by hand, which means adding a new scene used to require
edits in three places (data + shell + scene_runner). The helper here generates
either menu format directly from ``SCENE_PRESETS`` so adding a new scene only
requires editing the data.

Output of :func:`scene_menu_lines` is byte-identical to what the two call
sites currently print. The existing :mod:`tests.test_scene_runner` parity
tests (which diff stdout against the byte-frozen V1.34 monolith) lock that
guarantee in.

This module belongs in :mod:`rytm_randomizer.data` because the data layer is a
leaf (no upstream imports) -- generating display strings from the data is a
pure derivation that requires nothing else from the package. See
``tests/architecture/test_import_direction.py``.
"""

from __future__ import annotations

from .scenes import SCENE_PRESETS

__all__ = ["scene_menu_lines"]


# Suffix that the two menus append to specific scene names. The shell-style
# menu (no indent) only annotates ``s0``; the scene-runner-style menu
# (indented) also annotates ``s5``. Keeping these as two small maps -- one per
# format -- mirrors the existing hand-typed lines exactly.
_SHELL_NAME_SUFFIX: dict[str, str] = {
    "s0": " anchors",
}

_SCENE_RUNNER_NAME_SUFFIX: dict[str, str] = {
    "s0": " anchors",
    "s5": " anchors",
    # The four "base" scenes get a trailing " scene" tag in the indented menu
    # so the operator can tell base scenes apart from their A/B variants at a
    # glance. The A/B variants -- which are unambiguous already -- stay bare.
    "s1": " scene",
    "s2": " scene",
    "s3": " scene",
    "s4": " scene",
}


def scene_menu_lines(indent: str = "") -> tuple[str, ...]:
    """Return the formatted scene-menu lines derived from ``SCENE_PRESETS``.

    Parameters
    ----------
    indent:
        Empty string (the default) selects the ``shell.py`` format used by
        :meth:`InteractiveShell.print_commands`::

            "S0 = scene Home / Clean anchors"
            "S1 = scene Rolling"
            "S1A = scene Rolling Light"
            ...

        Any non-empty string selects the ``scene_runner.py`` format used by
        :meth:`SceneRunner.show_scene_tools`. The string is used as the
        per-line indent and the keys are right-padded to 3 characters so the
        equals signs stay column-aligned::

            "  S0  = Home / Clean anchors"
            "  S1  = Rolling scene"
            "  S1A = Rolling Light"
            ...

    Returns
    -------
    tuple[str, ...]
        14 formatted lines in canonical ``SCENE_PRESETS`` order
        (``s0, s1, s1a, s1b, s2, s2a, s2b, s3, s3a, s3b, s4, s4a, s4b, s5``).
    """

    if indent == "":
        return tuple(
            f"{key.upper()} = scene {preset['name']}{_SHELL_NAME_SUFFIX.get(key, '')}"
            for key, preset in SCENE_PRESETS.items()
        )

    return tuple(
        f"{indent}{key.upper():<3} = {preset['name']}{_SCENE_RUNNER_NAME_SUFFIX.get(key, '')}"
        for key, preset in SCENE_PRESETS.items()
    )
