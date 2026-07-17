"""Static CLI help text for the passive RytmRandomizer CLI.

This module holds the help/usage strings as data so that ``cli.py`` can stay
focused on argument parsing and dispatch. The values here are byte-for-byte
identical to the previously inline ``*_HELP`` constants; the CLI output must
not change by a single character.
"""

from typing import Final

USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "project-status-report [--summary|--json|--check] | mock-mapper-report | runtime-plan-report | "
    "active-boundary-report | mock-runtime-active-bridge-report | "
    "anchor-profile-report | behavior-parity-report | rytm-12-pad-machine-matrix-report | "
    "manual-feedback-packet-report "
    "[--scenario full|installer|profile|mock|hardware|review] [--json] | "
    "rytm-snapshot-pad-compatibility-report | "
    "analog-rytm-midi-catalog-report | "
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
    "analog-four-baseline-report --kit <syx-path> --pattern-kit <syx-path> "
    "--whole-project <syx-path> [--json] | "
    "analog-four-patch-genome-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json] | "
    "analog-four-patch-learning-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json] | "
    "analog-four-patch-corpus-report "
    "(--description <text>|--audio <path>) [--track N] [--limit N] "
    "[--corpus-file <path>] [--json] | "
    "analog-four-patch-send-plan-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json] | "
    "local-model-copilot-report --question <text> [--description <text>] "
    "[--workflow docs|mutation|patch|all] [--model <name>] [--ask-local-model] "
    "[--json] | "
    "analog-four-oxi-macro-report [<macro-name>] [--seed N] [--intensity N] "
    "[--events] [--limit N] [--json] | "
    "analog-four-oxi-macro-readiness-report [<macro-name>] [--seed N] "
    "[--intensity N] [--limit N] [--json] | "
    "analog-four-oxi-macro-set-planner-report [--set-name <text>] "
    "[--sequence <macro,...>] [--seed N] [--json] | "
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
    "style-profile-report | style-crates-queue-journal-report [--json] | "
    "style-crate-rehearsal-deck-report [--crate <key>] [--json] | "
    "oxi-live-macro-catalog-report | "
    "controller-brain-mapping-report [--json] | "
    "controller-brain-rehearsal-report [--json] | "
    "controller-brain-operator-package-report [--json] | "
    "controller-brain-live-runbook-report [--json] | "
    "controller-brain-live-state-report [--json] | "
    "controller-brain-live-bridge-readiness-report [--json] | "
    "controller-brain-live-dispatch-rehearsal-report [--json] | "
    "controller-brain-live-feedback-rehearsal-report [--json] | "
    "controller-brain-live-cockpit-handoff-report [--json] | "
    "controller-brain-live-implementation-bridge-report [--json] | "
    "controller-brain-live-desktop-blueprint-report [--json] | "
    "controller-brain-live-desktop-app-plan-report "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] [--json] | "
    "controller-brain-live-desktop-component-contract-report "
    "[--component-contract-label <text>] [--selector-prefix <text>] [--json] | "
    "controller-brain-live-desktop-view-model-report "
    "[--view-model-label <text>] [--state-prefix <text>] [--json] | "
    "controller-brain-live-desktop-render-contract-report "
    "[--render-contract-label <text>] [--surface-prefix <text>] [--json] | "
    "rytm-live-macro-hardware-rehearsal-report [--json] | "
    "live-gui-performance-flow-model-report [--json] | "
    "live-gui-performance-console-report [--json] | "
    "oxi-live-set-strategy-report [--json] | "
    "reference-style-blueprint-report "
    "(--description <text>|--audio <path>|--library <dir>) [--json] | "
    "list-style-profiles | inspect-style-profile <key> | "
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
    "style-performance-arc-live-cue-sheet-report [<arc-key> ...] [--rytm <syx-path>] "
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
    "style-performance-arc-live-runbook-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-stage-routing-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-stage-rehearsal-state-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-set-cockpit-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-show-export-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-transition-timeline-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-command-deck-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-state-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-readiness-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--json] | "
    "style-performance-arc-live-control-surface-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--json] | "
    "style-performance-arc-live-analyzer-handoff-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-analyzer-targets-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-gui-analyzer-readiness-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-gui-rehearsal-session-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--label <text>] [--json] | "
    "style-performance-arc-live-gui-capture-queue-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--label <text>] [--capture-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-capture-review-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-sidecar-session-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] [--json] | "
    "style-performance-arc-live-gui-screen-contract-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] [--json] | "
    "style-performance-arc-live-gui-render-tree-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--json] | "
    "style-performance-arc-live-gui-analyzer-overlay-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] [--json] | "
    "style-performance-arc-live-gui-analyzer-frame-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--json] | "
    "style-performance-arc-live-gui-interaction-script-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] [--json] | "
    "style-performance-arc-live-gui-action-reducer-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--json] | "
    "style-performance-arc-live-gui-controller-state-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] [--json] | "
    "style-performance-arc-live-gui-playback-transcript-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--json] | "
    "style-performance-arc-live-gui-playback-validation-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] [--json] | "
    "style-performance-arc-live-gui-test-harness-contract-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--json] | "
    "style-performance-arc-live-gui-test-harness-readiness-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] [--json] | "
    "style-performance-arc-live-gui-implementation-bridge-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--json] | "
    "style-performance-arc-live-gui-desktop-blueprint-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--json] | "
    "style-performance-arc-live-gui-desktop-app-plan-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] [--json] | "
    "style-performance-arc-live-gui-desktop-component-contract-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-desktop-view-model-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] "
    "[--view-model-label <text>] [--state-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-desktop-render-contract-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] "
    "[--view-model-label <text>] [--state-prefix <text>] "
    "[--render-contract-label <text>] [--json] | "
    "style-performance-arc-live-gui-desktop-render-harness-report "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] [--label <text>] "
    "[--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] "
    "[--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] "
    "[--view-model-label <text>] [--state-prefix <text>] "
    "[--render-contract-label <text>] "
    "[--render-harness-label <text>] [--runner-label <text>] [--json] | "
    "cockpit-send-plan-readiness-report (--plan-json <json>|--plan-file <path>) "
    "[--label <text>] [--json] | "
    "cockpit-send-plan-rehearsal-surface-report "
    "(--plan-json <json>|--plan-file <path>|--readiness-json <json>|--readiness-file <path>) "
    "[--label <text>] [--json] | "
    "cockpit-export-profile-model --profile-id <id> --profiles-dir <path> "
    "--output <file.rymp> [--key-hex <hex> --key-id <label>] "
    "[--unsigned] [--overwrite] [--json] | "
    "analog-four-saved-kit-export --source <kit.syx> --output <kit.syx> "
    "--filter2-resonance <track:value> [--filter2-resonance <track:value> ...] "
    "[--overwrite] [--json] | "
    "analog-four-audio-patch-batch --audio <path> --source-kit <kit.syx> "
    "--output-dir <dir> [--track N] [--candidates N] [--overwrite] [--json] | "
    "analog-four-audio-patch-rank --reference <path> --manifest <batch.json> "
    "--render <N=path> [--render <N=path> ...] [--json] | "
    "cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> "
    "[--key-id <label>] [--unsigned] [--output <path>] [--label <text>] [--json] | "
    "manual-feedback-packet-report "
    "[--scenario full|installer|profile|mock|hardware|review] [--json] | "
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


def _analog_rytm_midi_catalog_report_help():
    from .reports.analog_rytm_midi_catalog import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-rytm-midi-catalog-report

Usage:
  python -m rytm_randomizer.cli analog-rytm-midi-catalog-report
  python -m rytm_randomizer.cli analog-rytm-midi-catalog-report --help

Behavior:
  Prints the passive Analog Rytm MKII OS 1.72 MIDI CC/NRPN catalog report.

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


def _analog_four_baseline_report_help():
    from .reports.analog_four_baseline import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-baseline-report

Usage:
  python -m rytm_randomizer.cli analog-four-baseline-report --kit <syx-path> --pattern-kit <syx-path> --whole-project <syx-path>
  python -m rytm_randomizer.cli analog-four-baseline-report --kit <syx-path> --pattern-kit <syx-path> --whole-project <syx-path> --json
  python -m rytm_randomizer.cli analog-four-baseline-report --help

Behavior:
  Compares a clean Analog Four MK2 initialized kit export, A01 pattern+kit
  export, and whole-project export. The report fingerprints the first decoded
  A4 kit in each source, verifies whether the three baseline fingerprints
  agree, and marks the baseline ready for a later changed-patch diff. It does
  not claim parameter offsets; A4 offsets remain candidate-only until a changed
  patch is captured and promoted.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_patch_genome_report_help():
    from .reports.analog_four_patch_genome import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-patch-genome-report

Usage:
  python -m rytm_randomizer.cli analog-four-patch-genome-report --description <text>
  python -m rytm_randomizer.cli analog-four-patch-genome-report --audio <path>
  python -m rytm_randomizer.cli analog-four-patch-genome-report --description <text> --track N
  python -m rytm_randomizer.cli analog-four-patch-genome-report --description <text> --candidate N
  python -m rytm_randomizer.cli analog-four-patch-genome-report --description <text> --json
  python -m rytm_randomizer.cli analog-four-patch-genome-report --help

Behavior:
  Generates four passive Analog Four MK2 patch candidates from a description
  or audio feature report, then prints the selected candidate DNA with A4
  front-panel targets plus CC/NRPN metadata. CC-ready scalar rows include
  concrete 0..127 values; NRPN-only destination rows remain screen-only until
  exact destination ordinals are captured for live dial-in.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_patch_learning_report_help():
    from .reports.analog_four_patch_learning import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-patch-learning-report

Usage:
  python -m rytm_randomizer.cli analog-four-patch-learning-report --description <text>
  python -m rytm_randomizer.cli analog-four-patch-learning-report --audio <path>
  python -m rytm_randomizer.cli analog-four-patch-learning-report --description <text> --track N
  python -m rytm_randomizer.cli analog-four-patch-learning-report --description <text> --candidate N
  python -m rytm_randomizer.cli analog-four-patch-learning-report --description <text> --json
  python -m rytm_randomizer.cli analog-four-patch-learning-report --help

