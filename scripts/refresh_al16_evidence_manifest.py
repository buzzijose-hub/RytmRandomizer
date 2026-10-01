"""Refresh the committed AL02 evidence manifest's generator dependency hashes.

``rytm_randomizer/cockpit/export/al16_rytm_kit.py`` pins a curated list of
source files (``AL16_GENERATOR_DEPENDENCIES``) that determine the exported
Rytm KIT bytes, and the committed manifest at
``output/al16/AL02_LOCK_RYTM_manifest.json`` records their SHA-256 digests.
``tests/test_al16_rytm_export.py`` asserts the recorded digests still match
the working tree, so *any* edit to a pinned file -- including a purely
additive one, such as registering a new device family -- fails that test
until the manifest is refreshed.

Before this script existed that refresh was a hand-edit of a provenance
file, which is exactly the kind of step that should never be manual. It is
also easy to get wrong in a way that quietly over-writes real evidence.

**What this script will and will not do**

It rewrites ONLY the ``generator_dependency_sha256`` map. It refuses to run
when:

* the pinned dependency key set has changed (that is a deliberate contract
  change -- update ``AL16_GENERATOR_DEPENDENCIES`` and the companion test
  ``test_al16_generator_dependencies_match_the_complete_behavior_contract``
  in the same change set, then re-run), or
* the manifest records a real exported artifact (``output_sha256`` set).
  A manifest bound to shipped bytes must not have its provenance re-stamped
  by a bulk tool; that needs a fresh, reviewed export.

Every other manifest field -- contract, module digest, recipe, reference,
validation and byte-diff evidence -- is left byte-identical.

After running, the manifest's own SHA changes, so update
``_COMMITTED_EVIDENCE_HASHES`` in ``tests/test_al16_rytm_export.py`` with
the value printed at the end.

Usage (deliberate refresh only)::

    RYTM_AL16_MANIFEST_REFRESH=1 .venv/bin/python \\
        scripts/refresh_al16_evidence_manifest.py

Without ``RYTM_AL16_MANIFEST_REFRESH=1`` the script refuses to run, so it
cannot be triggered accidentally from an editor task or stray shell history.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Final

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_MANIFEST_PATH: Final[Path] = _REPO_ROOT / "output" / "al16" / "AL02_LOCK_RYTM_manifest.json"
_CAPTURE_FLAG: Final[str] = "RYTM_AL16_MANIFEST_REFRESH"


def _require_capture_flag() -> None:
    if os.environ.get(_CAPTURE_FLAG) != "1":
        raise SystemExit(
            f"Refusing to run without {_CAPTURE_FLAG}=1. This rewrites committed "
            "provenance evidence; see the module docstring."
        )


def main() -> int:
    """Refresh the manifest's dependency digests in place."""

    _require_capture_flag()

    sys.path.insert(0, str(_REPO_ROOT))
    from rytm_randomizer.cockpit.export import al16_rytm_kit as exporter

    raw = _MANIFEST_PATH.read_text(encoding="utf-8")
    manifest = json.loads(raw)

    if manifest.get("output_sha256") is not None:
        raise SystemExit(
            "Refusing to refresh: this manifest records a real exported artifact "
            "(output_sha256 is set). Re-stamping provenance for shipped bytes "
            "requires a fresh, reviewed export -- not a bulk hash refresh."
        )

    recorded = manifest["generator_dependency_sha256"]
    current = exporter._generator_dependency_hashes()

    if set(recorded) != set(current):
        added = sorted(set(current) - set(recorded))
        removed = sorted(set(recorded) - set(current))
        raise SystemExit(
            "Refusing to refresh: the pinned dependency set changed.\n"
            f"  added:   {added}\n"
            f"  removed: {removed}\n"
            "That is a deliberate contract change. Update "
            "AL16_GENERATOR_DEPENDENCIES and "
            "test_al16_generator_dependencies_match_the_complete_behavior_contract "
            "in the same change set, then re-run."
        )

    changed = {
        path: (recorded[path], digest)
        for path, digest in current.items()
        if recorded[path] != digest
    }
    if not changed:
        print("Manifest dependency digests already current; nothing to do.")
        return 0

    for path, (before, after) in sorted(changed.items()):
        print(f"  {path}\n    {before}\n    -> {after}")

    manifest["generator_dependency_sha256"] = current
    trailing = "\n" if raw.endswith("\n") else ""
    _MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + trailing,
        encoding="utf-8",
        newline="",
    )

    manifest_sha = hashlib.sha256(_MANIFEST_PATH.read_bytes()).hexdigest()
    print(f"\nRefreshed {len(changed)} dependency digest(s).")
    print("Update _COMMITTED_EVIDENCE_HASHES in tests/test_al16_rytm_export.py:")
    print(f'    "output/al16/AL02_LOCK_RYTM_manifest.json": (\n        "{manifest_sha}"\n    ),')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
