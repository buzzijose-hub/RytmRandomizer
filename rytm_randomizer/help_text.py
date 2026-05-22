"""Static CLI help text for the passive RytmRandomizer CLI.

This module holds the help/usage strings as data so that ``cli.py`` can stay
focused on argument parsing and dispatch. The values here are byte-for-byte
identical to the previously inline ``*_HELP`` constants; the CLI output must
not change by a single character.
"""

USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "project-status-report [--summary|--json|--check] | mock-mapper-report | runtime-plan-report | "
    "active-boundary-report | mock-runtime-active-bridge-report | "
    "anchor-profile-report | behavior-parity-report | rytm-12-pad-machine-matrix-report | "
    "rytm-snapshot-pad-compatibility-report | "
    "rytm-snapshot-intelligence-report <syx-path> [--slot N|--list] | "
    "rytm-snapshot-mutation-preview-report <syx-path> [--slot N] [--depth N] "
    "[--events] [--limit N] | "
    "rytm-style-snapshot-routing-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | "
    "rytm-style-mutation-intent-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | "
    "rytm-style-mutation-render-plan-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | "
    "rytm-style-mutation-mock-preview-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--events] [--limit N] [--json] | "
    "rytm-style-kit-readiness-report <syx-path> <style-key> "
    "[--discovery N] [--limit N] [--json] | "
    "analog-four-style-snapshot-routing-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | "
    "analog-four-style-mutation-intent-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | "
    "analog-four-style-mutation-mock-preview-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--events] [--limit N] [--json] | "
    "analog-four-kit-catalog-report <syx-path> [--limit N] [--json] | "
    "analog-four-style-kit-readiness-report <syx-path> <style-key> "
    "[--discovery N] [--limit N] [--json] | "
    "dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--discovery N] [--limit N] [--json] | "
    "dual-machine-style-kit-selection-report <style-key> --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--discovery N] [--limit N] [--json] | "
    "dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--discovery N] [--events] [--limit N] [--json] | "
    "dual-machine-style-live-audition-report <style-key> [<style-key> ...] "
    "--rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--discovery N] [--events] [--limit N] [--json] | "
    "dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] "
    "--rytm <syx-path> [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json] | "
    "dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json] | "
    "dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] "
    "[--events] [--limit N] [--json] | "
    "inspect-command <key> | "
    "dual-machine-target-report <rytm|a4|both> | inspect-scene <key> | "
    "inspect-group-profile <key> | list-commands | list-scenes | list-group-profiles | "
    "style-profile-report | list-style-profiles | inspect-style-profile <key> | "
    "search-style-profiles <query> | style-target-report | inspect-style-target <key> | "
    "style-performance-arc-report | list-style-performance-arcs | "
    "inspect-style-performance-arc <key> | search-style-performance-arcs <query> | "
    "style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-readiness-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--limit N] [--json] | "
    "style-performance-arc-audition-packet-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-rehearsal-manifest-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-session-packet-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-render-bundle-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-cue-sheet-report [<arc-key> ...] --rytm <syx-path> "
    "[--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-reference-match-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | "
    "preview-command <key> | preview-scene <key> | preview-group-profile <key>"
)


def _safety_block(lines):
    return "\n".join(f"  {line}" for line in lines)


def _rytm_snapshot_pad_compatibility_report_help():
    from .reports.rytm_snapshot_pad_compatibility import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-snapshot-pad-compatibility-report

Usage:
  python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report
  python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report --help

Behavior:
  Prints the passive Analog Rytm MK2 snapshot-pad compatibility report.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_snapshot_intelligence_report_help():
    from .reports.rytm_snapshot_intelligence import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-snapshot-intelligence-report

Usage:
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path>
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path> --list
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path> --slot N
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file and prints passive snapshot intelligence
  for a supported kit snapshot. Use --list to see supported kit slots in a dump.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_snapshot_mutation_preview_report_help():
    from .reports.rytm_snapshot_mutation_preview import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-snapshot-mutation-preview-report

Usage:
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path>
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --slot N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --depth N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --slot N --depth N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --events
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --events --limit N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, selects a supported kit snapshot,
  and prints a passive/mock-only mutation preview from snapshot machine facts.
  Use --events to include mock CC event rows. Use --limit N to cap rows; N=0
  prints all event rows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_style_snapshot_routing_report_help():
    from .reports.rytm_style_snapshot_routing import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-style-snapshot-routing-report

Usage:
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key>
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware routing readiness for the selected style target.
  The report shows favored zones, route-ready pads, blocked pads, and legal
  machine candidates without rendering mutation values.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_style_mutation_intent_report_help():
    from .reports.rytm_style_mutation_intent import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-style-mutation-intent-report

Usage:
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report <syx-path> <style-key>
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware mutation intent rows for the selected style target.
  The report shows which ready pads, zones, safe profile parameters, style
  biases, and directions future style mutation can target without rendering CC
  values or sending MIDI.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_style_mutation_render_plan_report_help():
    from .reports.rytm_style_mutation_render_plan import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-style-mutation-render-plan-report