Behavior:
  Builds on the passive Analog Four patch genome by ranking the four
  candidates, mapping measured reference traits to A4 controls, printing a
  future capture matrix for empirical learning, and separating live-dial-ready
  CC/NRPN rows from front-panel-only NRPN rows that still need ordinal capture.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_patch_corpus_report_help():
    from .reports.analog_four_patch_corpus import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-patch-corpus-report

Usage:
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --description <text>
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --audio <path>
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --description <text> --track N
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --description <text> --limit N
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --description <text> --corpus-file <path>
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --description <text> --json
  python -m rytm_randomizer.cli analog-four-patch-corpus-report --help

Behavior:
  Ranks a reference description or audio feature report against passive
  Analog Four MK2 patch-corpus examples. Without --corpus-file it uses
  clearly labeled synthetic starter rows derived from the current four patch
  candidates; with --corpus-file it can rank operator-recorded A4
  audio/patch examples without opening MIDI or touching hardware.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_patch_send_plan_report_help():
    from .reports.analog_four_patch_send_plan import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-patch-send-plan-report

Usage:
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --description <text>
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --audio <path>
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --description <text> --track N
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --description <text> --candidate N
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --description <text> --json
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report --help

Behavior:
  Builds on the passive Analog Four patch learning packet by compiling the
  selected candidate into ordered CC/NRPN live-dial events plus skipped
  front-panel rows. This is the preview surface for the active app command
  `python -m rytm_randomizer.app --dry-run --a4-patch-send-plan ...` or
  `--arm --confirm-a4-patch-send-plan`; the CLI report itself opens no MIDI
  port and sends no MIDI.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _local_model_copilot_report_help():
    from .reports.local_model_copilot import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: local-model-copilot-report

Usage:
  python -m rytm_randomizer.cli local-model-copilot-report --question <text>
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> --workflow docs
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> --workflow mutation --description <text>
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> --workflow patch --description <text>
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> --workflow all --ask-local-model --model <name>
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> --json
  python -m rytm_randomizer.cli local-model-copilot-report --help

Behavior:
  Builds passive local-AI packets for docs/MIDI questions, staged mutation
  intent, and Analog Four patch-review suggestions. Without --ask-local-model
  it prints the exact source packets and schemas only; with --ask-local-model
  it runs the configured LOCAL_MODEL_COMMAND executable and validates
  structured JSON stdout before returning staged review metadata.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_oxi_macro_report_help():
    from .reports.analog_four_oxi_macro_report import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-oxi-macro-report

Usage:
  python -m rytm_randomizer.cli analog-four-oxi-macro-report
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name>
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name> --seed N
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name> --intensity N
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name> --events
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name> --events --limit N
  python -m rytm_randomizer.cli analog-four-oxi-macro-report <macro-name> --json
  python -m rytm_randomizer.cli analog-four-oxi-macro-report --help

Behavior:
  Prints a passive in-memory Analog Four OXI-style macro preview. The report
  uses the existing manual-backed Analog Four CC metadata, stages deterministic
  four-track preview rows by seed and intensity, and can include mock row
  details with --events. It does not read a SysEx file, invoke a mapper, open a
  MIDI port, render real MIDI, or mutate hardware. Use --limit N to cap event
  rows; N=0 displays all rows. Use --json for GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_oxi_macro_readiness_report_help():
    from .reports.analog_four_oxi_macro_readiness import (
        PREFLIGHT_COMMAND,
        SAFETY_LINES,
    )

    return f"""RytmRandomizer passive CLI: analog-four-oxi-macro-readiness-report

Usage:
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report <macro-name>
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report <macro-name> --seed N
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report <macro-name> --intensity N
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report <macro-name> --limit N
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report <macro-name> --json
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report --help

Behavior:
  Prints a passive Analog Four OXI macro hardware-readiness report. It reuses
  the deterministic macro rows from analog-four-oxi-macro-report, annotates
  each row with the manual-backed CC readiness status, and emits explicit
  operator-present validation commands for later studio checks. Run the
  input-only soft-capture preflight first:
  {PREFLIGHT_COMMAND}

  The report also prints stop/recovery notes and promotion gates. It does not
  open MIDI ports, send MIDI, execute validation commands, or arm the A4 full
  macro send path.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_oxi_macro_set_planner_report_help():
    from .reports.analog_four_oxi_macro_set_planner import (
        BLOCKED_ACTIVE_ACTIONS,
        DEFAULT_SEQUENCE,
        SAFETY_LINES,
    )

    default_sequence = ", ".join(DEFAULT_SEQUENCE)
    blocked_actions = "\n".join(f"  - {action}" for action in BLOCKED_ACTIVE_ACTIONS)
    return f"""RytmRandomizer passive CLI: analog-four-oxi-macro-set-planner-report

Usage:
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --set-name <text>
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --sequence <macro,...>
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --seed N
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --help

Behavior:
  Prints a passive Analog Four OXI macro set planner. The default set sequence
  is {default_sequence}. Each set step reuses analog-four-oxi-macro-report and
  analog-four-oxi-macro-readiness-report metadata, then emits current/up-next
  queue fields, readiness counts, validation commands, and recovery notes for
  future Cockpit set planning. It does not open MIDI ports, send MIDI, execute
  validation commands, automate playback, or arm the A4 full macro send path.

Blocked active actions:
{blocked_actions}

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


def _style_crates_queue_journal_report_help():
    from .reports.style_crates_queue_journal import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-crates-queue-journal-report

Usage:
  python -m rytm_randomizer.cli style-crates-queue-journal-report
  python -m rytm_randomizer.cli style-crates-queue-journal-report --json
  python -m rytm_randomizer.cli style-crates-queue-journal-report --help

Behavior:
  Lists passive Style Crates, staged queue moves, and Mutation Journal entries.
  This is metadata-only planning for future GUI and hardware-gated workflows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_crate_rehearsal_deck_report_help():
    from .reports.style_crate_rehearsal_deck import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-crate-rehearsal-deck-report

Usage:
  python -m rytm_randomizer.cli style-crate-rehearsal-deck-report
  python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --crate <key>
  python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --json
  python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --help

Behavior:
  Builds passive GUI-ready crate, queue, and journal rehearsal cards.
  This turns Style Crates metadata into operator review cards without firing
  queued moves, replaying journal entries, launching a GUI, or sending MIDI.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _oxi_live_macro_catalog_report_help():
    return """RytmRandomizer passive CLI: oxi-live-macro-catalog-report

Usage:
  python -m rytm_randomizer.cli oxi-live-macro-catalog-report
  python -m rytm_randomizer.cli oxi-live-macro-catalog-report --help

Behavior:
  Prints the passive OXI live macro catalog, including Rytm macro cards,
  candidate-only Analog Four runway state, recovery actions, and blocked active
  actions.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""


def _controller_brain_mapping_report_help():
    return """RytmRandomizer passive CLI: controller-brain-mapping-report

Usage:
  python -m rytm_randomizer.cli controller-brain-mapping-report
  python -m rytm_randomizer.cli controller-brain-mapping-report --json
  python -m rytm_randomizer.cli controller-brain-mapping-report --help

Behavior:
  Prints the passive 16-encoder controller-brain intent catalog for future
  hardware surfaces. It maps paged controls to reviewed RytmRandomizer intent
  such as Rytm pad lanes, Analog Four runway macros, Style Crates, live queue
  staging, snapshot recovery, and Mutation Journal actions.

Safety:
  passive/read-only
  no MIDI controller input
  no MIDI sending
  no port opening
  no WebSocket command dispatch
  no hardware mutation
  no hardware required"""


def _controller_brain_rehearsal_report_help():
    return """RytmRandomizer passive CLI: controller-brain-rehearsal-report

Usage:
  python -m rytm_randomizer.cli controller-brain-rehearsal-report
  python -m rytm_randomizer.cli controller-brain-rehearsal-report --json
  python -m rytm_randomizer.cli controller-brain-rehearsal-report --help

Behavior:
  Prints a passive controller-brain rehearsal and export packet. It derives
  controller-template rows from the 16-encoder mapping profile, then resolves
  virtual gestures into reviewed RytmRandomizer intent for Rytm pads, Analog
  Four runway controls, Style Crates, queue staging, and snapshot recovery.

Safety:
  passive/read-only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no WebSocket command dispatch
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required"""


def _controller_brain_operator_package_report_help():
    return """RytmRandomizer passive CLI: controller-brain-operator-package-report

Usage:
  python -m rytm_randomizer.cli controller-brain-operator-package-report
  python -m rytm_randomizer.cli controller-brain-operator-package-report --json
  python -m rytm_randomizer.cli controller-brain-operator-package-report --help

Behavior:
  Prints a passive controller-brain to operator package ledger. It composes
  virtual controller gestures with the Live Kit Operator Package slots so a
  future hardware surface can preview macro depth, crate, queue, pad-lane,
  A4 review, and recovery intent before any active controller or hardware path
  exists.

Safety:
  passive/read-only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no WebSocket command dispatch
  no file writing
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required"""


def _controller_brain_live_runbook_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-runbook-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-runbook-report
  python -m rytm_randomizer.cli controller-brain-live-runbook-report --json
  python -m rytm_randomizer.cli controller-brain-live-runbook-report --help

Behavior:
  Prints a passive controller-brain live runbook. It composes the controller
  rehearsal packet, OXI live set strategy, and Cockpit performance console
  metadata into stage, inspect, fire, and recover steps for future controller
  surfaces.

Safety:
  passive/read-only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no WebSocket command dispatch
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required"""


def _controller_brain_live_state_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-state-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-state-report
  python -m rytm_randomizer.cli controller-brain-live-state-report --json
  python -m rytm_randomizer.cli controller-brain-live-state-report --help

Behavior:
  Prints a passive controller-brain live state contract. It derives state rows,
  queued intents, and audit events from the controller-brain live runbook so a
  future fixed-controller bridge can render and test the next interaction layer
  without opening controller input or dispatching runtime commands.

