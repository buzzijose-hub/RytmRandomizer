"""Validate and file Digitakt SysEx captures, so a verifier does not have to.

A hardware verifier's job is to press buttons on the instrument. Everything
after the ``.syx`` file lands on disk is mechanical, error-prone and exactly
the part a non-technical person should not be doing by hand: checking the file
is really an Elektron dump, computing SHA256s, creating the fixture folder,
naming files consistently, and writing the provenance note that makes a
capture usable at all.

This script does that half. It is **passive**: it reads files, writes into
``tests/fixtures/digitakt_saved_kit/``, and never opens a MIDI port or touches
the instrument. It cannot capture for you -- catching the dump needs a MIDI
listener and a human pressing ``YES`` on the Digitakt -- but it takes over the
moment a file exists.

Usage::

    python scripts/intake_digitakt_capture.py \\
        --device digitakt_mk1 \\
        --low  ~/Desktop/low.syx \\
        --high ~/Desktop/high.syx \\
        --captured-by "Steve" \\
        --os-version "1.52A"

``--high`` is optional but strongly encouraged: a matched pair differing in one
known parameter is what makes offset discovery possible by comparison rather
than by guesswork. With a single file there is nothing to compare against.

Part C of the verification guide is a fixed series of four captures, each
changing exactly one thing from the one before. Saved on the Desktop under
the names in :data:`PART_C_STEPS`, they are filed in one command::

    python scripts/intake_digitakt_capture.py --device digitakt_mk1 --part-c \\
        --captured-by "Steve" --os-version "1.52A" \\
        --screen-values "track 1 FREQ 64, track 2 FREQ 0, track 8 FREQ 0"

They land in their own ``part_c/`` folder so earlier captures and their note
are never overwritten.

Nothing here promotes any offset. Landing fixtures is evidence collection;
promotion is a separate, reviewed change that must satisfy
``.claude/rules/targeted-mutation-safety.md`` #6.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import date
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
FIXTURE_DIR: Final[Path] = PROJECT_ROOT / "tests" / "fixtures" / "digitakt_saved_kit"

#: Bigger than any plausible single pattern (a real Digitakt MK1 PATTERN dump
#: is 31,613 bytes). A whole-project dump is the common
#: mistake, and these files are committed permanently, so refuse loudly rather
#: than quietly adding megabytes to the repository's history.
MAX_REASONABLE_KIT_BYTES: Final[int] = 64 * 1024

_DEVICE_CHOICES: Final[tuple[str, ...]] = ("digitakt_mk1", "digitakt_ii")

#: The menu path confirmed on a Digitakt MK1 (OS 1.52A). A Digitakt has no KIT item.
DEFAULT_MENU_PATH: Final[str] = "SETTINGS > SYSEX DUMP > SYSEX SEND > PATTERN"

#: Part C: (file name on the Desktop, what changed since the previous capture).
PART_C_STEPS: Final[tuple[tuple[str, str], ...]] = (
    ("base.syx", "fresh project, nothing changed (every track's FREQ at its default)"),
    ("t1_mid.syx", "ONLY track 1 FREQ changed, to the middle (64)"),
    ("t2_low.syx", "then ONLY track 2 FREQ changed, to 0"),
    ("t8_low.syx", "then ONLY track 8 FREQ changed, to 0"),
)
PART_C_SUBDIR: Final[str] = "part_c"


def _fail(message: str) -> None:
    """Print an operator-readable error and exit non-zero."""

    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256_of(data: bytes) -> str:
    """Return the SHA256 of ``data`` as lowercase hex."""

    return hashlib.sha256(data).hexdigest()


def validate_capture(path: Path, device_id: str) -> bytes:
    """Read ``path`` and check it looks like a Digitakt PATTERN dump.

    Validation routes through the registered device's own decoder rather than
    re-typing byte rules here: the decoder is the single place that knows what
    a Digitakt payload looks like, and a second copy would drift from it.
    """

    if not path.is_file():
        _fail(f"no such file: {path}")
    raw = path.read_bytes()
    if not raw:
        _fail(f"{path.name} is empty -- the capture tool caught nothing. Redo the dump.")
    if len(raw) > MAX_REASONABLE_KIT_BYTES:
        _fail(
            f"{path.name} is {len(raw):,} bytes, which is far too large for a single "
            "pattern. You probably sent the whole PROJECT instead of the PATTERN. Redo the "
            "dump and choose PATTERN."
        )

    from rytm_randomizer.devices import registry
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    device = registry.get_device(device_id)
    try:
        payloads = extract_sysex_payloads(raw)
        if len(payloads) != 1:
            raise ValueError(f"expected exactly one SysEx message, found {len(payloads)}")
        device.decode_snapshot(payloads[0], 0)
    except ValueError as error:
        # The decoder's message already names the specific problem (missing
        # manufacturer id, wrong family byte, ...). Surfacing it verbatim beats
        # a generic "invalid file".
        _fail(f"{path.name} is not a readable Digitakt dump: {error}")
    return raw


def _note(
    *,
    device_id: str,
    captured_by: str,
    os_version: str,
    menu_path: str,
    entries: tuple[tuple[str, str, str], ...],
    screen_values: str | None = None,
) -> str:
    """Render the provenance note that must accompany the fixtures."""

    display = "Digitakt II" if device_id == "digitakt_ii" else "Digitakt (MK1)"
    lines = [
        "# Digitakt saved-kit wire fixtures",
        "",
        f"Captured by: {captured_by}",
        f"Date: {date.today().isoformat()}",
        f"Device: {display} (`{device_id}`)",
        f"OS version: {os_version}",
        f"Dump menu path: {menu_path}",
        *([f"Screen values reported: {screen_values}"] if screen_values else []),
        "",
        "## Files",
        "",
    ]
    for filename, description, digest in entries:
        lines += [f"- `{filename}`: {description}; SHA256 `{digest}`."]
    lines += [
        "",
        "## Status",
        "",
        "These captures are **evidence**, not send authority. A fact is promoted",
        "from them only by a reviewed change that adds fixture-backed byte",
        "isolation, checksum and exact re-encode evidence per",
        "`.claude/rules/targeted-mutation-safety.md` #6; nothing here enables a",
        "send (`DIGITAKT_OFFSETS_PROMOTED = False`).",
        "",
        "## Provenance",
        "",
        f"{captured_by} created these from a disposable initialized kit on their own",
        "hardware specifically for this repository's verification work. They contain",
        "no commercial sample-pack content and no personal performance material, and",
        "may be redistributed under the repository licence for test and verification",
        "use.",
        "",
    ]
    return "\n".join(lines)


def _changed_bytes(before: bytes, after: bytes, device_id: str) -> int:
    """Count differing bytes, comparing decoded bodies when the device decodes them."""

    from rytm_randomizer.devices import registry
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    device = registry.get_device(device_id)
    decoded = [device.decode_snapshot(extract_sysex_payloads(raw)[0], 0) for raw in (before, after)]
    bodies = [getattr(snap, "unpacked", b"") or raw for snap, raw in zip(decoded, (before, after))]
    if len(bodies[0]) != len(bodies[1]):
        return max(len(bodies[0]), len(bodies[1]))
    return sum(1 for a, b in zip(bodies[0], bodies[1]) if a != b)


def main(argv: list[str] | None = None) -> int:
    """Validate the captures, copy them into the fixture dir, write the note."""

    parser = argparse.ArgumentParser(
        description="Validate and file Digitakt SysEx captures (passive; no MIDI I/O).",
    )
    parser.add_argument("--device", required=True, choices=_DEVICE_CHOICES)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--low", type=Path, help="capture with the parameter LOW")
    mode.add_argument(
        "--part-c",
        action="store_true",
        help="file the four Part C captures (" + ", ".join(n for n, _ in PART_C_STEPS) + ")",
    )
    parser.add_argument("--high", type=Path, help="matched capture with the parameter HIGH")
    parser.add_argument(
        "--from-dir",
        type=Path,
        default=Path.home() / "Desktop",
        help="where the Part C files were saved (default: your Desktop)",
    )
    parser.add_argument("--captured-by", required=True, help="who made the capture")
    parser.add_argument("--os-version", required=True, help="instrument OS version")
    parser.add_argument(
        "--menu-path",
        default=DEFAULT_MENU_PATH,
        help="the EXACT menu path used, as seen on the instrument",
    )
    parser.add_argument(
        "--screen-values",
        help="the values the screen showed, e.g. 'track 1 FREQ 64, track 2 FREQ 0'",
    )
    parser.add_argument(
        "--parameter",
        default="track 1 filter frequency",
        help="which parameter differs between the two captures",
    )
    args = parser.parse_args(argv)

    target_dir = FIXTURE_DIR
    sources: list[tuple[Path, str, str]]
    if args.part_c:
        if args.high is not None:
            _fail("--high belongs to the low/high pair, not to --part-c.")
        target_dir = FIXTURE_DIR / PART_C_SUBDIR
        sources = [
            (args.from_dir / name, f"{args.device}_partc_{Path(name).stem}.syx", description)
            for name, description in PART_C_STEPS
        ]
    else:
        sources = [
            (
                args.low,
                f"{args.device}_kit_filter_low.syx",
                f"initialized kit, {args.parameter} LOW",
            )
        ]
        if args.high is not None:
            sources.append(
                (
                    args.high,
                    f"{args.device}_kit_filter_high.syx",
                    f"same kit, ONLY {args.parameter} changed to HIGH",
                )
            )

    # Validate and hash EVERYTHING before writing anything. A partial intake
    # that copies one file and then fails leaves the fixture dir in a state the
    # verifier has to clean up by hand, and prints advice above the error that
    # actually matters.
    checked: list[tuple[Path, str, str, bytes, str]] = []
    for source, target_name, description in sources:
        # One read per file: the bytes that pass validation are the bytes that
        # get hashed and filed, even if the source changes afterwards.
        raw = validate_capture(source, args.device)
        checked.append((source, target_name, description, raw, sha256_of(raw)))

    for previous, current in zip(checked, checked[1:]):
        if previous[4] == current[4]:
            _fail(
                f"{previous[0].name} and {current[0].name} are byte-identical, so nothing\n"
                "       changed between them. Make the change for that step, then capture\n"
                f"       {current[0].name} again."
            )

    entries: list[tuple[str, str, str]] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for _source, target_name, description, raw, digest in checked:
        (target_dir / target_name).write_bytes(raw)
        entries.append((target_name, description, digest))
        print(f"ok  {target_name}  {len(raw):,} bytes  sha256={digest[:16]}...")

    if args.part_c:
        # One change per step should show up as a handful of bytes at most. A
        # big number means more than one thing changed, which is worth knowing
        # now, while the Digitakt is still on the desk.
        print()
        for previous, current in zip(checked, checked[1:]):
            count = _changed_bytes(previous[3], current[3], args.device)
            print(f"    {previous[0].name} -> {current[0].name}: {count} byte(s) changed")
    elif args.high is None:
        print(
            "\nnote: no --high capture given. A single file cannot be compared against\n"
            "      anything, so offset discovery stays blocked. The matched pair is the\n"
            "      whole point -- please capture the second one if you can.",
            file=sys.stderr,
        )

    note_path = target_dir / "README.md"
    note_path.write_text(
        _note(
            device_id=args.device,
            captured_by=args.captured_by,
            os_version=args.os_version,
            menu_path=args.menu_path,
            entries=tuple(entries),
            screen_values=args.screen_values,
        ),
        encoding="utf-8",
    )
    print(f"ok  {note_path.relative_to(PROJECT_ROOT)}")
    print()
    print("Done. Next: commit these on a branch and open a pull request, or send")
    print(f"the whole {target_dir.relative_to(PROJECT_ROOT)} folder to the project owner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
