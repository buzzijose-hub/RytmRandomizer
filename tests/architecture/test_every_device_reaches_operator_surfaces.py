"""Every registered device must reach the operator-facing surfaces.

Registering a device is not the same as a human being able to see it. The
existing device guards all check that a device is registered *correctly* —
that it satisfies the Protocol, routes through the strategy seam, does not
import across families. **None of them check that it is ever shown to
anybody.**

That gap is not hypothetical. When the Digitakt and Digitakt II landed they
were registered, Protocol-conformant and strategy-routed — every device guard
passed — and:

* ``dual-machine-target-report both`` listed only the Rytm and the Analog
  Four, because ``dual_machine/targets.py`` filters the shared registry
  through a hardcoded alias tuple;
* the cockpit's DEVICES rail never mentioned a Digitakt at all;
* ``KitCapturePanel.tsx`` labels any non-Rytm device "Analog Four MKII" via a
  two-branch ternary, so a Digitakt would be silently mislabelled rather than
  rejected.

The README guard (``test_readme_freshness``) is the precedent this file
extends: it exists because a PR added the Analog Four and left the README
describing a Rytm-only product. Same failure, one layer in — a device the
product knows about but never shows.

Scope, deliberately narrow: this pins the two *census* surfaces, the reports
whose stated job is to enumerate the device roster. It does NOT pin alias
resolvers like ``dual_machine.targets``, whose ``both`` means "the Rytm+A4
pair the dual-machine workflows are built around" rather than "every device".
Conflating those two would force an unrelated device into a workflow that has
no idea what to do with it.
"""

from __future__ import annotations

from typing import Final

import pytest

pytestmark = pytest.mark.fast

#: Reports whose documented job is to enumerate the registered roster. A new
#: device must appear in each. Keyed by a human label for the failure message.
_CENSUS_SURFACES: Final[tuple[tuple[str, str, str], ...]] = (
    (
        "device inventory model",
        "rytm_randomizer.reports.live_gui_device_inventory_model",
        "format_live_gui_device_inventory_model_report",
    ),
    (
        "performance console model",
        "rytm_randomizer.reports.live_gui_performance_console_model",
        "format_live_gui_performance_console_model_report",
    ),
)


def _render(module_path: str, function_name: str) -> str:
    """Render one census report to a single searchable string."""

    import importlib

    module = importlib.import_module(module_path)
    render = getattr(module, function_name)
    return "\n".join(render())


def test_every_registered_device_appears_in_every_census_surface() -> None:
    """A registered device the operator can never see is not really supported.

    Add a device family and forget one of these reports, and this fails with
    the device id and the surface that dropped it — rather than the device
    quietly being absent from the product until somebody notices by hand.
    """

    from rytm_randomizer.devices import all_devices

    devices = all_devices()
    assert devices, (
        "The device registry is empty — importing rytm_randomizer.devices "
        "registered nothing. This test cannot run; fix the registry first."
    )

    missing: list[str] = []
    for label, module_path, function_name in _CENSUS_SURFACES:
        rendered = _render(module_path, function_name)
        for device_id, device in devices.items():
            display_name = str(getattr(device, "display_name", ""))
            if device_id in rendered or (display_name and display_name in rendered):
                continue
            missing.append(f"{device_id} ({display_name}) is absent from the {label}")

    assert not missing, (
        "Registered devices are missing from a census surface:\n  "
        + "\n  ".join(missing)
        + "\n\nRegistering a device does not make it visible. Each report above "
        "enumerates the roster for an operator, so a device missing from one is "
        "a device the product does not actually show. Either render it from "
        "`devices.all_devices()` instead of a hardcoded list, or — if the "
        "omission is deliberate — say so explicitly rather than leaving it to "
        "look like an oversight."
    )


def test_census_surfaces_render_every_device_count_and_name() -> None:
    """The census must carry the facts, not merely the id.

    A report that prints a device id but not its track count still leaves an
    operator unable to tell a Digitakt (8) from a Digitakt II (16) — which is
    exactly the fact a hardware verifier is asked to check.
    """

    from rytm_randomizer.devices import all_devices

    rendered = _render(*_CENSUS_SURFACES[0][1:])
    incomplete: list[str] = []
    for device_id, device in all_devices().items():
        track_count = getattr(device, "track_count", None)
        if track_count is None:
            continue
        if str(track_count) not in rendered:
            incomplete.append(f"{device_id}: track_count {track_count} not rendered")

    assert not incomplete, (
        "The device inventory omits a device's track count:\n  "
        + "\n  ".join(incomplete)
        + "\n\nThe count is how an operator tells two generations of the same "
        "family apart (Digitakt 8 vs Digitakt II 16); it is the fact hardware "
        "verification is asked to confirm."
    )