Safety:
  passive/read-only
  controller-brain live state metadata only
  queued intents are metadata only
  audit events are metadata only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no WebSocket command dispatch
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_bridge_readiness_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-bridge-readiness-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report
  python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --json
  python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --help

Behavior:
  Prints passive controller-brain live bridge readiness. It derives contract
  packets and readiness gates from the controller-brain live state contract so a
  future controller input adapter, reducer, WebSocket dispatcher, feedback
  layer, and hardware-send path have an explicit blocked handoff.

Safety:
  passive/read-only
  controller-brain bridge readiness metadata only
  contract packets are metadata only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no runtime reducer execution
  no WebSocket command dispatch
  no controller feedback emission
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_dispatch_rehearsal_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-dispatch-rehearsal-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report
  python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --json
  python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --help

Behavior:
  Prints passive controller-brain live dispatch rehearsal. It derives shadow
  dispatch decisions from the controller-brain bridge-readiness contract so a
  future controller input adapter, reducer, WebSocket dispatcher, feedback
  layer, and hardware-send path have an explicit blocked rehearsal packet.

Safety:
  passive/read-only
  controller-brain dispatch rehearsal metadata only
  shadow dispatch decisions are metadata only
  no MIDI controller input
  no MIDI learn or raw CC capture
  no runtime reducer execution
  no WebSocket command dispatch
  no controller feedback emission
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_feedback_rehearsal_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-feedback-rehearsal-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report
  python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --json
  python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --help

Behavior:
  Prints passive controller-brain live feedback rehearsal. It derives feedback
  frames from the controller-brain dispatch rehearsal contract so a future
  controller output adapter can map LED state, encoder rings, display text, and
  WebSocket feedback without emitting anything yet.

Safety:
  passive/read-only
  controller-brain feedback rehearsal metadata only
  feedback frames are metadata only
  no MIDI controller output
  no controller feedback emission
  no WebSocket feedback dispatch
  no runtime reducer execution
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_cockpit_handoff_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-cockpit-handoff-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report
  python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --json
  python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --help

Behavior:
  Prints passive controller-brain live Cockpit handoff metadata. It derives
  GUI-ready handoff cards, Cockpit panels, disabled Cockpit controls, replay
  commands, and safety evidence from the controller-brain feedback rehearsal.

Safety:
  passive/read-only
  controller-brain Cockpit handoff metadata only
  GUI-ready handoff cards are metadata only
  disabled Cockpit controls are metadata only
  no controller input
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI controller output
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_implementation_bridge_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-implementation-bridge-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report
  python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --json
  python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report --help

Behavior:
  Prints passive controller-brain live implementation bridge metadata. It turns
  disabled Cockpit handoff cards into future GUI implementation bindings,
  fixture bundles, implementation gates, replay commands, and safety evidence
  without mounting a renderer or executing runtime behavior.

Safety:
  passive/read-only
  controller-brain implementation bridge metadata only
  implementation bindings are declarative metadata only
  fixture bundles are metadata only
  implementation gates are metadata only
  no GUI launch
  no GUI renderer start
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI controller output
  no MIDI sending
  no port opening
  no snapshot mutation
  no hardware mutation
  no hardware required"""


def _controller_brain_live_desktop_blueprint_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-desktop-blueprint-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report
  python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report --json
  python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report --help

Behavior:
  Prints passive controller-brain live desktop blueprint metadata. It turns the
  implementation bridge into disabled desktop regions, component contracts,
  view-model bindings, fixture hints, acceptance checks, replay commands, and
  safety evidence for future Cockpit desktop work without mounting the GUI.

Safety:
  passive/read-only
  controller-brain desktop blueprint metadata only
  desktop regions are declarative metadata only
  component contracts are declarative metadata only
  view-model bindings are declarative metadata only
  fixture hints are metadata only
  acceptance checks are metadata only
  no GUI launch
  no GUI renderer start
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI controller output
  no MIDI sending
  no port opening
  no snapshot mutation
  no file writing
  no hardware mutation
  no hardware required"""


def _controller_brain_live_desktop_app_plan_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-desktop-app-plan-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report
  python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --json
  python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --app-plan-label "Controller brain desktop app plan" --framework-target desktop-python
  python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report --help

Behavior:
  Prints passive controller-brain live desktop app plan metadata. It turns the
  desktop blueprint into disabled app routes, component file hints, state
  slices, style tokens, acceptance checks, replay commands, and safety evidence
  for future Cockpit desktop work without launching an app or writing files.

Safety:
  passive/read-only
  controller-brain desktop app plan metadata only
  app routes are declarative metadata only
  component file hints are advisory metadata only
  state slices are declarative metadata only
  style tokens are declarative metadata only
  acceptance checks are metadata only
  no GUI launch
  no app launch
  no GUI renderer start
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI sending
  no port opening
  no snapshot mutation
  no file writing
  no hardware mutation
  no hardware required"""


def _controller_brain_live_desktop_component_contract_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-desktop-component-contract-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report
  python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --json
  python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --component-contract-label "Controller brain desktop component contract" --selector-prefix rr-controller
  python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report --help

Behavior:
  Prints disabled future component API contracts for the controller-brain
  desktop surface. It turns desktop app-plan component file hints and state
  slices into component selectors, prop contracts, event contracts, test hooks,
  fixture contracts, acceptance checks, replay commands, and safety evidence
  for future Cockpit desktop work without launching an app or writing files.

Safety:
  passive/read-only
  controller-brain desktop component contract metadata only
  component contracts are declarative metadata only
  prop contracts are declarative metadata only
  event contracts are disabled metadata only
  test hooks are declarative metadata only
  fixture contracts are advisory metadata only
  no GUI launch
  no app launch
  no GUI renderer start
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI sending
  no port opening
  no snapshot mutation
  no file writing
  no hardware mutation
  no hardware required"""


def _controller_brain_live_desktop_view_model_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-desktop-view-model-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report
  python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report --json
  python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report --view-model-label "Controller brain desktop view model" --state-prefix rr-state
  python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report --help

Behavior:
  Prints disabled future component view models for the controller-brain desktop
  surface. It turns desktop component contracts into component view models,
  state bindings, disabled action models, render assertions, acceptance checks,
  replay commands, and safety evidence for future Cockpit desktop work without
  launching an app, rendering a GUI, or writing files.

Safety:
  passive/read-only
  controller-brain desktop view model metadata only
  component view models are declarative metadata only
  state bindings are declarative metadata only
  disabled action models are metadata only
  render assertions are metadata only
  no GUI launch
  no app launch
  no GUI renderer start
  no runtime reducer execution
  no WebSocket dispatch
  no controller feedback emission
  no MIDI controller output
  no MIDI sending
  no port opening
  no snapshot mutation
  no file writing
  no hardware mutation
  no hardware required"""


def _controller_brain_live_desktop_render_contract_report_help():
    return """RytmRandomizer passive CLI: controller-brain-live-desktop-render-contract-report

Usage:
  python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report
  python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report --json
  python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report --render-contract-label "Controller brain desktop render contract" --surface-prefix rr-render
  python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report --help

Behavior:
  Prints future render surfaces for the controller-brain desktop UI. It composes
  the passive desktop view-model report into disabled render bindings,
  render guards, render assertions, acceptance checks, replay commands, and safety
  evidence for future Cockpit desktop work.

Safety:
  This report performs no GUI launch, no renderer execution,
  no WebSocket dispatch, no MIDI sending, and no file writing. It only prints
  deterministic metadata to stdout/JSON."""


def _rytm_live_macro_hardware_rehearsal_report_help():
    return """RytmRandomizer passive CLI: rytm-live-macro-hardware-rehearsal-report

Usage:
  python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report
  python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --json
  python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --help

Behavior:
  Prints a passive operator rehearsal packet for the next Rytm macro hardware
  session. It gives the armed shell launch command, macro-by-macro checks,
  Pad 5/9/10/11 and Pad 6-8 lane notes, and recovery checkpoints.

Safety:
  passive/read-only report
  does not open MIDI ports
  does not send MIDI
  operator must run the armed shell manually"""


def _live_gui_performance_flow_model_report_help():
    return """RytmRandomizer passive CLI: live-gui-performance-flow-model-report

Usage:
  python -m rytm_randomizer.cli live-gui-performance-flow-model-report
  python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json
  python -m rytm_randomizer.cli live-gui-performance-flow-model-report --help

Behavior:
  Emits the passive cockpit Performance Flow model that maps Rytm OXI macro
  commands to Analog Four review-only actions.

Safety:
  passive/read-only
  GUI performance flow metadata only
  no GUI launch
  no file writing
  no real MIDI rendering
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required"""


def _live_gui_performance_console_report_help():
    return """RytmRandomizer passive CLI: live-gui-performance-console-report

Usage:
  python -m rytm_randomizer.cli live-gui-performance-console-report
  python -m rytm_randomizer.cli live-gui-performance-console-report --json
  python -m rytm_randomizer.cli live-gui-performance-console-report --help

Behavior:
  Emits the passive Cockpit performance console packet that composes the
  device rail, Rytm 12-pad surface, style queue/journal, snapshot history,
  command queue, safety checklist, and A4 set plan into one GUI-ready model.

Safety:
  passive/read-only
  Cockpit performance console packet only
  no GUI launch
  no file writing
  no command execution
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required"""


def _oxi_live_set_strategy_report_help():
    from .reports.oxi_live_set_strategy import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: oxi-live-set-strategy-report

Usage:
  python -m rytm_randomizer.cli oxi-live-set-strategy-report
  python -m rytm_randomizer.cli oxi-live-set-strategy-report --json
  python -m rytm_randomizer.cli oxi-live-set-strategy-report --help

Behavior:
  Prints passive OXI-style live set chapters, rig-role responsibilities,
  all-12-pad strategy notes, Jose's current pad-lane discipline, A4
  review-only companion actions, and next hardware validation prompts.
  Use --json for GUI/analyzer consumers.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _reference_style_blueprint_report_help():
    return """RytmRandomizer passive CLI: reference-style-blueprint-report

