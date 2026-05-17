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
    "anchor-profile-report | behavior-parity-report | performance-snapshot-target-report --target <target> | sysex-kit-bank-report <path> | "
    "sysex-project-report <path> | sysex-kit-snapshot-report <path> --slot <1-128> | "
    "sysex-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "rytm-controlled-diff-report <before> <after> --slot <1-128> (--pad <1-12>|--all-pads) --limit <n> | "
    "dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] | "
    "dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] | "
    "dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] | "
    "dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> [--analog-four-path <path> --analog-four-slot <slot>] [--target <target>] | "
    "analog-four-kit-snapshot-report <path> --slot <1-128> | "
    "analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong> | "
    "analog-four-offset-candidate-report <path> (--track <1-4>|--all-tracks) --limit <n> | "
    "analog-four-controlled-diff-report <before> <after> --slot <1-128> --track <1-4> --limit <n> | "
    "essence-plan-report (--tags <csv>|--description <text>) --discovery <0..1> | inspect-command <key> | "
    "essence-application-readiness-report --mode <mode> (--tags <csv>|--description <text>|--style <text>) [--discovery <0..1>] [--snapshot <status>|--fixture <key>] | "
    "style-intent-report --style <text> [--discovery <0..1>] | "
    "snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>] | "
    "twelve-pad-mock-runtime-report --style <text> [--discovery <0..1>] | "
    "analog-four-reference-report | "
    "inspect-scene <key> | inspect-group-profile <key> | list-commands | "
    "list-scenes | list-group-profiles | search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | preview-command <key> | "
    "preview-scene <key> | preview-group-profile <key>"
)

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
  python -m rytm_randomizer.cli performance-snapshot-target-report --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli sysex-kit-bank-report <path>
  python -m rytm_randomizer.cli sysex-project-report <path>
  python -m rytm_randomizer.cli sysex-kit-snapshot-report <path> --slot <1-128>
  python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli rytm-controlled-diff-report <before> <after> --slot <1-128> --pad <1-12> --limit <n>
  python -m rytm_randomizer.cli rytm-controlled-diff-report <before> <after> --slot <1-128> --all-pads --limit <n>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report <path> --slot <1-128>
  python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli analog-four-offset-candidate-report <path> --track <1-4> --limit <n>
  python -m rytm_randomizer.cli analog-four-offset-candidate-report <path> --all-tracks --limit <n>
  python -m rytm_randomizer.cli analog-four-controlled-diff-report <before> <after> --slot <1-128> --track <1-4> --limit <n>
  python -m rytm_randomizer.cli essence-plan-report --tags <csv> --discovery <0..1>
  python -m rytm_randomizer.cli essence-plan-report --description <text> --discovery <0..1>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode <mode> --tags <csv> --discovery <0..1>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode <mode> --description <text> --discovery <0..1>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description <text> --discovery <0..1> --fixture <key>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --style <text> --fixture <key>
  python -m rytm_randomizer.cli style-intent-report --style <text>
  python -m rytm_randomizer.cli style-intent-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style <text>
  python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli analog-four-reference-report
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
  performance-snapshot-target-report
                     Preview which machine(s) Live Snapshot may touch.
  sysex-kit-bank-report
                     Analyze a saved SysEx kit bank file without touching hardware.
  sysex-project-report
                     Analyze a saved whole-project SysEx dump without touching hardware.
  sysex-kit-snapshot-report
                     Decode a saved Rytm kit slot into a passive 12-pad snapshot.
  sysex-snapshot-mutation-plan-report
                     Plan passive captured-value mutations from a saved kit snapshot.
  sysex-snapshot-mock-runtime-report
                     Capture snapshot-plan CC moves into an inert mock sender.
  rytm-controlled-diff-report
                     Compare two saved Rytm kit exports for changed pad parameters.
  dual-machine-mock-bridge-report
                     Preview a combined Rytm + Analog Four mock performance stream.
  dual-machine-live-snapshot-readiness-report
                     Gate a dual-machine bridge before future live sending.
  dual-machine-active-send-plan-report
                     Preview mapped CC events eligible for future active sending.
  dual-machine-guarded-send-dry-run-report
                     Execute eligible send-plan events into a mock sender only.
  analog-four-kit-snapshot-report
                     Decode a saved Analog Four kit into a passive track snapshot.
  analog-four-snapshot-mutation-plan-report
                     Plan passive A4 captured-value saved-offset mutations.
  analog-four-snapshot-mock-runtime-report
                     Capture A4 saved-offset candidates into inert mock events.
  analog-four-offset-candidate-report
                     Scan saved Analog Four kits for unverified offset candidates.
  analog-four-controlled-diff-report
                     Compare two saved Analog Four kit exports for changed offsets.
  essence-plan-report
                     Preview a 12-pad engine plan from essence tags or a description.
  essence-application-readiness-report
                     Explain whether an essence plan is apply-ready by mode.
  style-intent-report
                     Preview a 12-pad kit plan from broad style/genre intent.
  snapshot-essence-overlay-report
                     Compare a saved Rytm snapshot to a style-driven 12-pad machine plan.
  snapshot-essence-send-plan-report
                     Preview passive CC events from a saved snapshot and style plan.
  snapshot-essence-guarded-send-dry-run-report
                     Execute snapshot essence send-plan events into a mock sender only.
  twelve-pad-mock-runtime-report
                     Preview mapped-only 12-pad mock runtime CC messages.
  analog-four-reference-report
                     Print the passive Analog Four MKII reference intake report.
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
    "performance-snapshot-target-report": """RytmRandomizer passive CLI: performance-snapshot-target-report

Usage:
  python -m rytm_randomizer.cli performance-snapshot-target-report --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli performance-snapshot-target-report --help

Behavior:
  Prints a passive Live Snapshot target-scope report. The selected target is
  active for future capture, mutation, and restore. Machines outside the target
  are marked untouched and must receive no capture request, no CC messages, no
  SysEx restore, and no machine changes.

Safety:
  passive/read-only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "sysex-kit-bank-report": """RytmRandomizer passive CLI: sysex-kit-bank-report