Usage:
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report <syx-path> <style-key>
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware render-plan target windows for the selected
  style target. The report shows deterministic target values and value windows
  that future renderers can consume, without rendering CC messages or sending MIDI.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_style_mutation_mock_preview_report_help():
    from .reports.rytm_style_mutation_mock_preview import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-style-mutation-mock-preview-report

Usage:
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key>
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> --events
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> --events --limit N
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware mock CC rows for the selected style target.
  The report resolves CC numbers and target values through the existing Rytm
  renderer, but it does not open a port or send MIDI. Use --events to include
  mock CC rows; --limit N caps rows and N=0 prints all rows. Use --json for a
  deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _rytm_style_kit_readiness_report_help():
    from .reports.rytm_style_kit_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-style-kit-readiness-report

Usage:
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report <syx-path> <style-key>
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report <syx-path> <style-key> --limit N
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file, runs the passive style/mock preview
  readiness path for every supported decoded kit snapshot, and prints a per-kit
  table. The report shows which kits are preview-ready, stable payload
  fingerprints, planned pads, and how many mock rows each kit would produce.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or
  wild-discovery planning pressure. Use --limit N to cap displayed rows; N=0
  displays all rows. Use --json for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_style_snapshot_routing_report_help():
    from .reports.analog_four_style_snapshot_routing import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-style-snapshot-routing-report

Usage:
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report <syx-path> <style-key>
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report --help

Behavior:
  Reads a local Analog Four MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware routing readiness for the selected style target.
  The report shows favored zones and track readiness while A4 offsets remain
  candidate-only, so no mutation values are rendered.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_style_mutation_intent_report_help():
    from .reports.analog_four_style_mutation_intent import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-style-mutation-intent-report

Usage:
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report <syx-path> <style-key>
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report --help

Behavior:
  Reads a local Analog Four MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware track/zone mutation intent rows for the
  selected style target. The report shows zone biases and directions while A4
  offsets remain candidate-only, so no mutation values are rendered.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_style_mutation_mock_preview_report_help():
    from .reports.analog_four_style_mutation_mock_preview import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-style-mutation-mock-preview-report

Usage:
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key>
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> --slot N
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> --events
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> --events --limit N
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report --help

Behavior:
  Reads a local Analog Four MK2 SysEx file, selects a supported kit snapshot,
  and prints passive style-aware mock CC rows for the selected style target.
  Decoded A4 SysEx snapshots are candidate-only until offset promotion, so
  those reports clearly show why mock CC rows are blocked. Promoted snapshots
  can render CC-safe zones; NRPN-only zones are listed as deferred. Use --events
  to include mock CC rows; --limit N caps rows and N=0 prints all rows. Use
  --json for a deterministic machine-readable payload for future GUI/analyzer
  consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_kit_catalog_report_help():
    from .reports.analog_four_kit_catalog import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-kit-catalog-report

Usage:
  python -m rytm_randomizer.cli analog-four-kit-catalog-report <syx-path>
  python -m rytm_randomizer.cli analog-four-kit-catalog-report <syx-path> --limit N
  python -m rytm_randomizer.cli analog-four-kit-catalog-report <syx-path> --json
  python -m rytm_randomizer.cli analog-four-kit-catalog-report --help

Behavior:
  Reads a local Analog Four MK2 SysEx file and prints a passive kit catalog
  for every supported decoded kit snapshot. The report shows slot, kit name,
  SysEx layout, byte counts, and whether mutation remains blocked by
  candidate-only offsets. Use --limit N to cap displayed rows; N=0 displays
  all rows. Use --json for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_style_kit_readiness_report_help():
    from .reports.analog_four_style_kit_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-style-kit-readiness-report

Usage:
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report <syx-path> <style-key>
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report <syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report <syx-path> <style-key> --limit N
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report <syx-path> <style-key> --json
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report --help

Behavior:
  Reads a local Analog Four MK2 SysEx file, runs the passive style/mock preview
  readiness path for every supported decoded kit snapshot, and prints a per-kit
  table. The report shows which kits are preview-ready, which remain blocked by
  candidate-only offsets, and how many mock/deferred rows each kit would produce.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or
  wild-discovery planning pressure. Use --limit N to cap displayed rows; N=0
  displays all rows. Use --json for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_kit_readiness_report_help():
    from .reports.dual_machine_style_kit_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-kit-readiness-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key>
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key> --limit N
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key> --json
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report --help

Behavior:
  Reads one local Analog Rytm MK2 SysEx file and one local Analog Four MK2 SysEx
  file, runs the passive style/mock preview readiness path across every decoded
  kit, and ranks Rytm + A4 pairings for the selected style target. The report
  shows ready, partial, and blocked rig pairings with stable fingerprints so a
  future GUI/live workflow can choose a kit pair before any armed path exists.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or
  wild-discovery planning pressure. Use --limit N to cap displayed rows; N=0
  displays all rows. Use --json for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_kit_selection_report_help():
    from .reports.dual_machine_style_kit_selection import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-kit-selection-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --analog-four <syx-path> --scope analog-four-only
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --scope dual|rytm-only|analog-four-only|a4-only
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --rytm <syx-path> [--analog-four <syx-path>] [--discovery N] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report --help