Usage:
  python -m rytm_randomizer.cli reference-style-blueprint-report (--description <text>|--audio <path>|--library <dir>) [--json]
  python -m rytm_randomizer.cli reference-style-blueprint-report --help

Behavior:
  Translates a style reference into a deterministic passive Analog Rytm plus Analog Four blueprint.
  Description sources are conservative LOW-confidence. Audio and library sources use the style optional extra.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required"""


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
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report --analog-four <syx-path> --scope analog-four-only
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


def _style_performance_arc_live_runbook_report_help():
    from .reports.live_performance_runbook import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-runbook-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live performance runbook from an arc or reference.
  Direct arc mode consumes the selected live cue sheet. Reference mode ranks
  description, audio, or library evidence first, then embeds the selected cue
  sheet and stage packet. The output is a show-facing checklist with a launch
  brief, replayable passive commands, stage packet, timeline cards, optional
  capped cue event previews, recovery cues, and JSON for future GUI routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_stage_routing_report_help():
    from .reports.live_stage_snapshot_routing import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-stage-routing-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds passive stage snapshot routing from an arc or reference.
  The report consumes the selected live runbook and turns each cue into
  route cards with saved Rytm/A4 kit slot, kit name, payload fingerprint,
  planned pads/tracks, mock row counts, A4 deferred/candidate rows, blockers,
  recovery moves, and a one-screen live set card for show-day use.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_stage_rehearsal_state_report_help():
    from .reports.live_stage_rehearsal_state import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-stage-rehearsal-state-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds passive stage rehearsal state from an arc or reference.
  The report consumes stage snapshot routing and turns each route card into
  show-facing go/rehearse/do-not-arm cue states, Rytm/A4 machine states,
  rehearsal steps, operator prompts, passive replay commands, optional capped
  cue event previews, and JSON for future GUI/audio-analyzer routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_set_cockpit_report_help():
    from .reports.live_set_cockpit import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-set-cockpit-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live set cockpit from an arc or reference.
  The report consumes stage rehearsal state and turns it into one
  operator-facing show dashboard with launch controls, machine panels,
  Cue cockpit cards, recovery controls, passive replay commands, optional
  capped cue event previews, and JSON for future GUI/live-set routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_show_export_report_help():
    from .reports.live_show_export import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-show-export-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live show export packet from an arc or reference.
  The report consumes the live set cockpit and turns it into a deterministic
  show handoff with an export id, machine handoff manifest, cue launch script,
  recovery script, passive replay commands, optional capped cue event previews,
  and JSON for future GUI/live-performance routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_transition_timeline_report_help():
    from .reports.live_transition_timeline import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-transition-timeline-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --description <text> --rytm <syx-path> --analog-four <syx-path> --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live transition timeline from an arc or reference.
  The report consumes the live show export packet and turns it into
  operator-facing transition cards with prep windows, launch/hold/recovery
  prompts, machine handoff summaries, passive replay commands, optional
  capped cue event previews, and JSON for future GUI/live-performance routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_command_deck_report_help():
    from .reports.live_command_deck import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-command-deck-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live command deck from an arc or reference.
  The report consumes the live transition timeline and turns it into a
  current-cue operator packet with command cards, cue prep/launch/hold/recovery
  actions, machine handoff summaries, passive replay commands, optional capped
  cue event previews, and JSON for future GUI/live-performance routing.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_state_report_help():
    from .reports.live_performance_state import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-state-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --events --limit N
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-state-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive live performance state packet from an arc or reference.
  The report consumes the live command deck and turns it into a GUI-ready
  current-state payload with now/next cues, machine panels, action bar,
  warning stack, recovery stack, replayable passive commands, optional capped
  cue event previews, and JSON for future live-performance/audio-analyzer UI.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_readiness_report_help():
    from .reports.live_performance_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-readiness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds passive GUI/audio-analyzer readiness from a live state packet.
  The report consumes the live state packet and turns it into readiness gates,
  current-cue launch mode, machine panel rows, audio-analyzer handoff text,
  operator next actions, and replayable passive commands for future GUI and
  analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_control_surface_report_help():
    from .reports.live_control_surface import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-control-surface-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --arc <arc-key> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report --help

Arguments:
  --arc <arc-key>|--description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive GUI/audio-analyzer control surface from live readiness.
  The report consumes the live readiness packet and turns it into header tiles,
  transport controls, now/next cue cards, machine cards, analyzer cards,
  decision strip rows, recovery controls, and replayable passive commands for
  future desktop GUI and audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_analyzer_handoff_report_help():
    from .reports.live_analyzer_handoff import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-analyzer-handoff-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive audio analyzer handoff from reference evidence and the live
  control surface. The report exposes FeatureReport meters, top influence
  matches, control-surface sync cards, next-cue sync cards, capture prompts,
  and replayable passive commands for future GUI/audio-analyzer workflows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_analyzer_targets_report_help():
    from .reports.live_analyzer_targets import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-analyzer-targets-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>

Behavior:
  Builds passive rehearsal targets from the live analyzer handoff. The report
  exposes target bands, cue checkpoints, calibration steps, warning thresholds,
  and replayable passive commands for future live analyzer comparison.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_analyzer_readiness_report_help():
    from .reports.live_gui_analyzer_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-analyzer-readiness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description <text> --rytm <syx-path> --analog-four <syx-path> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive GUI/audio-analyzer readiness bundle from live analyzer
  targets. The report exposes GUI panel manifests, analyzer stream wiring,
  operator workflow steps, blocked active actions, and replayable passive
  commands for future desktop GUI and audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_rehearsal_session_report_help():
    from .reports.live_gui_rehearsal_session import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-rehearsal-session-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --description <text> --rytm <syx-path> --analog-four <syx-path> --label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive GUI rehearsal session packet from the GUI/audio-analyzer
  readiness bundle. The report exposes session task cards, listen-only
  rehearsal take cards, operator checklists, blocked active actions, and
  replayable passive commands for future desktop GUI and audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_capture_queue_report_help():
    from .reports.live_gui_capture_queue import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-capture-queue-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --description <text> --rytm <syx-path> --analog-four <syx-path> --label <text> --capture-prefix <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>

Behavior:
  Builds a passive GUI/audio analyzer capture queue from the GUI rehearsal
  session packet. The report exposes deterministic capture slots, analyzer job
  cards, suggested capture filenames, operator checklists, blocked active
  actions, and replayable passive commands for future desktop GUI and
  audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_capture_review_report_help():
    from .reports.live_gui_capture_review import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-capture-review-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --slot capture-001 --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI/audio analyzer capture review from the capture queue and
  captured FeatureReport evidence. The report emits deterministic go/repeat/hold
  operator decisions, metric drift notes, hold reasons, blocked active actions,
  and replayable passive commands for future desktop GUI and audio-analyzer
  flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_sidecar_session_report_help():
    from .reports.live_gui_sidecar_session import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-sidecar-session-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --slot capture-001 --sidecar-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive single sidecar-ready GUI state from the capture review. The
  report emits panel rows, analyzer comparison rows, capture decision rows,
  disabled active controls, blocked active actions, and replayable passive
  commands for future desktop GUI and audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_screen_contract_report_help():
    from .reports.live_gui_screen_contract import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-screen-contract-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --slot capture-001 --screen-label <text> --layout <key> --viewport desktop --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI screen contract from the sidecar session. The report
  emits ordered screen regions, component state, analyzer/capture table rows,
  disabled interaction controls, blocked active actions, deterministic JSON,
  and replayable passive commands for future desktop GUI and audio-analyzer
  flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_render_tree_report_help():
    from .reports.live_gui_render_tree import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-render-tree-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --render-target desktop-sidecar --density standard --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI render tree from the screen contract. The report emits
  a deterministic root/region/component/table-row tree, source bindings,
  disabled active controls, blocked active actions, JSON-ready node metadata,
  and replayable passive commands for future desktop GUI and audio-analyzer
  flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_analyzer_overlay_report_help():
    from .reports.live_gui_analyzer_overlay import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-analyzer-overlay-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --overlay-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive analyzer overlay from the render tree. The report emits
  meter widgets, threshold markers, selected capture badges, render-node
  annotations, blocked active actions, deterministic JSON, and replayable
  passive commands for future desktop GUI and audio-analyzer flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_analyzer_frame_report_help():
    from .reports.live_gui_analyzer_frame import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-analyzer-frame-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --overlay-label <text> --frame-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive analyzer frame from the analyzer overlay. The report emits
  ordered frame events, visual assertions, blocked active actions,
  deterministic JSON, and replayable passive commands for future desktop GUI
  and GUI test-harness flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_interaction_script_report_help():
    from .reports.live_gui_interaction_script import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-interaction-script-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --frame-label <text> --interaction-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI interaction script from the analyzer frame. The report
  emits ordered interaction steps, GUI control bindings, disabled hardware
  locks, deterministic JSON, and replayable passive commands for future desktop
  GUI and GUI test-harness flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_action_reducer_report_help():
    from .reports.live_gui_action_reducer import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-action-reducer-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --interaction-label <text> --reducer-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI action reducer from the interaction script. The report
  emits deterministic control transition metadata, blocked hardware/action
  decisions, JSON, and replayable passive commands for future desktop GUI and
  GUI test-harness flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_controller_state_report_help():
    from .reports.live_gui_controller_state import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-controller-state-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --reducer-label <text> --controller-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds passive GUI controller state from the action reducer. The report emits
  deterministic control-state rows, queued allowed GUI actions, blocked-control
  decisions, JSON, and replayable passive commands for future desktop GUI and
  GUI test-harness flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_playback_transcript_report_help():
    from .reports.live_gui_playback_transcript import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-playback-transcript-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --controller-label <text> --playback-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI playback transcript from controller state. The report
  emits deterministic playback events, GUI assertions, analyzer checkpoints,
  blocked active actions, JSON, and replayable passive commands for future
  desktop GUI and GUI test-harness flows.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_playback_validation_report_help():
    from .reports.live_gui_playback_validation import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-playback-validation-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --playback-label <text> --validation-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds passive GUI playback validation from a playback transcript. The report
  emits deterministic validation harness steps, validation cases, blocked active
  actions, JSON, and replayable passive commands for future GUI and
  audio-analyzer test harnesses.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_test_harness_contract_report_help():
    from .reports.live_gui_test_harness_contract import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-test-harness-contract-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --validation-label <text> --harness-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI test-harness contract from a playback-validation matrix.
  The report emits deterministic suites, fixtures, bindings, blocked active
  actions, JSON, and replayable passive commands for future GUI and
  audio-analyzer harnesses.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_test_harness_readiness_report_help():
    from .reports.live_gui_test_harness_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-test-harness-readiness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --harness-label <text> --readiness-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds passive GUI test-harness readiness from a test-harness contract.
  The report emits deterministic readiness gates, checks, rehearsal steps,
  blocked active actions, JSON, and replayable passive commands for future GUI
  and audio-analyzer harness rehearsal.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_implementation_bridge_report_help():
    from .reports.live_gui_implementation_bridge import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-implementation-bridge-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --readiness-label <text> --bridge-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds passive GUI implementation bridge metadata from test-harness readiness.
  The report emits deterministic view-model packets, disabled component mounts,
  fixture bundles, implementation gates, blocked active actions, JSON, and
  replayable passive commands for future desktop GUI implementation work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_blueprint_report_help():
    from .reports.live_gui_desktop_blueprint import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-blueprint-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --bridge-label <text> --blueprint-label <text> --desktop-shell operator-dashboard --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive desktop GUI blueprint from implementation bridge metadata.
  The report emits deterministic desktop shell, viewport, region, widget,
  binding, implementation task, fixture hint, acceptance check, blocked action,
  JSON, and replayable passive command metadata for future GUI work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_app_plan_report_help():
    from .reports.live_gui_desktop_app_plan import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-app-plan-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --blueprint-label <text> --desktop-shell operator-dashboard --app-plan-label <text> --framework-target desktop-python --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive desktop app plan from GUI desktop blueprint metadata.
  The report emits deterministic app shell, routes, component file hints,
  state slices, style tokens, acceptance checks, blocked actions, JSON, and
  replayable passive command metadata for future GUI desktop app work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_component_contract_report_help():
    from .reports.live_gui_desktop_component_contract import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-component-contract-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --app-plan-label <text> --component-contract-label <text> --selector-prefix <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive desktop component contract from GUI desktop app plan metadata.
  The report emits deterministic component contracts, prop contracts, disabled
  action contracts, test selectors, acceptance checks, blocked actions, JSON,
  and replayable passive command metadata for future GUI desktop implementation work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_view_model_report_help():
    from .reports.live_gui_desktop_view_model import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-view-model-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --component-contract-label <text> --selector-prefix <text> --view-model-label <text> --state-prefix <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive desktop view model from GUI desktop component-contract metadata.
  The report emits deterministic component view models, state bindings,
  disabled action view models, style tokens, acceptance checks, blocked actions,
  JSON, and replayable passive command metadata for future GUI desktop work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_render_contract_report_help():
    from .reports.live_gui_desktop_render_contract import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-render-contract-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --component-contract-label <text> --selector-prefix <text> --view-model-label <text> --state-prefix <text> --render-contract-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive desktop render contract from GUI desktop view-model metadata.
  The report emits deterministic render surfaces, render bindings,
  style-token bindings, render assertions, blocked actions, JSON, and
  replayable passive command metadata for future GUI desktop renderer work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_desktop_render_harness_report_help():
    from .reports.live_gui_desktop_render_harness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-desktop-render-harness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --cue N --lookahead N --matches N --takes N
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --render-contract-label <text> --render-harness-label <text> --runner-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds a passive GUI desktop render harness from GUI desktop render-contract metadata.
  The report emits deterministic surface harnesses, binding harnesses,
  style-token checks, harness assertions, blocked actions, JSON, and replayable
  passive command metadata for future GUI desktop harness work.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _style_performance_arc_live_gui_cockpit_boundary_readiness_report_help():
    from .reports.live_gui_cockpit_boundary_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-performance-arc-live-gui-cockpit-boundary-readiness-report

Usage:
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --audio <path> --capture-audio <path> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --library <dir> --capture-library <dir> --rytm <syx-path>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --render-harness-label <text> --boundary-label <text> --json
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --description <text> --capture-description <text> --rytm <syx-path> --analog-four <syx-path> --hardware-entrypoint <command> --passive-entrypoint <command> --ws-port-env <name>
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report --help

Arguments:
  --description <text>|--audio <path>|--library <dir>
  --capture-description <text>|--capture-audio <path>|--capture-library <dir>

Behavior:
  Builds passive cockpit boundary readiness from GUI desktop render-harness metadata.
  The report keeps active hardware remains app --arm only, makes Rytm 12-pad and
  Analog Four 4-track scope explicit, captures future WebSocket/env documentation
  expectations, records optional Tauri/web toolchain guardrails, and emits blocked
  actions, JSON, and replayable passive command metadata.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _cockpit_send_plan_readiness_report_help():
    from .reports.cockpit_send_plan_operator_readiness import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: cockpit-send-plan-readiness-report

Usage:
  python -m rytm_randomizer.cli cockpit-send-plan-readiness-report --plan-json <json>
  python -m rytm_randomizer.cli cockpit-send-plan-readiness-report --plan-file <path>
  python -m rytm_randomizer.cli cockpit-send-plan-readiness-report --plan-json <json> --label <text> --json
  python -m rytm_randomizer.cli cockpit-send-plan-readiness-report --help

Arguments:
  --plan-json <json>|--plan-file <path>

Behavior:
  Builds passive send-plan operator readiness from CockpitSendPlan metadata.
  The report explains ready versus blocked SEND state, pad packet rows,
  locked pads, blocked reasons, operator next action, deterministic JSON,
  and replayable passive command metadata without preparing or applying a SEND plan.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _cockpit_send_plan_rehearsal_surface_report_help():
    from .reports.cockpit_send_plan_rehearsal_surface import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: cockpit-send-plan-rehearsal-surface-report

Usage:
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --plan-json <json>
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --plan-file <path>
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --readiness-json <json>
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --readiness-file <path>
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --plan-json <json> --label <text> --json
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report --help

Arguments:
  --plan-json <json>|--plan-file <path>|--readiness-json <json>|--readiness-file <path>

Behavior:
  Builds passive send-plan rehearsal surface state from CockpitSendPlan or readiness metadata.
  The report emits GUI-ready panels, state bindings, disabled action controls,
  acceptance checks, blocked active actions, deterministic JSON, and replayable
  passive command metadata without preparing or applying SEND, launching a GUI,
  opening a sidecar, or touching hardware.

Safety:
{_safety_block(SAFETY_LINES)}"""