Usage:
  python -m rytm_randomizer.cli sysex-kit-bank-report <path>
  python -m rytm_randomizer.cli sysex-kit-bank-report --help

Behavior:
  Reads an existing SysEx kit bank file and prints passive record metadata.
  It does not request dumps, decode editable parameters, write SysEx, or touch hardware.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no SysEx writes
  no hardware required""",
    "sysex-project-report": """RytmRandomizer passive CLI: sysex-project-report

Usage:
  python -m rytm_randomizer.cli sysex-project-report <path>
  python -m rytm_randomizer.cli sysex-project-report --help

Behavior:
  Reads an existing whole-project SysEx dump and prints passive record groups
  for kits, sounds, patterns, project settings, and global-like records. It
  does not request dumps, receive live SysEx, decode editable parameters,
  write SysEx, or touch hardware.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "sysex-kit-snapshot-report": """RytmRandomizer passive CLI: sysex-kit-snapshot-report

Usage:
  python -m rytm_randomizer.cli sysex-kit-snapshot-report <path> --slot <1-128>
  python -m rytm_randomizer.cli sysex-kit-snapshot-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, selects one kit
  slot, unpacks its saved Elektron 7-bit payload, and prints a 12-pad snapshot
  inventory with machine IDs and saved parameter baselines where mapped.
  It does not request dumps, receive live SysEx, send MIDI, write SysEx, or
  touch hardware.

Safety:
  passive/read-only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "sysex-snapshot-mutation-plan-report": """RytmRandomizer passive CLI: sysex-snapshot-mutation-plan-report

Usage:
  python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, decodes one kit
  slot through the saved snapshot decoder, and prints a passive mutation plan
  using bounded deterministic deltas from the captured parameter values. It does
  not load anchors, switch machines, send MIDI, write SysEx, or touch hardware.

Safety:
  passive/read-only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "sysex-snapshot-mock-runtime-report": """RytmRandomizer passive CLI: sysex-snapshot-mock-runtime-report

Usage:
  python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, builds the
  captured-value snapshot mutation plan, and captures the planned CC moves into
  an inert mock sender. It does not open ports, send MIDI, write SysEx, or touch
  hardware.

Safety:
  passive/read-only
  mock sender only
  captured-value relative
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "rytm-controlled-diff-report": """RytmRandomizer passive CLI: rytm-controlled-diff-report