Behavior:
  Reads local Analog Rytm MK2 and/or Analog Four MK2 SysEx kit banks, consumes
  the passive style kit-readiness layer, and ranks the best operator selection
  for a live style target. With both paths it ranks dual-machine pairings. With
  --scope rytm-only or --scope analog-four-only it recommends one machine and
  explicitly leaves the other unchanged. Use --discovery N (0-100) to choose
  reference, balanced, discovery, or wild-discovery planning pressure. Use
  --limit N to cap displayed rows; N=0 displays all rows. Use --json for future
  GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_selection_mock_preview_report_help():
    from .reports.dual_machine_style_selection_mock_preview import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-selection-mock-preview-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --analog-four <syx-path> --scope analog-four-only
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --scope dual|rytm-only|analog-four-only|a4-only
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> [--analog-four <syx-path>] [--rank N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report --help

Behavior:
  Reads local Analog Rytm MK2 and/or Analog Four MK2 SysEx kit banks, selects a
  ranked style kit candidate, and prints the passive/mock-only mutation preview
  for that selection. Use --rank N to audition a lower-ranked candidate without
  manually copying slots between reports. Single-machine scopes leave the other
  machine unchanged.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_live_audition_report_help():
    from .reports.dual_machine_style_live_audition import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-live-audition-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --analog-four <syx-path> --scope analog-four-only
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --scope dual|rytm-only|analog-four-only|a4-only
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--rank N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report --help

Behavior:
  Reads local Analog Rytm MK2 and/or Analog Four MK2 SysEx kit banks, runs the
  ranked style selection mock preview for each requested style in order, and
  prints a passive live-audition set plan. This is for trying several style
  targets quickly during a performance or studio prep session without opening a
  MIDI port. Single-machine scopes leave the other machine unchanged.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_performance_set_plan_report_help():
    from .reports.dual_machine_style_performance_set_plan import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-performance-set-plan-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --analog-four <syx-path> --scope analog-four-only
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --scope dual|rytm-only|analog-four-only|a4-only
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report --help

Behavior:
  Reads local Analog Rytm MK2 and/or Analog Four MK2 SysEx kit banks, runs the
  ranked style selection mock preview for each requested style, and prints a
  timed passive performance set plan. Use --total-minutes N for an evenly
  divided full set, --segment-minutes N for fixed segment lengths, and
  --discovery-start/--discovery-end to ramp the reference/discovery pressure
  across the set. Single-machine scopes leave the other machine unchanged.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_snapshot_routing_report_help():
    from .reports.dual_machine_style_snapshot_routing import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-snapshot-routing-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key>
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> --rytm-slot N
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> --a4-slot N
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> --json
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report --help

Behavior:
  Reads one local Analog Rytm MK2 SysEx file and one local Analog Four MK2 SysEx
  file, selects supported kit snapshots, and prints passive rig-level style
  routing readiness. Detailed pad/track rows remain in the single-machine reports.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_mutation_intent_report_help():
    from .reports.dual_machine_style_mutation_intent import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-mutation-intent-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key>
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key> --rytm-slot N
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key> --a4-slot N
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key> --json
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report --help

Behavior:
  Reads one local Analog Rytm MK2 SysEx file and one local Analog Four MK2 SysEx
  file, selects supported kit snapshots, and prints passive rig-level style
  mutation intent. Detailed pad/track intent rows are included in --json for
  future GUI/analyzer consumers, but no mutation values are rendered.
  Use --discovery N (0-100) to choose reference, balanced, discovery, or wild-discovery planning pressure.
  Use --json for a deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _dual_machine_style_mutation_mock_preview_report_help():
    from .reports.dual_machine_style_mutation_mock_preview import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: dual-machine-style-mutation-mock-preview-report

Usage:
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key>
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --rytm-slot N
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --a4-slot N
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --discovery N
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --events
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --events --limit N
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> --json
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report --help

Behavior:
  Reads one local Analog Rytm MK2 SysEx file and one local Analog Four MK2 SysEx
  file, selects supported kit snapshots, and prints passive rig-level style
  mock CC rows. Rytm rows are rendered through the existing Rytm mock renderer;
  A4 decoded snapshots remain candidate-only until offsets are promoted, and
  NRPN-only A4 zones are listed as deferred. Use --events to include combined
  mock CC rows; --limit N caps rows and N=0 prints all rows. Use --json for a
  deterministic machine-readable payload for future GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_profile_report_help():
    from .reports.style_profiles import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-profile-report

Usage:
  python -m rytm_randomizer.cli style-profile-report
  python -m rytm_randomizer.cli style-profile-report --help

Behavior:
  Prints the passive style-profile catalog for techno design intent.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_target_report_help():
    from .reports.style_targets import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-target-report

Usage:
  python -m rytm_randomizer.cli style-target-report
  python -m rytm_randomizer.cli style-target-report --help

Behavior:
  Prints passive numeric style target vectors for future snapshot planning.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_report_help():
    from .reports.style_performance_arcs import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-report
  python -m rytm_randomizer.cli style-performance-arc-report --help

Behavior:
  Prints passive reference/performance arc presets for long-form set planning.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_set_plan_report_help():
    from .reports.style_performance_arcs import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-set-plan-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report --help

Behavior:
  Expands a named passive reference arc into a timed performance set plan.
  The command reuses the dual-machine style performance planner, so it can
  rank saved kits, apply the arc's default discovery ramp, and show optional
  mock event rows without opening a MIDI port or sending MIDI.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_readiness_report_help():
    from .reports.style_performance_arcs import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-readiness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-readiness-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm <syx-path> --limit N
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-readiness-report --help

Behavior:
  Ranks named passive reference arcs against saved kit banks.
  With no arc keys it ranks every curated reference arc. The report reuses
  the dual-machine performance planner to summarize ready, partial, and
  blocked arcs before any armed live path exists.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_audition_packet_report_help():
    from .reports.style_performance_arcs import AUDITION_PACKET_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-audition-packet-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report --help

Behavior:
  Builds a passive best-arc audition packet from saved kit banks.
  With no arc keys it evaluates every curated reference arc, chooses the
  highest-ranked ready or partial arc, and embeds the selected timed set-plan
  preview so an operator can start an audition from one report.

Safety:
{_safety_block(AUDITION_PACKET_SAFETY_LINES)}"""


def _style_performance_arc_rehearsal_manifest_report_help():
    from .reports.style_performance_arcs import REHEARSAL_MANIFEST_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-rehearsal-manifest-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report --help

Behavior:
  Builds a passive rehearsal manifest from saved kit banks.
  With no arc keys it evaluates every curated reference arc, chooses the
  highest-ranked ready or partial arc, and turns the selected timed set plan
  into preflight checks plus a segment-by-segment live rehearsal runbook.

Safety:
{_safety_block(REHEARSAL_MANIFEST_SAFETY_LINES)}"""


def _style_performance_arc_live_session_packet_report_help():
    from .reports.style_performance_arcs import LIVE_SESSION_PACKET_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-session-packet-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --help

Behavior:
  Builds a passive live rehearsal session packet from saved kit banks.
  With no arc keys it evaluates every curated reference arc, chooses the
  highest-ranked ready or partial arc, and turns the selected rehearsal
  manifest into a launch checklist, passive command list, and segment cards.

Safety:
{_safety_block(LIVE_SESSION_PACKET_SAFETY_LINES)}"""


def _style_performance_arc_live_render_bundle_report_help():
    from .reports.style_performance_arcs import LIVE_RENDER_BUNDLE_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-render-bundle-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report --help

Behavior:
  Builds a passive live render bundle from saved kit banks.
  With no arc keys it evaluates every curated reference arc, chooses the
  highest-ranked ready or partial arc, and turns the selected live-session
  packet into segment-level mock render previews and deferred A4 rows.

Safety:
{_safety_block(LIVE_RENDER_BUNDLE_SAFETY_LINES)}"""


def _style_performance_arc_live_cue_sheet_report_help():
    from .reports.style_performance_arcs import LIVE_CUE_SHEET_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-cue-sheet-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report <arc-key> <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm <syx-path> --scope rytm-only
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --rytm <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --help

Behavior:
  Builds a passive live performance cue sheet from saved kit banks.
  With no arc keys it evaluates every curated reference arc, chooses the
  highest-ranked ready or partial arc, consumes the selected live render
  bundle, and produces per-segment operator cues, risk labels, hands-on moves,
  recovery actions, and optional capped mock render row previews.

Safety:
{_safety_block(LIVE_CUE_SHEET_SAFETY_LINES)}"""


def _style_performance_arc_reference_match_report_help():
    from .reports.style_performance_arcs import REFERENCE_MATCH_SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-reference-match-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --description <text>
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --audio <path>
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --library <dir>
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --description <text> --json
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report --help

Behavior:
  Matches a reference description or FeatureReport to performance arcs.
  The report converts description, audio, or library features into bounded
  style-axis evidence, ranks curated performance arcs, and can embed the
  selected live cue sheet when saved-kit paths are supplied. When snapshots
  are present, it also summarizes the reference-selected snapshot preview:
  selected arc, readiness, mock/deferred totals, planned Rytm pads, planned
  Analog Four tracks, and passive operator action. Saved-kit references also
  expose a stage packet with compact cue cards, planned pads/tracks, risk
  labels, recovery actions, and a passive operator handoff. This is an
  influence-not-replica reference-match report for future GUI/audio-analyzer
  routing.

Safety:
{_safety_block(REFERENCE_MATCH_SAFETY_LINES)}"""


def resolve_help_text(key: str) -> str:
    text = HELP_TEXT[key]
    return text() if callable(text) else text


HELP_TEXT = {
    "--help": """RytmRandomizer passive CLI

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli project-status-report
  python -m rytm_randomizer.cli project-status-report --summary
  python -m rytm_randomizer.cli project-status-report --json
  python -m rytm_randomizer.cli project-status-report --check
  python -m rytm_randomizer.cli mock-mapper-report
  python -m rytm_randomizer.cli runtime-plan-report
  python -m rytm_randomizer.cli active-boundary-report
  python -m rytm_randomizer.cli mock-runtime-active-bridge-report
  python -m rytm_randomizer.cli anchor-profile-report
  python -m rytm_randomizer.cli behavior-parity-report
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
  python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path>
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path> --list
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path> --slot N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path>
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --slot N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --depth N
  python -m rytm_randomizer.cli rytm-snapshot-mutation-preview-report <syx-path> --events
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> [--slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli rytm-style-mutation-intent-report <syx-path> <style-key> [--slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli rytm-style-mutation-render-plan-report <syx-path> <style-key> [--slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli rytm-style-mutation-mock-preview-report <syx-path> <style-key> [--slot N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli rytm-style-kit-readiness-report <syx-path> <style-key> [--discovery N] [--limit N] [--json]
  python -m rytm_randomizer.cli analog-four-style-snapshot-routing-report <syx-path> <style-key> [--slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli analog-four-style-mutation-intent-report <syx-path> <style-key> [--slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli analog-four-style-mutation-mock-preview-report <syx-path> <style-key> [--slot N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli analog-four-kit-catalog-report <syx-path> [--limit N] [--json]
  python -m rytm_randomizer.cli analog-four-style-kit-readiness-report <syx-path> <style-key> [--discovery N] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key> [--discovery N] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-kit-selection-report <style-key> --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--discovery N] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-live-audition-report <style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-performance-set-plan-report <style-key> [<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> <style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json]
  python -m rytm_randomizer.cli dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> <style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli dual-machine-target-report <rytm|a4|both>
  python -m rytm_randomizer.cli style-profile-report
  python -m rytm_randomizer.cli list-style-profiles
  python -m rytm_randomizer.cli inspect-style-profile <key>
  python -m rytm_randomizer.cli search-style-profiles <query>
  python -m rytm_randomizer.cli style-target-report
  python -m rytm_randomizer.cli inspect-style-target <key>
  python -m rytm_randomizer.cli style-performance-arc-report
  python -m rytm_randomizer.cli list-style-performance-arcs
  python -m rytm_randomizer.cli inspect-style-performance-arc <key>
  python -m rytm_randomizer.cli search-style-performance-arcs <query>
  python -m rytm_randomizer.cli style-performance-arc-set-plan-report <arc-key> --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-readiness-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-audition-packet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-rehearsal-manifest-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-render-bundle-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli inspect-group-profile <key>
  python -m rytm_randomizer.cli list-commands
  python -m rytm_randomizer.cli list-scenes
  python -m rytm_randomizer.cli list-group-profiles
  python -m rytm_randomizer.cli search-commands <query>
  python -m rytm_randomizer.cli search-scenes <query>
  python -m rytm_randomizer.cli search-group-profiles <query>
  python -m rytm_randomizer.cli preview-command <key>
  python -m rytm_randomizer.cli preview-scene <key>
  python -m rytm_randomizer.cli preview-group-profile <key>
  python -m rytm_randomizer.cli --help

Commands:
  report             Print the passive registry report.
  project-status-report
                     Print the read-only project status report.
  mock-mapper-report
                     Print the passive mock mapper report.
  runtime-plan-report
                     Print the read-only runtime plan report.
  active-boundary-report
                     Print the read-only active boundary report.
  mock-runtime-active-bridge-report
                     Print the read-only mock runtime/active bridge report.
  anchor-profile-report
                     Print the read-only anchor/profile behavior report.
  behavior-parity-report
                     Print the read-only behavior-parity coverage report.
  rytm-12-pad-machine-matrix-report
                     Print the passive Rytm 12-pad machine matrix report.
  rytm-snapshot-pad-compatibility-report
                     Print the passive Rytm snapshot-pad compatibility report.
  rytm-snapshot-intelligence-report
                     Print passive Rytm snapshot intelligence for a SysEx file.
  rytm-snapshot-mutation-preview-report
                     Print passive Rytm snapshot mutation preview for a SysEx file.
  rytm-style-snapshot-routing-report
                     Print passive Rytm style snapshot routing for a SysEx file.
  rytm-style-mutation-intent-report
                     Print passive Rytm style mutation intent for a SysEx file.
  rytm-style-mutation-render-plan-report
                     Print passive Rytm style mutation render-plan metadata for a SysEx file.
  rytm-style-mutation-mock-preview-report
                     Print passive Rytm style mutation mock-preview rows for a SysEx file.
  rytm-style-kit-readiness-report
                     Print passive Rytm style readiness for every decoded kit.
  analog-four-style-snapshot-routing-report
                     Print passive Analog Four style snapshot routing for a SysEx file.
  analog-four-style-mutation-intent-report
                     Print passive Analog Four style mutation intent for a SysEx file.
  analog-four-style-mutation-mock-preview-report
                     Print passive Analog Four style mutation mock-preview rows for a SysEx file.
  analog-four-kit-catalog-report
                     Print passive Analog Four kit catalog metadata for a SysEx file.
  analog-four-style-kit-readiness-report
                     Print passive Analog Four style readiness for every decoded kit.
  dual-machine-style-kit-readiness-report
                     Print passive dual-machine style readiness across Rytm and A4 kit banks.
  dual-machine-style-kit-selection-report
                     Print passive style kit selections for Rytm, A4, or both machines.
  dual-machine-style-selection-mock-preview-report
                     Print passive mock previews from ranked style kit selections.
  dual-machine-style-live-audition-report
                     Print passive live-audition plans from multiple style selections.
  dual-machine-style-performance-set-plan-report
                     Print passive timed performance set plans from style selections.
  dual-machine-style-snapshot-routing-report
                     Print passive dual-machine style snapshot routing for Rytm and A4 SysEx files.
  dual-machine-style-mutation-intent-report
                     Print passive dual-machine style mutation intent for Rytm and A4 SysEx files.
  dual-machine-style-mutation-mock-preview-report
                     Print passive dual-machine style mutation mock-preview rows for Rytm and A4.
  dual-machine-target-report
                     Print the passive dual-machine target report.
  style-profile-report
                     Print the passive style profile report.
  list-style-profiles
                     List passive style profile keys and names.
  inspect-style-profile
                     Inspect passive style profile metadata by key.
  search-style-profiles
                     Search passive style profile metadata.
  style-target-report
                     Print the passive style target vector report.
  inspect-style-target
                     Inspect passive style target vector metadata by key.
  style-performance-arc-report
                     Print the passive style performance arc report.
  list-style-performance-arcs
                     List passive style performance arc keys and names.
  inspect-style-performance-arc
                     Inspect passive style performance arc metadata by key.
  search-style-performance-arcs
                     Search passive style performance arc metadata.
  style-performance-arc-set-plan-report
                     Print passive timed performance set plans from a reference arc.
  style-performance-arc-readiness-report
                     Rank passive reference arcs against saved kit banks.
  style-performance-arc-audition-packet-report
                     Build passive best-arc audition packets from saved kit banks.
  style-performance-arc-rehearsal-manifest-report
                     Build passive reference-arc rehearsal manifests from saved kit banks.
  style-performance-arc-live-session-packet-report
                     Build passive live rehearsal session packets from saved kit banks.
  style-performance-arc-live-render-bundle-report
                     Build passive live render bundles from saved kit banks.
  style-performance-arc-live-cue-sheet-report
                     Build passive live performance cue sheets from saved kit banks.
  style-performance-arc-reference-match-report
                     Match references to arcs, cue sheets, snapshot previews, and stage packets.
  inspect-command    Inspect passive command metadata by key.
  inspect-scene      Inspect passive scene metadata by key.
  inspect-group-profile
                     Inspect passive group profile metadata by key.
  list-commands      List passive command keys and labels.
  list-scenes        List passive scene keys and names.
  list-group-profiles
                     List passive group profile keys and names.
  search-commands    Search passive command metadata.
  search-scenes      Search passive scene metadata.
  search-group-profiles
                     Search passive group profile metadata.
  preview-command    Preview passive command metadata by key.
  preview-scene      Preview passive scene metadata by key.
  preview-group-profile
                     Preview passive group profile metadata by key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "report": """RytmRandomizer passive CLI: report

Usage:
  python -m rytm_randomizer.cli report
  python -m rytm_randomizer.cli report --help

Behavior:
  Prints the deterministic passive registry report to stdout.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "project-status-report": """RytmRandomizer passive CLI: project-status-report

Usage:
  python -m rytm_randomizer.cli project-status-report
  python -m rytm_randomizer.cli project-status-report --summary
  python -m rytm_randomizer.cli project-status-report --json
  python -m rytm_randomizer.cli project-status-report --check
  python -m rytm_randomizer.cli project-status-report --help

Behavior:
  Prints the deterministic read-only project status report to stdout.
  With --summary, prints a compact one-screen status summary.
  With --json, prints the same passive report as deterministic JSON.
  With --check, validates passive safety invariants and exits nonzero on failure.

Safety:
  passive/read-only
  mock-only visibility
  no MIDI sending
  no port opening
  no runtime execution
  no command execution
  no dispatch
  no hardware mutation
  no hardware required""",
    "mock-mapper-report": """RytmRandomizer passive CLI: mock-mapper-report

Usage:
  python -m rytm_randomizer.cli mock-mapper-report
  python -m rytm_randomizer.cli mock-mapper-report --help

Behavior:
  Prints the deterministic passive mock mapper report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "runtime-plan-report": """RytmRandomizer passive CLI: runtime-plan-report

Usage:
  python -m rytm_randomizer.cli runtime-plan-report
  python -m rytm_randomizer.cli runtime-plan-report --help

Behavior:
  Prints the deterministic read-only runtime plan report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no runtime execution
  no command execution
  no dispatch
  no hardware mutation
  no hardware required""",
    "active-boundary-report": """RytmRandomizer passive CLI: active-boundary-report

Usage:
  python -m rytm_randomizer.cli active-boundary-report
  python -m rytm_randomizer.cli active-boundary-report --help

Behavior:
  Prints the deterministic read-only active boundary report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no active execution
  no command execution
  no hardware mutation
  no hardware required""",
    "mock-runtime-active-bridge-report": """RytmRandomizer passive CLI: mock-runtime-active-bridge-report

Usage:
  python -m rytm_randomizer.cli mock-runtime-active-bridge-report
  python -m rytm_randomizer.cli mock-runtime-active-bridge-report --help

Behavior:
  Prints the deterministic read-only mock runtime/active bridge report to stdout.

Safety:
  passive/read-only
  mock-only
  no bridge invocation
  no sender construction
  no message emission
  no MIDI sending
  no port opening
  no runtime execution
  no command execution
  no dispatch
  no hardware mutation
  no hardware required""",
    "anchor-profile-report": """RytmRandomizer passive CLI: anchor-profile-report

Usage:
  python -m rytm_randomizer.cli anchor-profile-report
  python -m rytm_randomizer.cli anchor-profile-report --help

Behavior:
  Prints the deterministic read-only anchor/profile behavior report to stdout.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no runtime state
  no hardware mutation
  no hardware required""",
    "behavior-parity-report": """RytmRandomizer passive CLI: behavior-parity-report

Usage:
  python -m rytm_randomizer.cli behavior-parity-report
  python -m rytm_randomizer.cli behavior-parity-report --help

Behavior:
  Prints the deterministic read-only behavior-parity coverage report to stdout.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "rytm-12-pad-machine-matrix-report": """RytmRandomizer passive CLI: rytm-12-pad-machine-matrix-report

Usage:
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report --help

Behavior:
  Prints the passive Analog Rytm MK2 12-pad machine compatibility matrix.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "rytm-snapshot-pad-compatibility-report": _rytm_snapshot_pad_compatibility_report_help,
    "rytm-snapshot-intelligence-report": _rytm_snapshot_intelligence_report_help,
    "rytm-snapshot-mutation-preview-report": _rytm_snapshot_mutation_preview_report_help,
    "rytm-style-snapshot-routing-report": _rytm_style_snapshot_routing_report_help,
    "rytm-style-mutation-intent-report": _rytm_style_mutation_intent_report_help,
    "rytm-style-mutation-render-plan-report": _rytm_style_mutation_render_plan_report_help,
    "rytm-style-mutation-mock-preview-report": _rytm_style_mutation_mock_preview_report_help,
    "rytm-style-kit-readiness-report": _rytm_style_kit_readiness_report_help,
    "analog-four-style-snapshot-routing-report": _analog_four_style_snapshot_routing_report_help,
    "analog-four-style-mutation-intent-report": _analog_four_style_mutation_intent_report_help,
    "analog-four-style-mutation-mock-preview-report": (
        _analog_four_style_mutation_mock_preview_report_help
    ),
    "analog-four-kit-catalog-report": _analog_four_kit_catalog_report_help,
    "analog-four-style-kit-readiness-report": _analog_four_style_kit_readiness_report_help,
    "dual-machine-style-kit-readiness-report": _dual_machine_style_kit_readiness_report_help,
    "dual-machine-style-kit-selection-report": _dual_machine_style_kit_selection_report_help,
    "dual-machine-style-selection-mock-preview-report": (
        _dual_machine_style_selection_mock_preview_report_help
    ),
    "dual-machine-style-live-audition-report": _dual_machine_style_live_audition_report_help,
    "dual-machine-style-performance-set-plan-report": (
        _dual_machine_style_performance_set_plan_report_help
    ),
    "dual-machine-style-snapshot-routing-report": _dual_machine_style_snapshot_routing_report_help,
    "dual-machine-style-mutation-intent-report": _dual_machine_style_mutation_intent_report_help,
    "dual-machine-style-mutation-mock-preview-report": (
        _dual_machine_style_mutation_mock_preview_report_help
    ),
    "style-profile-report": _style_profile_report_help,
    "style-target-report": _style_target_report_help,
    "style-performance-arc-report": _style_performance_arc_report_help,
    "style-performance-arc-set-plan-report": _style_performance_arc_set_plan_report_help,
    "style-performance-arc-readiness-report": (_style_performance_arc_readiness_report_help),
    "style-performance-arc-audition-packet-report": (
        _style_performance_arc_audition_packet_report_help
    ),
    "style-performance-arc-rehearsal-manifest-report": (
        _style_performance_arc_rehearsal_manifest_report_help
    ),
    "style-performance-arc-live-session-packet-report": (
        _style_performance_arc_live_session_packet_report_help
    ),
    "style-performance-arc-live-render-bundle-report": (
        _style_performance_arc_live_render_bundle_report_help
    ),
    "style-performance-arc-live-cue-sheet-report": (
        _style_performance_arc_live_cue_sheet_report_help
    ),
    "style-performance-arc-reference-match-report": (
        _style_performance_arc_reference_match_report_help
    ),
    "dual-machine-target-report": """RytmRandomizer passive CLI: dual-machine-target-report

Usage:
  python -m rytm_randomizer.cli dual-machine-target-report <rytm|a4|both>
  python -m rytm_randomizer.cli dual-machine-target-report --help

Behavior:
  Prints the passive dual-machine target report to stdout.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "list-commands": """RytmRandomizer passive CLI: list-commands

Usage:
  python -m rytm_randomizer.cli list-commands
  python -m rytm_randomizer.cli list-commands --help

Behavior:
  Lists existing passive command keys and labels.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "list-scenes": """RytmRandomizer passive CLI: list-scenes

Usage:
  python -m rytm_randomizer.cli list-scenes
  python -m rytm_randomizer.cli list-scenes --help

Behavior:
  Lists existing passive scene keys and names.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "list-group-profiles": """RytmRandomizer passive CLI: list-group-profiles

Usage:
  python -m rytm_randomizer.cli list-group-profiles
  python -m rytm_randomizer.cli list-group-profiles --help

Behavior:
  Lists existing passive group profile keys and names.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "list-style-profiles": """RytmRandomizer passive CLI: list-style-profiles

Usage:
  python -m rytm_randomizer.cli list-style-profiles
  python -m rytm_randomizer.cli list-style-profiles --help

Behavior:
  Lists passive style profile keys and names.

Safety:
  passive/read-only
  metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-style-profile": """RytmRandomizer passive CLI: inspect-style-profile

Usage:
  python -m rytm_randomizer.cli inspect-style-profile <key>
  python -m rytm_randomizer.cli inspect-style-profile --help

Behavior:
  Displays passive style profile metadata for an existing key.

Safety:
  passive/read-only
  metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "search-style-profiles": """RytmRandomizer passive CLI: search-style-profiles

Usage:
  python -m rytm_randomizer.cli search-style-profiles <query>
  python -m rytm_randomizer.cli search-style-profiles --help

Behavior:
  Searches passive style profile metadata.

Safety:
  passive/read-only
  metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "list-style-performance-arcs": """RytmRandomizer passive CLI: list-style-performance-arcs

Usage:
  python -m rytm_randomizer.cli list-style-performance-arcs
  python -m rytm_randomizer.cli list-style-performance-arcs --help

Behavior:
  Lists passive reference/performance arc preset keys and names.

Safety:
  passive/read-only
  metadata and plan expansion only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-style-performance-arc": """RytmRandomizer passive CLI: inspect-style-performance-arc

Usage:
  python -m rytm_randomizer.cli inspect-style-performance-arc <key>
  python -m rytm_randomizer.cli inspect-style-performance-arc --help

Behavior:
  Displays passive reference/performance arc metadata for an existing key.

Safety:
  passive/read-only
  metadata and plan expansion only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "search-style-performance-arcs": """RytmRandomizer passive CLI: search-style-performance-arcs

Usage:
  python -m rytm_randomizer.cli search-style-performance-arcs <query>
  python -m rytm_randomizer.cli search-style-performance-arcs --help

Behavior:
  Searches passive reference/performance arc metadata.

Safety:
  passive/read-only
  metadata and plan expansion only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-style-target": """RytmRandomizer passive CLI: inspect-style-target

Usage:
  python -m rytm_randomizer.cli inspect-style-target <key>
  python -m rytm_randomizer.cli inspect-style-target --help

Behavior:
  Displays passive numeric style target vector metadata for an existing key.

Safety:
  passive/read-only
  metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "search-commands": """RytmRandomizer passive CLI: search-commands

Usage:
  python -m rytm_randomizer.cli search-commands <query>
  python -m rytm_randomizer.cli search-commands --help

Behavior:
  Searches existing passive command metadata.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "search-scenes": """RytmRandomizer passive CLI: search-scenes

Usage:
  python -m rytm_randomizer.cli search-scenes <query>
  python -m rytm_randomizer.cli search-scenes --help

Behavior:
  Searches existing passive scene metadata.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "search-group-profiles": """RytmRandomizer passive CLI: search-group-profiles

Usage:
  python -m rytm_randomizer.cli search-group-profiles <query>
  python -m rytm_randomizer.cli search-group-profiles --help

Behavior:
  Searches existing passive group profile metadata.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "preview-command": """RytmRandomizer passive CLI: preview-command

Usage:
  python -m rytm_randomizer.cli preview-command <key>
  python -m rytm_randomizer.cli preview-command --help

Behavior:
  Displays a passive dry-run preview for an existing command key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "preview-scene": """RytmRandomizer passive CLI: preview-scene

Usage:
  python -m rytm_randomizer.cli preview-scene <key>
  python -m rytm_randomizer.cli preview-scene --help

Behavior:
  Displays a passive dry-run preview for an existing scene key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no scene execution
  no command execution
  no hardware mutation
  no hardware required""",
    "preview-group-profile": """RytmRandomizer passive CLI: preview-group-profile

Usage:
  python -m rytm_randomizer.cli preview-group-profile <key>
  python -m rytm_randomizer.cli preview-group-profile --help

Behavior:
  Displays a passive dry-run preview for an existing group profile key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-command": """RytmRandomizer passive CLI: inspect-command

Usage:
  python -m rytm_randomizer.cli inspect-command <key>
  python -m rytm_randomizer.cli inspect-command --help

Behavior:
  Displays passive metadata for an existing command key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-scene": """RytmRandomizer passive CLI: inspect-scene

Usage:
  python -m rytm_randomizer.cli inspect-scene <key>
  python -m rytm_randomizer.cli inspect-scene --help

Behavior:
  Displays passive metadata for an existing scene key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "inspect-group-profile": """RytmRandomizer passive CLI: inspect-group-profile

Usage:
  python -m rytm_randomizer.cli inspect-group-profile <key>
  python -m rytm_randomizer.cli inspect-group-profile --help

Behavior:
  Displays passive metadata for an existing group profile key.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
}