_COCKPIT_EXPORT_PROFILE_MODEL_SAFETY_LINES = (
    "passive/read-only against profile registry",
    "writes a single export artifact via atomic write",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
    "no network access",
    "no cockpit sidecar connection",
)


def _cockpit_export_profile_model_help():
    return f"""RytmRandomizer passive CLI: cockpit-export-profile-model

Usage:
  python -m rytm_randomizer.cli cockpit-export-profile-model --profile-id <id> --profiles-dir <path> --output <file.rymp> --unsigned
  python -m rytm_randomizer.cli cockpit-export-profile-model --profile-id <id> --profiles-dir <path> --output <file.rymp> --key-hex <hex> --key-id <label>
  python -m rytm_randomizer.cli cockpit-export-profile-model --profile-id <id> --profiles-dir <path> --output <file.rymp> --unsigned --overwrite --json
  python -m rytm_randomizer.cli cockpit-export-profile-model --help

Arguments:
  --profile-id <id>          Profile id to export (required)
  --profiles-dir <path>      Directory containing the profile registry (required)
  --output <file.rymp>       Destination .rymp file (required)
  --key-hex <hex>            HMAC-SHA256 key as hex string (requires --key-id)
  --key-id <label>           Operator-visible label for the signing key
  --unsigned                 Export without a signing envelope
  --overwrite                Replace --output if it already exists
  --json                     Emit a JSON ack instead of text

Behavior:
  Packs the requested ProfileModel into the portable RYMP binary, optionally
  HMAC-SHA256-signs it, atomically writes the bytes to --output, then verifies
  the bytes on disk by reading them back and running the cockpit verifier.
  The ack reports profile metadata, bytes written, whether an existing file
  was overwritten, the signed/unsigned mode, and the verification result.
  Either --key-hex/--key-id (signed) or --unsigned must be supplied explicitly —
  there is no silent default. --key-hex and --unsigned are mutually exclusive.

Safety:
{_safety_block(_COCKPIT_EXPORT_PROFILE_MODEL_SAFETY_LINES)}"""


_ANALOG_FOUR_SAVED_KIT_EXPORT_SAFETY_LINES: Final[tuple[str, ...]] = (
    "reads one operator-selected Analog Four saved-kit .syx file",
    "writes one generated .syx file via the canonical atomic writer",
    "only hardware-write-validated parameters are accepted",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
    "no network access",
)


def _analog_four_saved_kit_export_help():
    return f"""RytmRandomizer passive CLI: analog-four-saved-kit-export

Usage:
  python -m rytm_randomizer.cli analog-four-saved-kit-export --source <kit.syx> --output <kit.syx> --filter2-resonance 1:64
  python -m rytm_randomizer.cli analog-four-saved-kit-export --source <kit.syx> --output <kit.syx> --filter2-resonance 1:16 --filter2-resonance 2:48 --filter2-resonance 3:80 --filter2-resonance 4:112 --json
  python -m rytm_randomizer.cli analog-four-saved-kit-export --help

Arguments:
  --source <kit.syx>                 Hardware-exported source saved kit
  --output <kit.syx>                 Destination for the generated saved kit
  --filter2-resonance <track:value>  Track 1-4 and front-panel value 0-127; repeatable
  --overwrite                        Replace --output if it already exists
  --json                             Emit a JSON acknowledgment instead of text

Behavior:
  Validates and decodes one Analog Four MKII saved-kit frame, applies every
  requested hardware-validated Filter2 Resonance value, rebuilds the Elektron
  7-bit payload/checksum/length trailer, and atomically publishes the output.
  The acknowledgment reports the kit name, SHA256, byte count, track values,
  and concrete unpacked offsets. Existing output is refused unless --overwrite
  is explicit.

Safety:
{_safety_block(_ANALOG_FOUR_SAVED_KIT_EXPORT_SAFETY_LINES)}"""