Usage:
  python -m rytm_randomizer.cli rytm-controlled-diff-report <before> <after> --slot <1-128> --pad <1-12> --limit <n>
  python -m rytm_randomizer.cli rytm-controlled-diff-report <before> <after> --slot <1-128> --all-pads --limit <n>
  python -m rytm_randomizer.cli rytm-controlled-diff-report --help

Behavior:
  Reads two existing Rytm kit bank or whole-project SysEx files, selects the
  same saved kit slot and either one pad or all 12 pads from each file, and
  reports changed decoded saved parameters. This is for controlled before/after
  mapping sessions. It does not request dumps, receive live SysEx, send MIDI,
  write SysEx, or touch hardware.

Safety:
  passive/read-only
  controlled comparison only
  mapped saved parameters only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "dual-machine-mock-bridge-report": """RytmRandomizer passive CLI: dual-machine-mock-bridge-report

Usage:
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-mock-bridge-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file and previews a
  combined Rytm + Analog Four mock sender stream. The Rytm side mutates from
  saved captured values. By default, the Analog Four side uses the conservative
  safe-starter CC plan from validated Track 1-4 smoke tests. Supplying
  --analog-four-path and --analog-four-slot switches the Analog Four side to
  saved-offset candidate events from that saved snapshot; those events are
  candidate_unverified and no CC mapping is claimed. Optional --target limits
  the mock stream to Rytm only, Analog Four only, or both; untouched devices
  produce no mock messages. It does not send MIDI, open ports, request dumps,
  write SysEx, or touch hardware.

Safety:
  passive/read-only
  mock sender only
  optional Analog Four saved-offset candidate events
  no CC mapping claimed for Analog Four snapshot candidates
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "dual-machine-live-snapshot-readiness-report": """RytmRandomizer passive CLI: dual-machine-live-snapshot-readiness-report

Usage:
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report --help

Behavior:
  Builds the passive dual-machine mock bridge, then reports a readiness gate
  for future live snapshot sending. Mapped CC mock messages can be marked ready;
  Analog Four saved-offset candidate events are blocked as candidate_unverified
  because no CC mapping is claimed. This command never sends MIDI or opens a
  port.

Safety:
  passive/read-only
  readiness gate only
  candidate_unverified events block hardware sending
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "dual-machine-active-send-plan-report": """RytmRandomizer passive CLI: dual-machine-active-send-plan-report

Usage:
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-active-send-plan-report --help

Behavior:
  Builds the passive dual-machine mock bridge, then prints an active send plan
  preview for future guarded hardware sending. Mapped CC mock messages are
  listed as eligible; saved-offset candidate events are blocked because no CC
  mapping is claimed. This command never sends MIDI or opens a port.

Safety:
  passive/read-only
  active send plan preview only
  saved-offset candidate events are blocked
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "dual-machine-guarded-send-dry-run-report": """RytmRandomizer passive CLI: dual-machine-guarded-send-dry-run-report

Usage:
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
  python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report --help

Behavior:
  Builds the passive dual-machine active send plan, then runs the guarded send
  dry-run into an inert mock sender. Ready target scopes emit mapped CC mock
  messages. Blocked plans emit no partial messages. This command never sends
  MIDI or opens a port.

Safety:
  passive/read-only
  guarded send dry-run only
  mock sender only
  blocked plans emit no partial messages
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-kit-snapshot-report": """RytmRandomizer passive CLI: analog-four-kit-snapshot-report

Usage:
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report <path> --slot <1-128>
  python -m rytm_randomizer.cli analog-four-kit-snapshot-report --help

Behavior:
  Reads an existing Analog Four kit bank or whole-project SysEx file,
  selects one kit slot, unpacks its saved Elektron 7-bit payload, and prints a
  passive kit plus Track 1-4 inventory. Saved parameter offsets are reported as
  saved_parameter_offsets_unmapped until a later mapper proves the layout. It
  does not request dumps, receive live SysEx, send MIDI, write SysEx, or touch
  hardware.

Safety:
  passive/read-only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-snapshot-mutation-plan-report": """RytmRandomizer passive CLI: analog-four-snapshot-mutation-plan-report