def _analog_four_audio_patch_batch_help():
    from .cockpit.export.analog_four_patch_batch_cli import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: analog-four-audio-patch-batch

Usage:
  python -m rytm_randomizer.cli analog-four-audio-patch-batch --audio <path> --source-kit <kit.syx> --output-dir <dir>
  python -m rytm_randomizer.cli analog-four-audio-patch-batch --audio <path> --source-kit <kit.syx> --output-dir <dir> --track 2 --candidates 4 --json
  python -m rytm_randomizer.cli analog-four-audio-patch-batch --help

Arguments:
  --audio <path>           Short reference audio clip to analyze
  --source-kit <kit.syx>   Hardware-exported source saved kit
  --output-dir <dir>       Destination for candidate .syx and JSON sidecar files
  --track N                Analog Four track 1-4; default 1
  --candidates N           Candidate count 1-4; default 4
  --overwrite              Replace the stable manifest; reuse exact generation files
  --json                   Emit a JSON acknowledgment instead of text

Behavior:
  Runs real audio-dependent inference and generates up to four candidate patch
  genomes. Every candidate writes one saved-kit .syx file and one sidecar with
  the complete patch DNA plus its CC/NRPN live-dial plan. The current .syx
  writer applies only hardware-write-validated Filter2 Resonance; all other DNA
  remains represented in the sidecar as live-sendable, manual, or deferred.
  The acknowledgment reports the audio source hash, manifest path/hash,
  candidate paths, category counts, and safety contract. This is not a claim of full saved-kit coverage
  or Synthplant-equivalent learned accuracy.

Safety:
{_safety_block(SAFETY_LINES)}"""


def _analog_four_audio_patch_rank_help():
    from .cockpit.export.analog_four_patch_render_rank import (
        ANALOG_FOUR_RENDER_RANK_SAFETY,
    )

    return f"""RytmRandomizer passive CLI: analog-four-audio-patch-rank

Usage:
  python -m rytm_randomizer.cli analog-four-audio-patch-rank --reference <path> --manifest <batch.json> --render <N=path>
  python -m rytm_randomizer.cli analog-four-audio-patch-rank --reference <path> --manifest <batch.json> --render <1=path> --render <2=path> --json
  python -m rytm_randomizer.cli analog-four-audio-patch-rank --help

Arguments:
  --reference <path>       Original audio used to create the batch
  --manifest <batch.json>  Committed audio-patch batch manifest
  --render <N=path>        A4 recording for candidate 1-4; repeatable
  --json                   Emit deterministic JSON instead of text

Behavior:
  Hash-verifies each selected candidate sidecar, proves that --reference is
  the exact batch source, measures eleven envelope and timbre features from
  every A4 recording, and ranks candidates by weighted acoustic distance.
  The result identifies the closest candidate and exposes every feature delta.

Safety:
{_safety_block(ANALOG_FOUR_RENDER_RANK_SAFETY)}"""


def _cockpit_export_rehearsal_report_help():
    from .reports.cockpit_export_rehearsal import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: cockpit-export-rehearsal-report

Usage:
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path>
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> --key-id <label>
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> --unsigned
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> --output <path> --json
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --help

Arguments:
  --profile-id <id>          Required. Profile id to rehearse for model export.
  --profiles-dir <path>      Required. Directory the ProfileRegistry scans for user profiles.
  --key-id <label>           Optional. Signing key label; assume signed envelope export.
  --unsigned                 Optional. Assume unsigned export. Mutually exclusive with --key-id.
  --output <path>            Optional. Override the would-write output path.
  --label <text>             Optional. Surface label for GUI consumers.
  --json                     Optional. Emit deterministic JSON instead of text.

Behavior:
  Builds the passive model-export rehearsal surface for one ProfileModel
  resolved from the registry. The report shows the would-write output path,
  the format and model versions, the packed payload size and CRC32, whether
  the export would be signed, the signed-envelope size (if signed), the GUI
  surface contract (panels, state bindings, action controls, acceptance
  checks), blocked actions, and a replayable passive command. The report
  does not write any file, does not invoke the signer or writer, and does
  not connect to the cockpit sidecar.

Safety:
{_safety_block(SAFETY_LINES)}"""


def resolve_help_text(key: str) -> str:
    text = HELP_TEXT[key]
    if isinstance(text, str):
        return text
    if callable(text):
        resolved = text()
        if isinstance(resolved, str):
            return resolved
    raise TypeError(f"help text provider for {key!r} did not return a string")


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
  python -m rytm_randomizer.cli analog-rytm-midi-catalog-report
  python -m rytm_randomizer.cli manual-validation-kit-report [--phase <slug>] [--json]
  python -m rytm_randomizer.cli manual-feedback-packet-report [--scenario full|installer|profile|mock|hardware|review] [--json]
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
  python -m rytm_randomizer.cli analog-four-baseline-report --kit <syx-path> --pattern-kit <syx-path> --whole-project <syx-path> [--json]
  python -m rytm_randomizer.cli analog-four-patch-genome-report (--description <text>|--audio <path>) [--track N] [--candidate N] [--json]
  python -m rytm_randomizer.cli analog-four-patch-learning-report (--description <text>|--audio <path>) [--track N] [--candidate N] [--json]
  python -m rytm_randomizer.cli analog-four-patch-corpus-report (--description <text>|--audio <path>) [--track N] [--limit N] [--corpus-file <path>] [--json]
  python -m rytm_randomizer.cli analog-four-patch-send-plan-report (--description <text>|--audio <path>) [--track N] [--candidate N] [--json]
  python -m rytm_randomizer.cli local-model-copilot-report --question <text> [--description <text>] [--workflow docs|mutation|patch|all] [--model <name>] [--ask-local-model] [--json]
  python -m rytm_randomizer.cli analog-four-oxi-macro-report [<macro-name>] [--seed N] [--intensity N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report [<macro-name>] [--seed N] [--intensity N] [--limit N] [--json]
  python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report [--set-name <text>] [--sequence <macro,...>] [--seed N] [--json]
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
  python -m rytm_randomizer.cli style-crates-queue-journal-report [--json]
  python -m rytm_randomizer.cli style-crate-rehearsal-deck-report [--crate <key>] [--json]
  python -m rytm_randomizer.cli oxi-live-macro-catalog-report
  python -m rytm_randomizer.cli controller-brain-mapping-report [--json]
  python -m rytm_randomizer.cli controller-brain-rehearsal-report [--json]
  python -m rytm_randomizer.cli controller-brain-operator-package-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-runbook-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-state-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-implementation-bridge-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-desktop-blueprint-report [--json]
  python -m rytm_randomizer.cli controller-brain-live-desktop-app-plan-report [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--json]
  python -m rytm_randomizer.cli controller-brain-live-desktop-component-contract-report [--component-contract-label <text>] [--selector-prefix <text>] [--json]
  python -m rytm_randomizer.cli controller-brain-live-desktop-view-model-report [--view-model-label <text>] [--state-prefix <text>] [--json]
  python -m rytm_randomizer.cli controller-brain-live-desktop-render-contract-report [--render-contract-label <text>] [--surface-prefix <text>] [--json]
  python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report [--json]
  python -m rytm_randomizer.cli live-gui-performance-flow-model-report [--json]
  python -m rytm_randomizer.cli live-gui-performance-console-report [--json]
  python -m rytm_randomizer.cli oxi-live-set-strategy-report [--json]
  python -m rytm_randomizer.cli reference-style-blueprint-report (--description <text>|--audio <path>|--library <dir>) [--json]
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
  python -m rytm_randomizer.cli style-performance-arc-live-cue-sheet-report [<arc-key> ...] [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-reference-match-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-runbook-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-stage-routing-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-show-export-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-state-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--events] [--limit N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-readiness-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-control-surface-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-handoff-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-rehearsal-session-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-queue-report (--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--label <text>] [--capture-prefix <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-capture-review-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-sidecar-session-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-screen-contract-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-render-tree-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-overlay-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-frame-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-interaction-script-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-action-reducer-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-controller-state-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-transcript-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-playback-validation-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-contract-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-test-harness-readiness-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-implementation-bridge-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-blueprint-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-app-plan-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-component-contract-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--component-contract-label <text>] [--selector-prefix <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-view-model-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--component-contract-label <text>] [--selector-prefix <text>] [--view-model-label <text>] [--state-prefix <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-contract-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--component-contract-label <text>] [--selector-prefix <text>] [--view-model-label <text>] [--state-prefix <text>] [--render-contract-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-desktop-render-harness-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--component-contract-label <text>] [--selector-prefix <text>] [--view-model-label <text>] [--state-prefix <text>] [--render-contract-label <text>] [--render-harness-label <text>] [--runner-label <text>] [--json]
  python -m rytm_randomizer.cli style-performance-arc-live-gui-cockpit-boundary-readiness-report (--description <text>|--audio <path>|--library <dir>) (--capture-description <text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] [--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] [--render-target desktop-sidecar|test-harness|operator-dashboard] [--density standard|compact] [--overlay-label <text>] [--frame-label <text>] [--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] [--playback-label <text>] [--validation-label <text>] [--harness-label <text>] [--readiness-label <text>] [--bridge-label <text>] [--blueprint-label <text>] [--desktop-shell operator-dashboard|desktop-sidecar|test-harness] [--app-plan-label <text>] [--framework-target desktop-python|web-desktop|test-harness] [--component-contract-label <text>] [--selector-prefix <text>] [--view-model-label <text>] [--state-prefix <text>] [--render-contract-label <text>] [--render-harness-label <text>] [--runner-label <text>] [--boundary-label <text>] [--hardware-entrypoint <command>] [--passive-entrypoint <command>] [--ws-port-env <name>] [--json]
  python -m rytm_randomizer.cli cockpit-send-plan-readiness-report (--plan-json <json>|--plan-file <path>) [--label <text>] [--json]
  python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report (--plan-json <json>|--plan-file <path>|--readiness-json <json>|--readiness-file <path>) [--label <text>] [--json]
  python -m rytm_randomizer.cli cockpit-export-profile-model --profile-id <id> --profiles-dir <path> --output <file.rymp> [--key-hex <hex> --key-id <label>] [--unsigned] [--overwrite] [--json]
  python -m rytm_randomizer.cli analog-four-saved-kit-export --source <kit.syx> --output <kit.syx> --filter2-resonance <track:value> [--filter2-resonance <track:value> ...] [--overwrite] [--json]
  python -m rytm_randomizer.cli analog-four-audio-patch-batch --audio <path> --source-kit <kit.syx> --output-dir <dir> [--track N] [--candidates N] [--overwrite] [--json]
  python -m rytm_randomizer.cli analog-four-audio-patch-rank --reference <path> --manifest <batch.json> --render <N=path> [--render <N=path> ...] [--json]
  python -m rytm_randomizer.cli cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> [--key-id <label>] [--unsigned] [--output <path>] [--label <text>] [--json]
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
  analog-rytm-midi-catalog-report
                     Print the passive Analog Rytm MIDI catalog report.
  manual-validation-kit-report
                     Print the passive installer/UI/profile/manual validation kit.
  manual-feedback-packet-report
                     Print a passive manual testing feedback packet.
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
  analog-four-baseline-report
                     Compare initialized Analog Four kit, pattern+kit, and project dumps.
  analog-four-patch-genome-report
                     Generate passive Analog Four patch DNA candidates from audio or text.
  analog-four-patch-learning-report
                     Generate passive Analog Four patch learning and live-dial readiness.
  analog-four-patch-corpus-report
                     Rank passive Analog Four patch corpus matches from audio or text.
  analog-four-patch-send-plan-report
                     Preview generated Analog Four patch CC/NRPN live-dial events.
  local-model-copilot-report
                     Build passive local model copilot packets for docs, mutation, and A4 patch DNA.
  analog-four-oxi-macro-report
                     Print passive Analog Four OXI-style macro preview metadata.
  analog-four-oxi-macro-readiness-report
                     Print passive Analog Four OXI macro hardware-readiness metadata.
  analog-four-oxi-macro-set-planner-report
                     Print passive Analog Four OXI macro set-planner metadata.
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
  style-crates-queue-journal-report
                     Print the passive Style Crates, Queue, and Mutation Journal report.
  style-crate-rehearsal-deck-report
                     Print passive GUI-ready style crate rehearsal cards.
  oxi-live-macro-catalog-report
                     Print passive OXI live macro cards and A4 runway state.
  controller-brain-mapping-report
                     Print passive 16-encoder controller-brain intent maps.
  controller-brain-rehearsal-report
                     Print passive controller-brain rehearsal and template export packets.
  controller-brain-operator-package-report
                     Print passive controller-brain to operator package ledgers.
  controller-brain-live-runbook-report
                     Print passive controller-brain live runbook steps.
  controller-brain-live-state-report
                     Print passive controller-brain live state rows, queued intents, and audit events.
  controller-brain-live-bridge-readiness-report
                     Print passive controller-brain bridge readiness packets and gates.
  controller-brain-live-dispatch-rehearsal-report
                     Print passive controller-brain shadow dispatch decisions and gates.
  controller-brain-live-feedback-rehearsal-report
                     Print passive controller-brain feedback frames and output gates.
  controller-brain-live-cockpit-handoff-report
                     Print passive controller-brain Cockpit handoff cards and disabled controls.
  controller-brain-live-implementation-bridge-report
                     Print passive controller-brain implementation bindings and gates.
  controller-brain-live-desktop-blueprint-report
                     Print passive controller-brain desktop regions and component contracts.
  controller-brain-live-desktop-app-plan-report
                     Print passive controller-brain app routes and component file hints.
  controller-brain-live-desktop-component-contract-report
                     Print passive controller-brain desktop component API contracts.
  controller-brain-live-desktop-view-model-report
                     Print passive controller-brain desktop view models and state bindings.
  controller-brain-live-desktop-render-contract-report
                     Print passive controller-brain desktop render surfaces and bindings.
  rytm-live-macro-hardware-rehearsal-report
                     Print passive Rytm macro hardware rehearsal checklist.
  live-gui-performance-flow-model-report
                     Print the passive live GUI performance flow model.
  live-gui-performance-console-report
                     Print the passive Cockpit performance console model.
  oxi-live-set-strategy-report
                     Print passive OXI live set strategy chapters and pad policy.
  reference-style-blueprint-report
                     Translate a style reference into a passive Rytm plus Analog Four blueprint.
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
  style-performance-arc-live-runbook-report
                     Build passive live performance runbooks from arcs or references.
  style-performance-arc-stage-routing-report
                     Build passive stage snapshot routing from arcs or references.
  style-performance-arc-stage-rehearsal-state-report
                     Build passive stage rehearsal states from arcs or references.
  style-performance-arc-live-set-cockpit-report
                     Build passive live set cockpits from arcs or references.
  style-performance-arc-live-show-export-report
                     Build passive live show export packets from arcs or references.
  style-performance-arc-live-transition-timeline-report
                     Build passive live transition timelines from arcs or references.
  style-performance-arc-live-command-deck-report
                     Build passive live command decks from arcs or references.
  style-performance-arc-live-state-report
                     Build passive live performance state packets from arcs or references.
  style-performance-arc-live-readiness-report
                     Build passive GUI/audio-analyzer readiness from live state packets.
  style-performance-arc-live-control-surface-report
                     Build passive GUI/audio-analyzer control surfaces from live readiness.
  style-performance-arc-live-analyzer-handoff-report
                     Build passive audio analyzer handoffs from reference evidence.
  style-performance-arc-live-analyzer-targets-report
                     Build passive rehearsal targets for future live analyzer comparison.
  style-performance-arc-live-gui-analyzer-readiness-report
                     Build passive GUI/audio-analyzer readiness bundles.
  style-performance-arc-live-gui-rehearsal-session-report
                     Build passive GUI rehearsal session packets.
  style-performance-arc-live-gui-capture-queue-report
                     Build passive GUI/audio-analyzer capture queues.
  style-performance-arc-live-gui-capture-review-report
                     Review passive GUI/audio-analyzer captures with go/repeat/hold decisions.
  style-performance-arc-live-gui-sidecar-session-report
                     Compose passive capture review into one sidecar-ready GUI state.
  style-performance-arc-live-gui-screen-contract-report
                     Compose passive sidecar state into a deterministic GUI screen contract.
  style-performance-arc-live-gui-render-tree-report
                     Compose passive screen contract into a deterministic GUI render tree.
  style-performance-arc-live-gui-analyzer-overlay-report
                     Compose passive render tree into GUI analyzer overlay metadata.
  style-performance-arc-live-gui-analyzer-frame-report
                     Compose passive analyzer overlay into GUI frame metadata.
  style-performance-arc-live-gui-interaction-script-report
                     Compose passive analyzer frame into GUI interaction metadata.
  style-performance-arc-live-gui-action-reducer-report
                     Compose passive interaction script into GUI action reducer metadata.
  style-performance-arc-live-gui-controller-state-report
                     Compose passive action reducer into GUI controller state metadata.
  style-performance-arc-live-gui-playback-transcript-report
                     Compose passive controller state into GUI playback transcript metadata.
  style-performance-arc-live-gui-playback-validation-report
                     Compose passive playback transcript into GUI validation matrix metadata.
  style-performance-arc-live-gui-test-harness-contract-report
                     Compose passive validation matrix into GUI test-harness contract metadata.
  style-performance-arc-live-gui-test-harness-readiness-report
                     Compose passive GUI test-harness contract into readiness metadata.
  style-performance-arc-live-gui-implementation-bridge-report
                     Compose passive GUI readiness into future implementation wiring metadata.
  style-performance-arc-live-gui-desktop-blueprint-report
                     Compose passive GUI implementation metadata into a future desktop blueprint.
  style-performance-arc-live-gui-desktop-app-plan-report
                     Compose passive GUI desktop blueprint metadata into a future desktop app plan.
  style-performance-arc-live-gui-desktop-component-contract-report
                     Compose passive GUI desktop app plan metadata into future component contracts.
  style-performance-arc-live-gui-desktop-view-model-report
                     Compose passive GUI desktop component contracts into future view models.
  style-performance-arc-live-gui-desktop-render-contract-report
                    Compose passive GUI desktop view models into future render contracts.
  style-performance-arc-live-gui-desktop-render-harness-report
                    Compose passive GUI desktop render contracts into future render harnesses.
  style-performance-arc-live-gui-cockpit-boundary-readiness-report
                    Compose passive GUI desktop render harnesses into cockpit boundary readiness.
  cockpit-send-plan-readiness-report
                    Explain prepared cockpit SEND plan readiness for operator review.
  cockpit-send-plan-rehearsal-surface-report
                    Build GUI-ready passive SEND plan rehearsal surface state.
  cockpit-export-profile-model
                    Export a cockpit ProfileModel (pack + sign + atomic write + verify).
  analog-four-saved-kit-export
                    Render hardware-validated Analog Four values into a saved-kit SysEx file.
  analog-four-audio-patch-batch
                    Infer and export up to four passive Analog Four patch candidates from audio.
  analog-four-audio-patch-rank
                    Rank recorded Analog Four candidates against their reference audio.
  cockpit-export-rehearsal-report
                    Build GUI-ready passive cockpit model-export rehearsal surface state.
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
    "analog-rytm-midi-catalog-report": _analog_rytm_midi_catalog_report_help,
    "rytm-outbound-cc-repeatability-report": """RytmRandomizer passive CLI: rytm-outbound-cc-repeatability-report

Usage:
  python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report
  python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report --json
  python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report --help

Behavior:
  Prints the passive all-12-track outbound CC repeatability checklist for the next manual validation pass.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "manual-validation-kit-report": """RytmRandomizer passive CLI: manual-validation-kit-report

Usage:
  python -m rytm_randomizer.cli manual-validation-kit-report [--phase <slug>] [--json]
  python -m rytm_randomizer.cli manual-validation-kit-report --phase mock_rehearsal
  python -m rytm_randomizer.cli manual-validation-kit-report --help

Behavior:
  Prints a passive installer, cockpit UI, profile workflow, mock rehearsal, single armed-smoke, and evidence closeout checklist for manual validation.
  Active hardware commands are instruction text only; this report does not execute them.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
    "manual-feedback-packet-report": """RytmRandomizer passive CLI: manual-feedback-packet-report

Usage:
  python -m rytm_randomizer.cli manual-feedback-packet-report
  python -m rytm_randomizer.cli manual-feedback-packet-report --scenario profile
  python -m rytm_randomizer.cli manual-feedback-packet-report --scenario hardware --json
  python -m rytm_randomizer.cli manual-feedback-packet-report --help

Behavior:
  Prints a deterministic manual feedback packet for installer, cockpit,
  profile wizard, analyzer, export, mock-control, and approved hardware-boundary
  observations. The packet is evidence only; it does not run the GUI or analyzer.

Safety:
  passive/read-only
  in-memory only
  no GUI launch
  no audio analysis
  no file writes
  no MIDI sending
  no port opening
  no hardware mutation
  no hardware required""",
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
    "analog-four-baseline-report": _analog_four_baseline_report_help,
    "analog-four-patch-genome-report": _analog_four_patch_genome_report_help,
    "analog-four-patch-learning-report": _analog_four_patch_learning_report_help,
    "analog-four-patch-corpus-report": _analog_four_patch_corpus_report_help,
    "analog-four-patch-send-plan-report": _analog_four_patch_send_plan_report_help,
    "local-model-copilot-report": _local_model_copilot_report_help,
    "analog-four-oxi-macro-report": _analog_four_oxi_macro_report_help,
    "analog-four-oxi-macro-readiness-report": (_analog_four_oxi_macro_readiness_report_help),
    "analog-four-oxi-macro-set-planner-report": (_analog_four_oxi_macro_set_planner_report_help),
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
    "style-crates-queue-journal-report": _style_crates_queue_journal_report_help,
    "style-crate-rehearsal-deck-report": _style_crate_rehearsal_deck_report_help,
    "oxi-live-macro-catalog-report": _oxi_live_macro_catalog_report_help,
    "controller-brain-mapping-report": _controller_brain_mapping_report_help,
    "controller-brain-rehearsal-report": _controller_brain_rehearsal_report_help,
    "controller-brain-operator-package-report": _controller_brain_operator_package_report_help,
    "controller-brain-live-runbook-report": (_controller_brain_live_runbook_report_help),
    "controller-brain-live-state-report": _controller_brain_live_state_report_help,
    "controller-brain-live-bridge-readiness-report": (
        _controller_brain_live_bridge_readiness_report_help
    ),
    "controller-brain-live-dispatch-rehearsal-report": (
        _controller_brain_live_dispatch_rehearsal_report_help
    ),
    "controller-brain-live-feedback-rehearsal-report": (
        _controller_brain_live_feedback_rehearsal_report_help
    ),
    "controller-brain-live-cockpit-handoff-report": (
        _controller_brain_live_cockpit_handoff_report_help
    ),
    "controller-brain-live-implementation-bridge-report": (
        _controller_brain_live_implementation_bridge_report_help
    ),
    "controller-brain-live-desktop-blueprint-report": (
        _controller_brain_live_desktop_blueprint_report_help
    ),
    "controller-brain-live-desktop-app-plan-report": (
        _controller_brain_live_desktop_app_plan_report_help
    ),
    "controller-brain-live-desktop-component-contract-report": (
        _controller_brain_live_desktop_component_contract_report_help
    ),
    "controller-brain-live-desktop-view-model-report": (
        _controller_brain_live_desktop_view_model_report_help
    ),
    "controller-brain-live-desktop-render-contract-report": (
        _controller_brain_live_desktop_render_contract_report_help
    ),
    "rytm-live-macro-hardware-rehearsal-report": (_rytm_live_macro_hardware_rehearsal_report_help),
    "live-gui-performance-flow-model-report": _live_gui_performance_flow_model_report_help,
    "live-gui-performance-console-report": _live_gui_performance_console_report_help,
    "oxi-live-set-strategy-report": _oxi_live_set_strategy_report_help,
    "reference-style-blueprint-report": _reference_style_blueprint_report_help,
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
    "style-performance-arc-live-runbook-report": (_style_performance_arc_live_runbook_report_help),
    "style-performance-arc-stage-routing-report": (
        _style_performance_arc_stage_routing_report_help
    ),
    "style-performance-arc-stage-rehearsal-state-report": (
        _style_performance_arc_stage_rehearsal_state_report_help
    ),
    "style-performance-arc-live-set-cockpit-report": (
        _style_performance_arc_live_set_cockpit_report_help
    ),
    "style-performance-arc-live-show-export-report": (
        _style_performance_arc_live_show_export_report_help
    ),
    "style-performance-arc-live-transition-timeline-report": (
        _style_performance_arc_live_transition_timeline_report_help
    ),
    "style-performance-arc-live-command-deck-report": (
        _style_performance_arc_live_command_deck_report_help
    ),
    "style-performance-arc-live-state-report": (_style_performance_arc_live_state_report_help),
    "style-performance-arc-live-readiness-report": (
        _style_performance_arc_live_readiness_report_help
    ),
    "style-performance-arc-live-control-surface-report": (
        _style_performance_arc_live_control_surface_report_help
    ),
    "style-performance-arc-live-analyzer-handoff-report": (
        _style_performance_arc_live_analyzer_handoff_report_help
    ),
    "style-performance-arc-live-analyzer-targets-report": (
        _style_performance_arc_live_analyzer_targets_report_help
    ),
    "style-performance-arc-live-gui-analyzer-readiness-report": (
        _style_performance_arc_live_gui_analyzer_readiness_report_help
    ),
    "style-performance-arc-live-gui-rehearsal-session-report": (
        _style_performance_arc_live_gui_rehearsal_session_report_help
    ),
    "style-performance-arc-live-gui-capture-queue-report": (
        _style_performance_arc_live_gui_capture_queue_report_help
    ),
    "style-performance-arc-live-gui-capture-review-report": (
        _style_performance_arc_live_gui_capture_review_report_help
    ),
    "style-performance-arc-live-gui-sidecar-session-report": (
        _style_performance_arc_live_gui_sidecar_session_report_help
    ),
    "style-performance-arc-live-gui-screen-contract-report": (
        _style_performance_arc_live_gui_screen_contract_report_help
    ),
    "style-performance-arc-live-gui-render-tree-report": (
        _style_performance_arc_live_gui_render_tree_report_help
    ),
    "style-performance-arc-live-gui-analyzer-overlay-report": (
        _style_performance_arc_live_gui_analyzer_overlay_report_help
    ),
    "style-performance-arc-live-gui-analyzer-frame-report": (
        _style_performance_arc_live_gui_analyzer_frame_report_help
    ),
    "style-performance-arc-live-gui-interaction-script-report": (
        _style_performance_arc_live_gui_interaction_script_report_help
    ),
    "style-performance-arc-live-gui-action-reducer-report": (
        _style_performance_arc_live_gui_action_reducer_report_help
    ),
    "style-performance-arc-live-gui-controller-state-report": (
        _style_performance_arc_live_gui_controller_state_report_help
    ),
    "style-performance-arc-live-gui-playback-transcript-report": (
        _style_performance_arc_live_gui_playback_transcript_report_help
    ),
    "style-performance-arc-live-gui-playback-validation-report": (
        _style_performance_arc_live_gui_playback_validation_report_help
    ),
    "style-performance-arc-live-gui-test-harness-contract-report": (
        _style_performance_arc_live_gui_test_harness_contract_report_help
    ),
    "style-performance-arc-live-gui-test-harness-readiness-report": (
        _style_performance_arc_live_gui_test_harness_readiness_report_help
    ),
    "style-performance-arc-live-gui-implementation-bridge-report": (
        _style_performance_arc_live_gui_implementation_bridge_report_help
    ),
    "style-performance-arc-live-gui-desktop-blueprint-report": (
        _style_performance_arc_live_gui_desktop_blueprint_report_help
    ),
    "style-performance-arc-live-gui-desktop-app-plan-report": (
        _style_performance_arc_live_gui_desktop_app_plan_report_help
    ),
    "style-performance-arc-live-gui-desktop-component-contract-report": (
        _style_performance_arc_live_gui_desktop_component_contract_report_help
    ),
    "style-performance-arc-live-gui-desktop-view-model-report": (
        _style_performance_arc_live_gui_desktop_view_model_report_help
    ),
    "style-performance-arc-live-gui-desktop-render-contract-report": (
        _style_performance_arc_live_gui_desktop_render_contract_report_help
    ),
    "style-performance-arc-live-gui-desktop-render-harness-report": (
        _style_performance_arc_live_gui_desktop_render_harness_report_help
    ),
    "style-performance-arc-live-gui-cockpit-boundary-readiness-report": (
        _style_performance_arc_live_gui_cockpit_boundary_readiness_report_help
    ),
    "cockpit-send-plan-readiness-report": _cockpit_send_plan_readiness_report_help,
    "cockpit-send-plan-rehearsal-surface-report": (
        _cockpit_send_plan_rehearsal_surface_report_help
    ),
    "cockpit-export-profile-model": _cockpit_export_profile_model_help,
    "analog-four-saved-kit-export": _analog_four_saved_kit_export_help,
    "analog-four-audio-patch-batch": _analog_four_audio_patch_batch_help,
    "analog-four-audio-patch-rank": _analog_four_audio_patch_rank_help,
    "cockpit-export-rehearsal-report": _cockpit_export_rehearsal_report_help,
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