Usage:
  python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report --help

Behavior:
  Reads an existing Analog Four kit bank or whole-project SysEx file, decodes
  one saved kit slot, and plans captured-value-relative changes around
  candidate_unverified saved offsets. It does not claim parameter names, CC
  mappings, send MIDI, write SysEx, or touch hardware.

Safety:
  passive/read-only
  candidate offsets only
  no parameter names claimed
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-snapshot-mock-runtime-report": """RytmRandomizer passive CLI: analog-four-snapshot-mock-runtime-report

Usage:
  python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
  python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report --help

Behavior:
  Reads an existing Analog Four kit bank or whole-project SysEx file, builds a
  captured-value-relative saved-offset candidate plan, and captures that plan
  into inert mock events. Events are saved-offset candidate records only:
  candidate_unverified, no parameter names claimed, and no CC mapping claimed.
  It does not request dumps, receive live SysEx, send MIDI, write SysEx, or
  touch hardware.

Safety:
  passive/read-only
  mock sender only
  saved-offset candidate events only
  no parameter names claimed
  no CC mapping claimed
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-offset-candidate-report": """RytmRandomizer passive CLI: analog-four-offset-candidate-report

Usage:
  python -m rytm_randomizer.cli analog-four-offset-candidate-report <path> --track <1-4> --limit <n>
  python -m rytm_randomizer.cli analog-four-offset-candidate-report <path> --all-tracks --limit <n>
  python -m rytm_randomizer.cli analog-four-offset-candidate-report --help

Behavior:
  Reads an existing Analog Four kit bank or whole-project SysEx file, unpacks
  saved kit payloads, and scans either one Track 1-4 block or all four track
  blocks across kit variations for varying CC-like saved words. Reported
  offsets are candidate_unverified and no parameter names are claimed. It does
  not request dumps, receive live SysEx, send MIDI, write SysEx, or touch
  hardware.

Safety:
  passive/read-only
  candidate offsets only
  no parameter names claimed
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-controlled-diff-report": """RytmRandomizer passive CLI: analog-four-controlled-diff-report

Usage:
  python -m rytm_randomizer.cli analog-four-controlled-diff-report <before> <after> --slot <1-128> --track <1-4> --limit <n>
  python -m rytm_randomizer.cli analog-four-controlled-diff-report --help

Behavior:
  Reads two existing Analog Four kit bank or whole-project SysEx files, selects
  the same saved kit slot and Track 1-4 block from each file, and reports
  changed CC-like saved words. This is for controlled before/after mapping
  sessions: reported offsets are candidate_unverified and no parameter names
  are claimed. It does not request dumps, receive live SysEx, send MIDI, write
  SysEx, or touch hardware.

Safety:
  passive/read-only
  controlled comparison only
  candidate offsets only
  no parameter names claimed
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "essence-plan-report": """RytmRandomizer passive CLI: essence-plan-report

Usage:
  python -m rytm_randomizer.cli essence-plan-report --tags <csv> --discovery <0..1>
  python -m rytm_randomizer.cli essence-plan-report --description <text> --discovery <0..1>
  python -m rytm_randomizer.cli essence-plan-report --help

Behavior:
  Prints a passive 12-pad engine plan preview from essence tags or a written
  reference description and a Reference/Discovery value. It does not analyze
  audio files, send MIDI, write SysEx, or mutate hardware.

Safety:
  passive/read-only
  no audio file analysis
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no SysEx writes
  no hardware required""",
    "essence-application-readiness-report": """RytmRandomizer passive CLI: essence-application-readiness-report

Usage:
  python -m rytm_randomizer.cli essence-application-readiness-report --mode <safe-anchors|live-snapshot> --tags <csv> --discovery <0..1>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode <safe-anchors|live-snapshot> --description <text> --discovery <0..1>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode <safe-anchors|live-snapshot> --style <text> [--discovery <0..1>]
  python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description <text> --discovery <0..1> --snapshot <not-requested|capturing|captured|partial|failed>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description <text> --discovery <0..1> --fixture <key>
  python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --style <text> [--discovery <0..1>] --fixture <key>
  python -m rytm_randomizer.cli essence-application-readiness-report --help

Behavior:
  Prints a passive readiness gate for applying a 12-pad essence plan under Safe
  Anchors or Live Snapshot. It accepts essence tags, written descriptions, or a
  broad style prompt such as schranz or Birmingham techno. It explains which
  pads are ready, blocked, or future-only. With --fixture, it uses a passive
  mock snapshot inventory. It does not capture kits, analyze audio files, send
  MIDI, write SysEx, or mutate hardware.

Safety:
  passive/read-only
  no audio file analysis
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no Pads 5-12 runtime mutation
  no hardware required""",
    "style-intent-report": """RytmRandomizer passive CLI: style-intent-report

Usage:
  python -m rytm_randomizer.cli style-intent-report --style <text>
  python -m rytm_randomizer.cli style-intent-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli style-intent-report --help

Behavior:
  Prints a passive 12-pad style kit plan from broad genre/style intent such as
  broken techno, dark techno, Birmingham techno, schranz, hardcore, classic
  Detroit techno, driving techno, or peak-time techno. Analog Four appears only
  as future expansion metadata. It does not analyze audio files, send MIDI,
  write SysEx, or mutate hardware.

Safety:
  passive/read-only
  no audio file analysis
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no Analog Four runtime support
  no Pads 5-12 runtime mutation
  no hardware required""",
    "snapshot-essence-overlay-report": """RytmRandomizer passive CLI: snapshot-essence-overlay-report

Usage:
  python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-overlay-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, builds the
  captured-value snapshot mutation plan, resolves a broad style prompt, and
  compares the captured engine on each of the 12 pads against the selected
  mapped style engine. It reports same-engine pads, engine-switch-ready pads,
  blocked pads, and the machine CC15 switches a future guarded active path
  would need. It does not send MIDI, open ports, write SysEx, or touch hardware.

Safety:
  passive/read-only
  snapshot/essence comparison only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "snapshot-essence-send-plan-report": """RytmRandomizer passive CLI: snapshot-essence-send-plan-report

Usage:
  python -m rytm_randomizer.cli snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-send-plan-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, builds the
  snapshot essence overlay, and prints the passive CC send plan needed to make
  the selected 12-pad style plan audible. Same-engine pads use captured-value
  mutation events. Engine-switch pads emit machine CC15 first and then selected
  mapped profile anchor parameters. It does not send MIDI, open ports, write
  SysEx, or touch hardware.

Safety:
  passive/read-only
  mock sender only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "snapshot-essence-guarded-send-dry-run-report": """RytmRandomizer passive CLI: snapshot-essence-guarded-send-dry-run-report

Usage:
  python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
  python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli snapshot-essence-guarded-send-dry-run-report --help

Behavior:
  Reads an existing Rytm kit bank or whole-project SysEx file, builds the
  snapshot essence send plan, and executes the eligible CC events into a mock
  sender only. The guard requires arming and dry-run confirmation internally,
  refuses blocked plans without partial emission, and never opens a MIDI port
  or sends hardware MIDI.

Safety:
  passive/read-only
  mock sender only
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "twelve-pad-mock-runtime-report": """RytmRandomizer passive CLI: twelve-pad-mock-runtime-report

Usage:
  python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style <text>
  python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --help

Behavior:
  Builds a mock-only 12-pad runtime contract from broad style intent. It uses
  currently mapped V1.34 machine profiles, falls back from preferred future
  engines to mapped candidates, and prints the inert mock CC stream for
  inspection. It does not send MIDI, open ports, write SysEx, or mutate
  hardware.

Safety:
  passive/read-only
  mock sender only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
    "analog-four-reference-report": """RytmRandomizer passive CLI: analog-four-reference-report

Usage:
  python -m rytm_randomizer.cli analog-four-reference-report
  python -m rytm_randomizer.cli analog-four-reference-report --help

Behavior:
  Prints an attributed passive Analog Four MKII reference intake: source,
  license, four planning track roles, starter CC/NRPN parameter groups, and
  blocked next slices. It does not add Analog Four runtime support, send MIDI,
  open ports, receive SysEx, write SysEx, or mutate hardware.

Safety:
  passive/read-only
  reference intake only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
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
