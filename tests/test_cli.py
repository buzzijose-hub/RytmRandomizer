import json
import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _operator_docs_text() -> str:
    """Return the concatenated operator-facing docs (README + CLI_REFERENCE).

    Historically the README carried the full CLI command appendix and every
    ``test_readme_mentions_*`` assertion read straight from ``README.md``.
    The product-facing README rewrite moved the deep command reference into
    ``docs/CLI_REFERENCE.md`` to keep the landing page scannable; the
    operator-facing invariant -- "every passive CLI command is documented
    for an operator who reads our docs" -- is unchanged, it just spans two
    files now. This helper reads BOTH and returns the joined text so the
    existing assertions keep working without each having to know the
    layout. New tests should call this helper too.
    """

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    cli_ref_path = PROJECT_ROOT / "docs" / "CLI_REFERENCE.md"
    cli_ref = cli_ref_path.read_text(encoding="utf-8") if cli_ref_path.exists() else ""
    return readme + "\n" + cli_ref


USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | project-status-report "
    "[--summary|--json|--check] | mock-mapper-report | runtime-plan-report | "
    "active-boundary-report | mock-runtime-active-bridge-report | "
    "anchor-profile-report | behavior-parity-report | "
    "rytm-12-pad-machine-matrix-report | manual-feedback-packet-report [--scenario "
    "full|installer|profile|mock|hardware|review] [--json] | "
    "rytm-snapshot-pad-compatibility-report | analog-rytm-midi-catalog-report | "
    "rytm-snapshot-intelligence-report <syx-path> [--slot N|--list] | "
    "rytm-snapshot-mutation-preview-report <syx-path> [--slot N] [--depth N] "
    "[--events] [--limit N] | rytm-style-snapshot-routing-report <syx-path> "
    "<style-key> [--slot N] [--discovery N] [--json] | "
    "rytm-style-mutation-intent-report <syx-path> <style-key> [--slot N] [--discovery "
    "N] [--json] | rytm-style-mutation-render-plan-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | rytm-style-mutation-mock-preview-report "
    "<syx-path> <style-key> [--slot N] [--discovery N] [--events] [--limit N] [--json] "
    "| rytm-style-kit-readiness-report <syx-path> <style-key> [--discovery N] [--limit "
    "N] [--json] | analog-four-style-snapshot-routing-report <syx-path> <style-key> "
    "[--slot N] [--discovery N] [--json] | analog-four-style-mutation-intent-report "
    "<syx-path> <style-key> [--slot N] [--discovery N] [--json] | "
    "analog-four-style-mutation-mock-preview-report <syx-path> <style-key> [--slot N] "
    "[--discovery N] [--events] [--limit N] [--json] | analog-four-kit-catalog-report "
    "<syx-path> [--limit N] [--json] | analog-four-baseline-report --kit <syx-path> "
    "--pattern-kit <syx-path> --whole-project <syx-path> [--json] | "
    "analog-four-patch-genome-report (--description <text>|--audio <path>) [--track N] "
    "[--candidate N] [--json] | analog-four-patch-learning-report (--description "
    "<text>|--audio <path>) [--track N] [--candidate N] [--json] | "
    "analog-four-patch-corpus-report (--description <text>|--audio <path>) [--track N] "
    "[--limit N] [--corpus-file <path>] [--json] | analog-four-patch-send-plan-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json] | "
    "local-model-copilot-report --question <text> [--description <text>] [--workflow "
    "docs|mutation|patch|all] [--model <name>] [--ask-local-model] [--json] | "
    "analog-four-oxi-macro-report [<macro-name>] [--seed N] [--intensity N] [--events] "
    "[--limit N] [--json] | analog-four-oxi-macro-readiness-report [<macro-name>] "
    "[--seed N] [--intensity N] [--limit N] [--json] | "
    "analog-four-oxi-macro-set-planner-report [--set-name <text>] [--sequence "
    "<macro,...>] [--seed N] [--json] | analog-four-style-kit-readiness-report "
    "<syx-path> <style-key> [--discovery N] [--limit N] [--json] | "
    "dual-machine-style-kit-readiness-report <rytm-syx-path> <a4-syx-path> <style-key> "
    "[--discovery N] [--limit N] [--json] | dual-machine-style-kit-selection-report "
    "<style-key> --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--discovery N] [--limit N] [--json] | "
    "dual-machine-style-selection-mock-preview-report <style-key> --rytm <syx-path> "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--discovery N] [--events] [--limit N] [--json] | "
    "dual-machine-style-live-audition-report <style-key> [<style-key> ...] --rytm "
    "<syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--discovery N] [--events] "
    "[--limit N] [--json] | dual-machine-style-performance-set-plan-report <style-key> "
    "[<style-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | dual-machine-style-snapshot-routing-report <rytm-syx-path> "
    "<a4-syx-path> <style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json] "
    "| dual-machine-style-mutation-intent-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--json] | "
    "dual-machine-style-mutation-mock-preview-report <rytm-syx-path> <a4-syx-path> "
    "<style-key> [--rytm-slot N] [--a4-slot N] [--discovery N] [--events] [--limit N] "
    "[--json] | inspect-command <key> | dual-machine-target-report <rytm|a4|both> | "
    "inspect-scene <key> | inspect-group-profile <key> | list-commands | list-scenes | "
    "list-group-profiles | style-profile-report | style-crates-queue-journal-report "
    "[--json] | style-crate-rehearsal-deck-report [--crate <key>] [--json] | "
    "oxi-live-macro-catalog-report | controller-brain-mapping-report [--json] | "
    "controller-brain-rehearsal-report [--json] | "
    "controller-brain-operator-package-report [--json] | "
    "controller-brain-live-runbook-report [--json] | "
    "controller-brain-live-state-report [--json] | "
    "controller-brain-live-bridge-readiness-report [--json] | "
    "controller-brain-live-dispatch-rehearsal-report [--json] | "
    "controller-brain-live-feedback-rehearsal-report [--json] | "
    "controller-brain-live-cockpit-handoff-report [--json] | "
    "controller-brain-live-implementation-bridge-report [--json] | "
    "rytm-live-macro-hardware-rehearsal-report [--json] | "
    "live-gui-performance-flow-model-report [--json] | "
    "live-gui-performance-console-report [--json] | oxi-live-set-strategy-report "
    "[--json] | reference-style-blueprint-report (--description <text>|--audio "
    "<path>|--library <dir>) [--json] | list-style-profiles | inspect-style-profile "
    "<key> | search-style-profiles <query> | style-target-report | "
    "inspect-style-target <key> | style-performance-arc-report | "
    "list-style-performance-arcs | inspect-style-performance-arc <key> | "
    "search-style-performance-arcs <query> | style-performance-arc-set-plan-report "
    "<arc-key> --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-readiness-report [<arc-key> ...] "
    "--rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--limit N] "
    "[--json] | style-performance-arc-audition-packet-report [<arc-key> ...] --rytm "
    "<syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-rehearsal-manifest-report [<arc-key> "
    "...] --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-session-packet-report "
    "[<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-render-bundle-report [<arc-key> "
    "...] --rytm <syx-path> [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-cue-sheet-report [<arc-key> "
    "...] [--rytm <syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-reference-match-report "
    "(--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-runbook-report (--arc <arc-key>|--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--events] [--limit N] [--json] | style-performance-arc-stage-routing-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-stage-rehearsal-state-report (--arc "
    "<arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-set-cockpit-report (--arc "
    "<arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-show-export-report (--arc "
    "<arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-transition-timeline-report "
    "(--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] "
    "[--limit N] [--json] | style-performance-arc-live-command-deck-report (--arc "
    "<arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm "
    "<syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] "
    "[--lookahead N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-state-report (--arc <arc-key>|--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--events] [--limit N] [--json] | "
    "style-performance-arc-live-readiness-report (--arc <arc-key>|--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--json] | "
    "style-performance-arc-live-control-surface-report (--arc <arc-key>|--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--json] | "
    "style-performance-arc-live-analyzer-handoff-report (--description <text>|--audio "
    "<path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] "
    "[--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-analyzer-targets-report (--description <text>|--audio "
    "<path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope "
    "dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] "
    "[--segment-minutes N] [--discovery-start N] [--discovery-end N] [--cue N] "
    "[--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-gui-analyzer-readiness-report (--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--matches N] [--json] | "
    "style-performance-arc-live-gui-rehearsal-session-report (--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--label <text>] [--json] "
    "| style-performance-arc-live-gui-capture-queue-report (--description "
    "<text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four "
    "<syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] "
    "[--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end "
    "N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--label <text>] "
    "[--capture-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-capture-review-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--json] | "
    "style-performance-arc-live-gui-sidecar-session-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--json] | style-performance-arc-live-gui-analyzer-overlay-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--json] | "
    "style-performance-arc-live-gui-analyzer-frame-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--frame-label <text>] [--json] | "
    "style-performance-arc-live-gui-action-reducer-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--frame-label <text>] "
    "[--interaction-label <text>] [--reducer-label <text>] [--json] | "
    "style-performance-arc-live-gui-controller-state-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--frame-label <text>] "
    "[--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] "
    "[--json] | style-performance-arc-live-gui-playback-transcript-report "
    "(--description <text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--frame-label <text>] "
    "[--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--json] | "
    "style-performance-arc-live-gui-playback-validation-report (--description "
    "<text>|--audio <path>|--library <dir>) (--capture-description "
    "<text>|--capture-audio <path>|--capture-library <dir>) [--rytm <syx-path>] "
    "[--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] "
    "[--discovery-end N] [--cue N] [--lookahead N] [--matches N] [--takes N] [--slot "
    "capture-001] [--label <text>] [--capture-prefix <text>] [--sidecar-label <text>] "
    "[--screen-label <text>] [--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] [--density "
    "standard|compact] [--overlay-label <text>] [--frame-label <text>] "
    "[--interaction-label <text>] [--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] [--json] | "
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
    "al16-rytm-kit-export --reference <kit.syx> --recipe <recipe.yaml> "
    "--destination-slot <0..127> --output <kit.syx> | "
    "al16-rytm-mapping-evidence --reference <baseline.syx> "
    "--configured <configured.syx> --recipe <recipe.yaml> "
    "--gap-manifest <manifest.json> --expected-gap-manifest-sha256 <sha256> "
    "--report <report.json> | "
    "analog-four-audio-patch-batch --audio <path> --source-kit <kit.syx> "
    "--output-dir <dir> [--track N] [--candidates N] [--overwrite] [--json] | "
    "analog-four-audio-patch-rank --reference <path> --manifest <batch.json> "
    "--render <N=path> [--render <N=path> ...] [--json] | "
    "cockpit-export-rehearsal-report --profile-id <id> --profiles-dir <path> "
    "[--key-id <label>] [--unsigned] [--output <path>] [--label <text>] [--json] | "
    "manual-feedback-packet-report "
    "[--scenario full|installer|profile|mock|hardware|review] [--json] | "
    "scoped-randomization-preview [--json] | kit-morph-preview [--json] | "
    "search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | preview-command <key> | "
    "preview-scene <key> | preview-group-profile <key>"
)


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def expected_report_text():
    return normalize_newlines(
        (FIXTURES_DIR / "registry_report_expected.txt").read_text(encoding="utf-8")
    )


def fixture_text(filename):
    return normalize_newlines((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_cli_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.cli"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_top_level_help_exits_zero_and_matches_fixture():
    result = run_cli("--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_help_expected.txt")
    assert result.stderr == ""


def test_analog_four_audio_patch_batch_help_is_exact_and_passive():
    from rytm_randomizer.cockpit.export.analog_four_patch_batch_cli import SAFETY_LINES

    result = run_cli("analog-four-audio-patch-batch", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-audio-patch-batch" in help_text
    assert "real audio-dependent inference" in help_text
    assert "hardware-write-validated Filter2 Resonance" in help_text
    assert "complete patch DNA plus its CC/NRPN live-dial plan" in help_text
    assert "--studio-handoff" in help_text
    assert "--a4-output-port <name>" in help_text
    assert "zero calibration" in help_text
    assert "generated app --arm commands" in help_text
    assert "not a claim of full saved-kit coverage" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_audio_patch_rank_help_is_exact_and_passive():
    from rytm_randomizer.cockpit.export.analog_four_patch_render_rank import (
        ANALOG_FOUR_RENDER_RANK_SAFETY,
    )

    result = run_cli("analog-four-audio-patch-rank", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-audio-patch-rank" in help_text
    assert "--render <N=path>" in help_text
    assert "measures eleven envelope and timbre features" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in ANALOG_FOUR_RENDER_RANK_SAFETY]
    assert result.stderr == ""


@pytest.mark.parametrize(
    "command",
    [
        "analog-rytm-midi-catalog-report",
        "analog-four-baseline-report",
        "analog-four-patch-genome-report",
        "analog-four-patch-learning-report",
        "analog-four-patch-corpus-report",
        "analog-four-patch-send-plan-report",
        "local-model-copilot-report",
        "analog-four-oxi-macro-report",
        "analog-four-oxi-macro-readiness-report",
        "analog-four-oxi-macro-set-planner-report",
        "oxi-live-macro-catalog-report",
        "controller-brain-mapping-report",
        "controller-brain-rehearsal-report",
        "rytm-live-macro-hardware-rehearsal-report",
        "live-gui-performance-flow-model-report",
        "live-gui-performance-console-report",
        "oxi-live-set-strategy-report",
        "scoped-randomization-preview",
        "kit-morph-preview",
    ],
)
def test_lazy_help_text_entries_resolve_directly(command: str):
    from rytm_randomizer.help_text import resolve_help_text

    text = resolve_help_text(command)

    assert f"RytmRandomizer passive CLI: {command}" in text
    assert "Safety:" in text


def test_report_help_exits_zero_and_matches_fixture():
    result = run_cli("report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_report_help_expected.txt")
    assert result.stderr == ""


def test_project_status_report_help_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_mock_mapper_report_help_exits_zero_and_matches_fixture():
    result = run_cli("mock-mapper-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_mapper_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_runtime_plan_report_help_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_runtime_plan_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_active_boundary_report_help_exits_zero_and_matches_fixture():
    result = run_cli("active-boundary-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_active_boundary_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_help_exits_zero_and_matches_fixture():
    result = run_cli("mock-runtime-active-bridge-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_runtime_active_bridge_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_anchor_profile_report_help_exits_zero_and_matches_fixture():
    result = run_cli("anchor-profile-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_anchor_profile_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_behavior_parity_report_help_exits_zero_and_matches_fixture():
    result = run_cli("behavior-parity-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_behavior_parity_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_machine_matrix_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-12-pad-machine-matrix-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_machine_matrix_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_snapshot_pad_compatibility_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-snapshot-pad-compatibility-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_snapshot_pad_compatibility_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_analog_rytm_midi_catalog_report_help_exits_zero_and_matches_fixture():
    result = run_cli("analog-rytm-midi-catalog-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_analog_rytm_midi_catalog_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_snapshot_pad_compatibility_help_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import SAFETY_LINES

    result = run_cli("rytm-snapshot-pad-compatibility-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_rytm_midi_catalog_help_safety_matches_report_source():
    from rytm_randomizer.reports.analog_rytm_midi_catalog import SAFETY_LINES

    result = run_cli("analog-rytm-midi-catalog-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_snapshot_intelligence_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-snapshot-intelligence-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_snapshot_intelligence_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_snapshot_intelligence_help_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_snapshot_intelligence import SAFETY_LINES

    result = run_cli("rytm-snapshot-intelligence-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_snapshot_mutation_preview_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-snapshot-mutation-preview-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_snapshot_mutation_preview_report_help_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_snapshot_mutation_preview_help_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import SAFETY_LINES

    result = run_cli("rytm-snapshot-mutation-preview-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_style_snapshot_routing_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import SAFETY_LINES

    result = run_cli("rytm-style-snapshot-routing-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: rytm-style-snapshot-routing-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_style_mutation_intent_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_style_mutation_intent import SAFETY_LINES

    result = run_cli("rytm-style-mutation-intent-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: rytm-style-mutation-intent-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_style_mutation_render_plan_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_style_mutation_render_plan import SAFETY_LINES

    result = run_cli("rytm-style-mutation-render-plan-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: rytm-style-mutation-render-plan-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_style_mutation_mock_preview_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_style_mutation_mock_preview import SAFETY_LINES

    result = run_cli("rytm-style-mutation-mock-preview-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: rytm-style-mutation-mock-preview-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_style_snapshot_routing_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_style_snapshot_routing import SAFETY_LINES

    result = run_cli("analog-four-style-snapshot-routing-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-style-snapshot-routing-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_style_mutation_intent_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_style_mutation_intent import SAFETY_LINES

    result = run_cli("analog-four-style-mutation-intent-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-style-mutation-intent-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_style_mutation_mock_preview_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_style_mutation_mock_preview import SAFETY_LINES

    result = run_cli("analog-four-style-mutation-mock-preview-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-style-mutation-mock-preview-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_kit_catalog_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_kit_catalog import SAFETY_LINES

    result = run_cli("analog-four-kit-catalog-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-kit-catalog-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_baseline_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_baseline import SAFETY_LINES

    result = run_cli("analog-four-baseline-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-baseline-report" in help_text
    assert "--kit <syx-path>" in help_text
    assert "--pattern-kit <syx-path>" in help_text
    assert "--whole-project <syx-path>" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_oxi_macro_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import SAFETY_LINES

    result = run_cli("analog-four-oxi-macro-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-oxi-macro-report" in help_text
    assert "python -m rytm_randomizer.cli analog-four-oxi-macro-report" in help_text
    assert "--seed N" in help_text
    assert "--intensity N" in help_text
    assert "--events" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_rytm_style_kit_readiness_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.rytm_style_kit_readiness import SAFETY_LINES

    result = run_cli("rytm-style-kit-readiness-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: rytm-style-kit-readiness-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_analog_four_style_kit_readiness_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.analog_four_style_kit_readiness import SAFETY_LINES

    result = run_cli("analog-four-style-kit-readiness-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: analog-four-style-kit-readiness-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_kit_readiness_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_kit_readiness import SAFETY_LINES

    result = run_cli("dual-machine-style-kit-readiness-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-kit-readiness-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_kit_selection_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_kit_selection import SAFETY_LINES

    result = run_cli("dual-machine-style-kit-selection-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-kit-selection-report" in help_text
    assert "--scope dual|rytm-only|analog-four-only|a4-only" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_selection_mock_preview_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_selection_mock_preview import (
        SAFETY_LINES,
    )

    result = run_cli("dual-machine-style-selection-mock-preview-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert (
        "RytmRandomizer passive CLI: dual-machine-style-selection-mock-preview-report" in help_text
    )
    assert "--rank N" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_live_audition_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_live_audition import SAFETY_LINES

    result = run_cli("dual-machine-style-live-audition-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-live-audition-report" in help_text
    assert "<style-key> [<style-key> ...]" in help_text
    assert "--rank N" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_performance_set_plan_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_performance_set_plan import (
        SAFETY_LINES,
    )

    result = run_cli("dual-machine-style-performance-set-plan-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-performance-set-plan-report" in help_text
    assert "--total-minutes N" in help_text
    assert "--discovery-start N" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_snapshot_routing_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.dual_machine_style_snapshot_routing import SAFETY_LINES

    result = run_cli("dual-machine-style-snapshot-routing-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-snapshot-routing-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_mutation_intent_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.dual_machine_style_mutation_intent import SAFETY_LINES

    result = run_cli("dual-machine-style-mutation-intent-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: dual-machine-style-mutation-intent-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_dual_machine_style_mutation_mock_preview_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.dual_machine_style_mutation_mock_preview import SAFETY_LINES

    result = run_cli("dual-machine-style-mutation-mock-preview-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert (
        "RytmRandomizer passive CLI: dual-machine-style-mutation-mock-preview-report" in help_text
    )
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_style_profile_report_help_exits_zero_and_safety_matches_report_source():
    from rytm_randomizer.reports.style_profiles import SAFETY_LINES

    result = run_cli("style-profile-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: style-profile-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_style_crates_queue_journal_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.style_crates_queue_journal import SAFETY_LINES

    result = run_cli("style-crates-queue-journal-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: style-crates-queue-journal-report" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_oxi_live_set_strategy_report_help_exits_zero_and_safety_matches_source():
    from rytm_randomizer.reports.oxi_live_set_strategy import SAFETY_LINES

    result = run_cli("oxi-live-set-strategy-report", "--help")

    assert result.returncode == 0
    help_text = normalize_newlines(result.stdout)
    assert "RytmRandomizer passive CLI: oxi-live-set-strategy-report" in help_text
    assert "python -m rytm_randomizer.cli oxi-live-set-strategy-report --json" in help_text
    safety_block = help_text.split("Safety:\n", 1)[1]
    assert safety_block.splitlines() == [f"  {line}" for line in SAFETY_LINES]
    assert result.stderr == ""


def test_inspect_command_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_help_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_scene_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_inspect_scene_help_expected.txt")
    assert result.stderr == ""


def test_inspect_group_profile_help_exits_zero_and_matches_fixture():
    result = run_cli("inspect-group-profile", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_group_profile_help_expected.txt"
    )
    assert result.stderr == ""


def test_list_commands_help_exits_zero_and_matches_fixture():
    result = run_cli("list-commands", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_commands_help_expected.txt")
    assert result.stderr == ""


def test_list_scenes_help_exits_zero_and_matches_fixture():
    result = run_cli("list-scenes", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_scenes_help_expected.txt")
    assert result.stderr == ""


def test_list_group_profiles_help_exits_zero_and_matches_fixture():
    result = run_cli("list-group-profiles", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_list_group_profiles_help_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_help_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_help_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_help_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_help_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_help_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_help_expected.txt"
    )
    assert result.stderr == ""


def test_preview_command_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-command", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_command_help_expected.txt"
    )
    assert result.stderr == ""


def test_preview_scene_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-scene", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_preview_scene_help_expected.txt")
    assert result.stderr == ""


def test_preview_group_profile_help_exits_zero_and_matches_fixture():
    result = run_cli("preview-group-profile", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_group_profile_help_expected.txt"
    )
    assert result.stderr == ""


def test_report_command_exits_zero_and_matches_fixture():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == expected_report_text()
    assert result.stderr == ""


def test_project_status_report_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_summary_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--summary")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_summary_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_check_command_exits_zero_and_matches_fixture():
    result = run_cli("project-status-report", "--check")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_project_status_report_check_expected.txt"
    )
    assert result.stderr == ""


def test_project_status_report_json_command_exits_zero_and_returns_json():
    result = run_cli("project-status-report", "--json")

    assert result.returncode == 0
    parsed = json.loads(result.stdout)
    assert parsed["title"] == "RytmRandomizer Project Status Report"
    assert parsed["phase"]["creative_identity_candidate"] == "KitForge"
    assert parsed["behavior_parity"]["accepted_packet_count"] == 12
    assert parsed["runtime_plan"]["runtime_execution"] == "absent"
    assert parsed["active_boundary"]["active_cli_behavior"] == "absent"
    assert parsed["mock_runtime_active_bridge"]["emits_messages"] is False
    assert parsed["safety"]["real_midi"] == "present_behind_arm_flag"
    assert parsed["safety"]["port_opening"] == "present_behind_arm_flag"
    assert parsed["safety"]["active_execution"] == "present_behind_arm_flag"
    assert parsed["safety"]["default_mode"] == "passive"
    assert parsed["safety"]["hardware_required"] is False
    assert parsed["convergence"]["active_execution"] == "present"
    assert parsed["convergence"]["active_execution_gate"] == "--arm flag"
    assert parsed["convergence"]["default_mode"] == "passive"
    assert parsed["source"]["in_memory_only"] is True
    assert parsed["source"]["writes_files"] is False
    assert result.stderr == ""


def test_mock_mapper_report_command_exits_zero_and_matches_fixture():
    result = run_cli("mock-mapper-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_mock_mapper_report_expected.txt")
    assert result.stderr == ""


def test_analog_four_oxi_macro_report_command_exits_zero_and_is_deterministic():
    first = run_cli(
        "analog-four-oxi-macro-report",
        "hard-groove",
        "--seed",
        "23",
        "--intensity",
        "6",
        "--events",
        "--limit",
        "0",
    )
    second = run_cli(
        "analog-four-oxi-macro-report",
        "hard-groove",
        "--seed",
        "23",
        "--intensity",
        "6",
        "--events",
        "--limit",
        "0",
    )

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    output = normalize_newlines(first.stdout)
    assert "RytmRandomizer passive Analog Four OXI macro report" in output
    assert "Macro: hard-groove / Hard Groove" in output
    assert "Tracks: 4" in output
    assert "Shown events: 12" in output
    assert "Truncated events: 0" in output
    assert "- Track 1" in output
    assert "- Track 4" in output
    assert "- mock_only: True" in output
    assert "- hardware_required: False" in output
    assert "- opens_ports: False" in output
    assert "- sends_midi: False" in output
    assert "- active_behavior: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert first.stderr == ""
    assert second.stderr == ""


def test_analog_four_oxi_macro_report_json_exits_zero_and_is_machine_readable():
    result = run_cli(
        "analog-four-oxi-macro-report",
        "dub-pressure",
        "--seed",
        "3",
        "--intensity",
        "5",
        "--json",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["macro_name"] == "dub-pressure"
    assert payload["macro_label"] == "Dub Pressure"
    assert payload["track_count"] == 4
    assert payload["event_count"] == len(payload["events"])
    assert payload["mock_only"] is True
    assert payload["hardware_required"] is False
    assert payload["opens_ports"] is False
    assert payload["sends_midi"] is False
    assert payload["active_behavior"] is False
    assert {event["track"] for event in payload["events"]} == {1, 2, 3, 4}
    assert all(0 <= event["value"] <= 127 for event in payload["events"])
    assert "no MIDI sending" in payload["safety"]
    assert result.stderr == ""


def test_runtime_plan_report_command_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_runtime_plan_report_expected.txt")
    assert result.stderr == ""


def test_active_boundary_report_command_exits_zero_and_matches_fixture():
    result = run_cli("active-boundary-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_active_boundary_report_expected.txt"
    )
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_exits_zero_and_matches_fixture():
    result = run_cli("mock-runtime-active-bridge-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_mock_runtime_active_bridge_report_expected.txt"
    )
    assert result.stderr == ""


def test_anchor_profile_report_command_exits_zero_and_matches_fixture():
    result = run_cli("anchor-profile-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_anchor_profile_report_expected.txt"
    )
    assert result.stderr == ""


def test_behavior_parity_report_command_exits_zero_and_matches_fixture():
    result = run_cli("behavior-parity-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_behavior_parity_report_expected.txt"
    )
    assert result.stderr == ""


def test_rytm_machine_matrix_report_command_exits_zero_and_describes_pad_10():
    result = run_cli("rytm-12-pad-machine-matrix-report")

    output = normalize_newlines(result.stdout)
    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm 12-pad machine matrix" in output
    assert "- Pads: 12" in output
    assert "- Allowed pad-machine slots: 116" in output
    assert "Pad 10 / OH / Open Hihat:" in output
    assert "OH Classic (CC15 10)" in output
    assert result.stderr == ""


def test_rytm_snapshot_pad_compatibility_report_command_exits_zero_and_describes_pad_10():
    result = run_cli("rytm-snapshot-pad-compatibility-report")

    output = normalize_newlines(result.stdout)
    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot pad compatibility" in output
    assert "- Snapshot-ready pads: 4" in output
    assert "- Blocked pads: 8" in output
    assert "Pad 10 / OH / Open Hihat:" in output
    assert "Snapshot ready: False" in output
    assert result.stderr == ""


def test_analog_rytm_midi_catalog_report_command_exits_zero_and_describes_coverage():
    result = run_cli("analog-rytm-midi-catalog-report")

    output = normalize_newlines(result.stdout)
    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Rytm MIDI catalog" in output
    assert "- Total CC/NRPN rows: 323" in output
    assert "- Machine SRC rows: 224" in output
    assert "- Machine profiles with SRC rows: 33 / 33" in output
    assert "Validated runtime rows stay limited to the existing V1.34 mutation maps." in output
    assert result.stderr == ""


def test_rytm_snapshot_intelligence_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"SUBPROC")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("rytm-snapshot-intelligence-report", str(path))

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot intelligence" in result.stdout
    assert "Kit: SUBPROC" in result.stdout
    assert "Pad 10:" in result.stdout
    assert result.stderr == ""


def test_rytm_snapshot_intelligence_report_command_rejects_missing_file(tmp_path):
    result = run_cli("rytm-snapshot-intelligence-report", str(tmp_path / "missing.syx"))

    assert result.returncode == 2
    assert result.stdout == ""
    assert "SysEx file does not exist" in result.stderr
    assert "Traceback" not in result.stderr


def test_rytm_snapshot_intelligence_report_command_reports_out_of_range_slot(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"SLOT0")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("rytm-snapshot-intelligence-report", str(path), "--slot", "1")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Requested --slot 1" in result.stderr
    assert "only 1 supported Analog Rytm kit snapshot" in result.stderr
    assert "Slot 0: SLOT0" in result.stderr
    assert "Traceback" not in result.stderr


def test_rytm_snapshot_intelligence_report_command_lists_supported_slots(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    first_payload = rytm_real_layout_kit_payload(name=b"FIRST")
    second_payload = rytm_real_layout_kit_payload(name=b"SECOND")
    path = tmp_path / "bank.syx"
    path.write_bytes(
        bytes([0xF0]) + first_payload + bytes([0xF7, 0xF0]) + second_payload + bytes([0xF7])
    )

    result = run_cli("rytm-snapshot-intelligence-report", str(path), "--list")

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot file catalog" in result.stdout
    assert "Supported Rytm kit snapshots: 2" in result.stdout
    assert "Slot 0: FIRST" in result.stdout
    assert "Slot 1: SECOND" in result.stdout
    assert result.stderr == ""


def test_rytm_snapshot_mutation_preview_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"PREVIEW")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("rytm-snapshot-mutation-preview-report", str(path), "--depth", "2")

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot mutation preview" in result.stdout
    assert "Kit: PREVIEW" in result.stdout
    assert "Depth: 2" in result.stdout
    assert "- Plan ready: False" in result.stdout
    assert "- Mock messages: 0" in result.stdout
    assert "candidate-only" in result.stdout
    assert result.stderr == ""


def test_rytm_snapshot_mutation_preview_report_command_can_show_event_section(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"PREVIEW")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-snapshot-mutation-preview-report",
        str(path),
        "--events",
        "--limit",
        "3",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot mutation preview" in result.stdout
    assert "Event preview:" in result.stdout
    assert "- No event rows available because the plan is not ready." in result.stdout
    assert "candidate-only" in result.stdout
    assert result.stderr == ""


def test_rytm_snapshot_mutation_preview_report_command_rejects_missing_file(tmp_path):
    result = run_cli(
        "rytm-snapshot-mutation-preview-report",
        str(tmp_path / "missing.syx"),
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "SysEx file does not exist" in result.stderr
    assert "Traceback" not in result.stderr


def test_rytm_style_snapshot_routing_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"STYLE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-snapshot-routing-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "10",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style snapshot routing" in result.stdout
    assert "Kit: STYLE" in result.stdout
    assert "Style target: birmingham_pressure" in result.stdout
    assert "Discovery band: reference" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_snapshot_routing_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"RYTMJSON")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-snapshot-routing-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "95",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "RYTMJSON"
    assert parsed["style_key"] == "birmingham_pressure"
    assert parsed["discovery_amount"] == 95
    assert parsed["discovery_band"] == "wild_discovery"
    assert parsed["pads"][0]["pad"] == 1
    assert result.stderr == ""


def test_rytm_style_snapshot_routing_report_unknown_style_fails_safely(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"STYLE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("rytm-style-snapshot-routing-report", str(path), "ghost_style")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr


def test_rytm_style_mutation_intent_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"INTENT")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-intent-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "10",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style mutation intent" in result.stdout
    assert "Kit: INTENT" in result.stdout
    assert "Style target: birmingham_pressure" in result.stdout
    assert "Discovery band: reference" in result.stdout
    assert "Mutation depth: micro" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_mutation_intent_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"INTJSON")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-intent-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "95",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "INTJSON"
    assert parsed["style_key"] == "birmingham_pressure"
    assert parsed["discovery_band"] == "wild_discovery"
    assert parsed["mutation_depth"] == "wild"
    assert "RytmRandomizer passive Rytm" not in result.stdout
    assert result.stderr == ""


def test_rytm_style_mutation_render_plan_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"RENDER")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-render-plan-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "75",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style mutation render plan" in result.stdout
    assert "Kit: RENDER" in result.stdout
    assert "Render ready: True" in result.stdout
    assert "target" in result.stdout
    assert "window" in result.stdout
    assert "- no MIDI rendering" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_mutation_render_plan_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"RENJSON")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-render-plan-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "95",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "RENJSON"
    assert parsed["style_key"] == "birmingham_pressure"
    assert parsed["mutation_depth"] == "wild"
    assert parsed["render_ready"] is True
    assert parsed["pads"][0]["render_events"][0]["target_value"] >= 0
    assert result.stderr == ""


def test_rytm_style_mutation_mock_preview_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"MOCKPREV")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-mock-preview-report",
        str(path),
        "jose_core_techno",
        "--discovery",
        "45",
        "--events",
        "--limit",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style mutation mock preview" in result.stdout
    assert "Kit: MOCKPREV" in result.stdout
    assert "Preview ready: True" in result.stdout
    assert "CC" in result.stdout
    assert "- mock-only preview" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_mutation_mock_preview_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"MOCKJS")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "rytm-style-mutation-mock-preview-report",
        str(path),
        "jose_core_techno",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "MOCKJS"
    assert parsed["style_key"] == "jose_core_techno"
    assert parsed["discovery_amount"] == 45
    assert parsed["preview_ready"] is True
    assert parsed["events"][0]["control"] >= 0
    assert result.stderr == ""


def test_analog_four_style_snapshot_routing_report_command_reads_syx_file(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4STYLE".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-snapshot-routing-report",
        str(path),
        "industrial_dark",
        "--discovery",
        "10",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four style snapshot routing" in result.stdout
    assert "Kit: A4STYLE" in result.stdout
    assert "Style target: industrial_dark" in result.stdout
    assert "Discovery band: reference" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_analog_four_style_snapshot_routing_report_command_can_emit_json(tmp_path):
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4JSON".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-snapshot-routing-report",
        str(path),
        "industrial_dark",
        "--discovery",
        "95",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "A4JSON"
    assert parsed["style_key"] == "industrial_dark"
    assert parsed["discovery_amount"] == 95
    assert parsed["discovery_band"] == "wild_discovery"
    assert parsed["tracks"][0]["track"] == 1
    assert result.stderr == ""


def test_analog_four_style_snapshot_routing_report_unknown_style_fails_safely(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4STYLE".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("analog-four-style-snapshot-routing-report", str(path), "ghost_style")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr


def test_analog_four_style_mutation_intent_report_command_reads_syx_file(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4INTENT".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-mutation-intent-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "75",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four style mutation intent" in result.stdout
    assert "Kit: A4INTENT" in result.stdout
    assert "Style target: birmingham_pressure" in result.stdout
    assert "Mutation depth: strong" in result.stdout
    assert "bias 94" in result.stdout
    assert "direction higher" in result.stdout
    assert "- no MIDI rendering" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_style_mutation_intent_report_command_can_emit_json(tmp_path):
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4JSON".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-mutation-intent-report",
        str(path),
        "birmingham_pressure",
        "--discovery",
        "75",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "A4JSON"
    assert parsed["style_key"] == "birmingham_pressure"
    assert parsed["mutation_depth"] == "strong"
    assert parsed["tracks"][0]["intent_rows"][0]["target_bias"] == 94
    assert result.stderr == ""


def test_analog_four_style_mutation_intent_report_unknown_style_fails_safely(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4INTENT".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("analog-four-style-mutation-intent-report", str(path), "ghost_style")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr


def test_analog_four_style_mutation_mock_preview_report_command_reads_syx_file(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4MOCK".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-mutation-mock-preview-report",
        str(path),
        "jose_core_techno",
        "--events",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four style mutation mock preview" in result.stdout
    assert "Kit: A4MOCK" in result.stdout
    assert "Style target: jose_core_techno" in result.stdout
    assert "Preview ready: False" in result.stdout
    assert "candidate-only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_analog_four_style_mutation_mock_preview_report_command_can_emit_json(tmp_path):
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4MJSON".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "analog-four-style-mutation-mock-preview-report",
        str(path),
        "jose_core_techno",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["kit_name"] == "A4MJSON"
    assert parsed["style_key"] == "jose_core_techno"
    assert parsed["preview_ready"] is False
    assert parsed["mock_message_count"] == 0
    assert "candidate-only" in parsed["readiness_reason"]
    assert result.stderr == ""


def test_analog_four_style_mutation_mock_preview_report_unknown_style_fails_safely(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4MOCK".ljust(16, b"\x00")
    path = tmp_path / "a4.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("analog-four-style-mutation-mock-preview-report", str(path), "ghost_style")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr


def test_analog_four_kit_catalog_report_command_reads_syx_file(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4CAT".ljust(16, b"\x00")
    path = tmp_path / "a4-catalog.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("analog-four-kit-catalog-report", str(path))

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four kit catalog" in result.stdout
    assert "Supported kits: 1" in result.stdout
    assert "Candidate snapshots: 1" in result.stdout
    assert "Mutation-ready kits: 0" in result.stdout
    assert "Slot 0 | A4CAT | layout candidate | offsets candidate-only" in result.stdout
    assert "- SysEx decode only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_analog_four_kit_catalog_report_command_can_emit_json(tmp_path):
    first_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4ONE".ljust(16, b"\x00")
    second_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4TWO".ljust(16, b"\x00")
    path = tmp_path / "a4-catalog.syx"
    path.write_bytes(
        bytes([0xF0])
        + first_payload
        + bytes([0xF7])
        + bytes([0xF0])
        + second_payload
        + bytes([0xF7])
    )

    result = run_cli("analog-four-kit-catalog-report", str(path), "--limit", "1", "--json")

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["supported_kit_count"] == 2
    assert parsed["shown_count"] == 1
    assert parsed["truncated_count"] == 1
    assert parsed["entries"][0]["kit_name"] == "A4ONE"
    assert parsed["entries"][0]["snapshot_layout"] == "candidate"
    assert result.stderr == ""


def test_analog_four_baseline_report_command_compares_three_syx_sources(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4INIT".ljust(16, b"\x00")
    frame = bytes([0xF0]) + payload + bytes([0xF7])
    kit_path = tmp_path / "A4_Test1_Init_Kit.syx"
    pattern_kit_path = tmp_path / "A4_Test1_Init_A01_PatternKit.syx"
    whole_project_path = tmp_path / "A4_Test1_Init_WholeProject.syx"
    kit_path.write_bytes(frame)
    pattern_kit_path.write_bytes(frame)
    whole_project_path.write_bytes(frame + frame)

    result = run_cli(
        "analog-four-baseline-report",
        "--kit",
        str(kit_path),
        "--pattern-kit",
        str(pattern_kit_path),
        "--whole-project",
        str(whole_project_path),
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["baseline_status"] == "coherent-init-baseline"
    assert parsed["ready_for_changed_patch_diff"] is True
    assert parsed["sources"]["whole_project"]["supported_kit_count"] == 2
    assert result.stderr == ""


def test_analog_four_style_kit_readiness_report_command_reads_syx_file(tmp_path):
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4READY".ljust(16, b"\x00")
    path = tmp_path / "a4-readiness.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("analog-four-style-kit-readiness-report", str(path), "jose_core_techno")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four style kit readiness" in result.stdout
    assert "Style target: jose_core_techno" in result.stdout
    assert "Supported kits: 1" in result.stdout
    assert "Preview-ready kits: 0" in result.stdout
    assert "Blocked kits: 1" in result.stdout
    assert "Slot 0 | A4READY | layout candidate | preview_ready False" in result.stdout
    assert "- style/mock preview only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_analog_four_style_kit_readiness_report_command_can_emit_json(tmp_path):
    first_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4ONE".ljust(16, b"\x00")
    second_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4TWO".ljust(16, b"\x00")
    path = tmp_path / "a4-readiness.syx"
    path.write_bytes(
        bytes([0xF0])
        + first_payload
        + bytes([0xF7])
        + bytes([0xF0])
        + second_payload
        + bytes([0xF7])
    )

    result = run_cli(
        "analog-four-style-kit-readiness-report",
        str(path),
        "jose_core_techno",
        "--limit",
        "1",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["style_key"] == "jose_core_techno"
    assert parsed["kit_count"] == 2
    assert parsed["shown_count"] == 1
    assert parsed["truncated_count"] == 1
    assert parsed["entries"][0]["kit_name"] == "A4ONE"
    assert parsed["entries"][0]["preview_ready"] is False
    assert result.stderr == ""


def test_rytm_style_kit_readiness_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    path = tmp_path / "rytm-readiness.syx"
    path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"RYTMREADY") + bytes([0xF7])
    )

    result = run_cli("rytm-style-kit-readiness-report", str(path), "jose_core_techno")

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style kit readiness" in result.stdout
    assert "Style target: jose_core_techno" in result.stdout
    assert "Supported kits: 1" in result.stdout
    assert "Preview-ready kits: 1" in result.stdout
    assert "Blocked kits: 0" in result.stdout
    assert "Slot 0 | RYTMREADY | preview_ready True" in result.stdout
    assert "- style/mock preview only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_kit_readiness_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    first_payload = rytm_real_layout_kit_payload(name=b"RYTMONE")
    second_payload = rytm_real_layout_kit_payload(name=b"RYTMTWO")
    path = tmp_path / "rytm-readiness.syx"
    path.write_bytes(
        bytes([0xF0])
        + first_payload
        + bytes([0xF7])
        + bytes([0xF0])
        + second_payload
        + bytes([0xF7])
    )

    result = run_cli(
        "rytm-style-kit-readiness-report",
        str(path),
        "jose_core_techno",
        "--limit",
        "1",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["style_key"] == "jose_core_techno"
    assert parsed["kit_count"] == 2
    assert parsed["shown_count"] == 1
    assert parsed["truncated_count"] == 1
    assert parsed["entries"][0]["kit_name"] == "RYTMONE"
    assert parsed["entries"][0]["preview_ready"] is True
    assert result.stderr == ""


def test_dual_machine_style_kit_readiness_report_command_reads_syx_files(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"PAIRRYTM") + bytes([0xF7])
    )
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"PAIRA4".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "dual-machine-style-kit-readiness-report",
        str(rytm_path),
        str(a4_path),
        "jose_core_techno",
        "--limit",
        "1",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive dual-machine style kit readiness" in result.stdout
    assert "Style target: jose_core_techno" in result.stdout
    assert "Rytm kits: 1" in result.stdout
    assert "Analog Four kits: 1" in result.stdout
    assert "Pairings: 1" in result.stdout
    assert "Rytm slot 0 PAIRRYTM + A4 slot 0 PAIRA4" in result.stdout
    assert "readiness partial" in result.stdout
    assert "- rig-level kit-bank readiness only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_dual_machine_style_kit_readiness_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"PAIRJSON") + bytes([0xF7])
    )
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4PAIR".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "dual-machine-style-kit-readiness-report",
        str(rytm_path),
        str(a4_path),
        "jose_core_techno",
        "--json",
    )

    parsed = json.loads(result.stdout)
    assert result.returncode == 0
    assert parsed["pairing_count"] == 1
    assert parsed["entries"][0]["rig_readiness"] == "partial"
    assert parsed["entries"][0]["rytm"]["kit_name"] == "PAIRJSON"
    assert parsed["entries"][0]["analog_four"]["kit_name"] == "A4PAIR"
    assert result.stderr == ""


def test_dual_machine_style_snapshot_routing_report_command_reads_syx_files(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"DUORYTM") + bytes([0xF7])
    )
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"DUOA4".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "dual-machine-style-snapshot-routing-report",
        str(rytm_path),
        str(a4_path),
        "industrial_dark",
        "--discovery",
        "10",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive dual-machine style snapshot routing" in result.stdout
    assert "Style target: industrial_dark" in result.stdout
    assert "- Kit: DUORYTM" in result.stdout
    assert "- Kit: DUOA4" in result.stdout
    assert "Discovery band: reference" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_dual_machine_style_snapshot_routing_report_command_can_emit_json(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"DUOJSON") + bytes([0xF7])
    )
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4JSON".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "dual-machine-style-snapshot-routing-report",
        str(rytm_path),
        str(a4_path),
        "industrial_dark",
        "--discovery",
        "95",
        "--json",
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["style_key"] == "industrial_dark"
    assert payload["discovery_amount"] == 95
    assert payload["discovery_band"] == "wild_discovery"
    assert payload["machines"]["rytm"]["kit_name"] == "DUOJSON"
    assert payload["machines"]["analog_four"]["kit_name"] == "A4JSON"
    assert payload["safety"][0] == "passive/read-only"
    assert result.stderr == ""


def test_dual_machine_style_snapshot_routing_report_unknown_style_fails_safely(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    rytm_path = tmp_path / "rytm.syx"
    rytm_path.write_bytes(
        bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"DUORYTM") + bytes([0xF7])
    )
    a4_payload = bytes([0x00, 0x20, 0x3C, 0x07]) + b"DUOA4".ljust(16, b"\x00")
    a4_path = tmp_path / "a4.syx"
    a4_path.write_bytes(bytes([0xF0]) + a4_payload + bytes([0xF7]))

    result = run_cli(
        "dual-machine-style-snapshot-routing-report",
        str(rytm_path),
        str(a4_path),
        "ghost_style",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr


def test_readme_mentions_rytm_machine_matrix_report_command():
    text = _operator_docs_text()

    assert "rytm-12-pad-machine-matrix-report" in text
    assert "12-pad machine matrix" in text


def test_readme_mentions_rytm_snapshot_pad_compatibility_report_command():
    text = _operator_docs_text()

    assert "rytm-snapshot-pad-compatibility-report" in text
    assert "snapshot-pad compatibility" in text


def test_readme_mentions_analog_rytm_midi_catalog_report_command():
    text = _operator_docs_text()

    assert "analog-rytm-midi-catalog-report" in text
    assert "Analog Rytm MIDI catalog" in text


def test_readme_mentions_controller_brain_mapping_report_command():
    text = _operator_docs_text()

    assert "controller-brain-mapping-report" in text
    assert "controller-brain-rehearsal-report" in text
    assert "16-encoder" in text
    assert "controller-brain" in text


def test_readme_mentions_rytm_snapshot_intelligence_report_command():
    text = _operator_docs_text()

    assert "rytm-snapshot-intelligence-report" in text
    assert "snapshot intelligence" in text


def test_readme_mentions_rytm_snapshot_mutation_preview_report_command():
    text = _operator_docs_text()

    assert "rytm-snapshot-mutation-preview-report" in text
    assert "snapshot mutation preview" in text
    assert "--events" in text


def test_readme_mentions_style_profile_commands():
    text = _operator_docs_text()

    assert "style-profile-report" in text
    assert "style profiles" in text


def test_readme_mentions_analog_four_style_snapshot_routing_report_command():
    text = _operator_docs_text()

    assert "analog-four-style-snapshot-routing-report" in text
    assert "Analog Four style snapshot routing" in text


def test_readme_mentions_dual_machine_style_snapshot_routing_report_command():
    text = _operator_docs_text()

    assert "dual-machine-style-snapshot-routing-report" in text
    assert "dual-machine style snapshot routing" in text


def test_readme_mentions_dual_machine_style_selection_mock_preview_report_command():
    text = _operator_docs_text()

    assert "dual-machine-style-selection-mock-preview-report" in text
    assert "selection mock preview" in text


def test_readme_mentions_dual_machine_style_live_audition_report_command():
    text = _operator_docs_text()

    assert "dual-machine-style-live-audition-report" in text
    assert "live audition" in text


def test_readme_mentions_dual_machine_style_performance_set_plan_report_command():
    text = _operator_docs_text()

    assert "dual-machine-style-performance-set-plan-report" in text
    assert "performance set plan" in text


def test_readme_mentions_style_performance_arc_live_cue_sheet_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-cue-sheet-report" in text
    assert "live cue sheet" in text


def test_readme_mentions_style_performance_arc_reference_match_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-reference-match-report" in text
    assert "reference-match" in text


def test_readme_mentions_style_performance_arc_live_runbook_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-runbook-report" in text
    assert "live runbook" in text


def test_readme_mentions_style_performance_arc_stage_routing_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-stage-routing-report" in text
    assert "stage routing" in text
    assert "route cards" in text


def test_readme_mentions_style_performance_arc_stage_rehearsal_state_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-stage-rehearsal-state-report" in text
    assert "stage rehearsal" in text
    assert "go/rehearse/do-not-arm" in text


def test_readme_mentions_style_performance_arc_live_show_export_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-show-export-report" in text
    assert "live show export" in text
    assert "show handoff" in text


def test_readme_mentions_style_performance_arc_live_transition_timeline_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-transition-timeline-report" in text
    assert "live transition timeline" in text
    assert "transition cards" in text


def test_readme_mentions_style_performance_arc_live_command_deck_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-command-deck-report" in text
    assert "live command deck" in text
    assert "command cards" in text


def test_readme_mentions_style_performance_arc_live_state_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-state-report" in text
    assert "live state packet" in text
    assert "GUI-ready" in text


def test_readme_mentions_style_performance_arc_live_control_surface_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-control-surface-report" in text
    assert "control surface" in text
    assert "GUI/audio-analyzer" in text


def test_readme_mentions_style_performance_arc_live_analyzer_handoff_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-analyzer-handoff-report" in text
    assert "analyzer handoff" in text
    assert "FeatureReport meters" in text


def test_readme_mentions_style_performance_arc_live_analyzer_targets_report_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-analyzer-targets-report" in text
    assert "analyzer target" in text
    assert "future live analyzer comparison" in text


def test_readme_mentions_style_performance_arc_live_gui_analyzer_readiness_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-analyzer-readiness-report" in text
    assert "GUI/audio-analyzer readiness bundle" in text
    assert "blocked active actions" in text


def test_readme_mentions_style_performance_arc_live_gui_rehearsal_session_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-rehearsal-session-report" in text
    assert "GUI rehearsal session packet" in text
    assert "listen-only rehearsal take" in text


def test_readme_mentions_style_performance_arc_live_gui_capture_queue_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-capture-queue-report" in text
    assert "GUI/audio analyzer capture queue" in text
    assert "analyzer job" in text


def test_readme_mentions_style_performance_arc_live_gui_capture_review_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-capture-review-report" in text
    assert "GUI/audio analyzer capture review" in text
    assert "go/repeat/hold" in text


def test_readme_mentions_style_performance_arc_live_gui_sidecar_session_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-sidecar-session-report" in text
    assert "sidecar-ready GUI state" in text
    assert "disabled active controls" in text


def test_readme_mentions_style_performance_arc_live_gui_analyzer_overlay_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-analyzer-overlay-report" in text
    assert "GUI analyzer overlay" in text
    assert "meter widgets" in text


def test_readme_mentions_style_performance_arc_live_gui_analyzer_frame_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-analyzer-frame-report" in text
    assert "GUI analyzer frame" in text
    assert "frame events" in text


def test_readme_mentions_style_performance_arc_live_gui_action_reducer_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-action-reducer-report" in text
    assert "GUI action reducer" in text
    assert "control transition" in text


def test_readme_mentions_style_performance_arc_live_gui_controller_state_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-controller-state-report" in text
    assert "GUI controller state" in text
    assert "control-state" in text


def test_readme_mentions_style_performance_arc_live_gui_playback_transcript_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-playback-transcript-report" in text
    assert "GUI playback transcript" in text
    assert "playback transcript" in text


def test_readme_mentions_style_performance_arc_live_gui_playback_validation_command():
    text = _operator_docs_text()

    assert "style-performance-arc-live-gui-playback-validation-report" in text
    assert "GUI playback validation" in text
    assert "validation matrix" in text


def test_dual_machine_target_report_prints_both_devices(capsys) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["dual-machine-target-report", "both"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Target: both" in out
    assert "analog_rytm_mk2" in out
    assert "analog_four_mk2" in out


def test_dual_machine_target_report_rejects_unknown_target(capsys) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["dual-machine-target-report", "octatrack"])

    err = capsys.readouterr().err
    assert exit_code == 2
    assert "unknown target" in err
    assert "octatrack" not in err


def test_dual_machine_target_report_requires_target_arg(capsys) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["dual-machine-target-report"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "dual-machine-target-report <rytm|a4|both>" in captured.err


def test_report_command_is_deterministic():
    first = run_cli("report")
    second = run_cli("report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_command_is_deterministic():
    first = run_cli("project-status-report")
    second = run_cli("project-status-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_summary_command_is_deterministic():
    first = run_cli("project-status-report", "--summary")
    second = run_cli("project-status-report", "--summary")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_check_command_is_deterministic():
    first = run_cli("project-status-report", "--check")
    second = run_cli("project-status-report", "--check")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_project_status_report_json_command_is_deterministic():
    first = run_cli("project-status-report", "--json")
    second = run_cli("project-status-report", "--json")

    assert first.returncode == 0
    assert second.returncode == 0
    assert json.loads(first.stdout) == json.loads(second.stdout)
    assert first.stdout == second.stdout
    assert first.stderr == ""
    assert second.stderr == ""


def test_mock_mapper_report_command_is_deterministic():
    first = run_cli("mock-mapper-report")
    second = run_cli("mock-mapper-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_runtime_plan_report_command_is_deterministic():
    first = run_cli("runtime-plan-report")
    second = run_cli("runtime-plan-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_active_boundary_report_command_is_deterministic():
    first = run_cli("active-boundary-report")
    second = run_cli("active-boundary-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_mock_runtime_active_bridge_report_command_is_deterministic():
    first = run_cli("mock-runtime-active-bridge-report")
    second = run_cli("mock-runtime-active-bridge-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_anchor_profile_report_command_is_deterministic():
    first = run_cli("anchor-profile-report")
    second = run_cli("anchor-profile-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_behavior_parity_report_command_is_deterministic():
    first = run_cli("behavior-parity-report")
    second = run_cli("behavior-parity-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_rytm_snapshot_pad_compatibility_report_command_is_deterministic():
    first = run_cli("rytm-snapshot-pad-compatibility-report")
    second = run_cli("rytm-snapshot-pad-compatibility-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_analog_rytm_midi_catalog_report_command_is_deterministic():
    first = run_cli("analog-rytm-midi-catalog-report")
    second = run_cli("analog-rytm-midi-catalog-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_rytm_snapshot_intelligence_report_command_is_deterministic(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"DETERMIN")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    first = run_cli("rytm-snapshot-intelligence-report", str(path))
    second = run_cli("rytm-snapshot-intelligence-report", str(path))

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_rytm_snapshot_mutation_preview_report_command_is_deterministic(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"PREVDET")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))
    first = run_cli("rytm-snapshot-mutation-preview-report", str(path), "--depth", "2")
    second = run_cli("rytm-snapshot-mutation-preview-report", str(path), "--depth", "2")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_style_profile_report_command_exits_zero_and_describes_foundation():
    result = run_cli("style-profile-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style profile report" in output
    assert "- Profiles: 10" in output
    assert "Detroit Minimal" in output
    assert "Birmingham Pressure" in output
    assert "Jose Core Techno" in output
    assert "Analyzer hooks:" in output
    assert "- passive/read-only" in output
    assert "- no MIDI sending" in output
    assert result.stderr == ""


def test_style_profile_report_command_is_deterministic():
    first = run_cli("style-profile-report")
    second = run_cli("style-profile-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_style_crates_queue_journal_report_command_exits_zero_and_describes_mvp():
    result = run_cli("style-crates-queue-journal-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style crates queue journal report" in output
    assert "- Crates: 9" in output
    assert "dark_hypnotic: Dark Hypnotic" in output
    assert "industrial_broken: Industrial/Broken" in output
    assert "Staged Queue:" in output
    assert "Mutation Journal:" in output
    assert "Future Danger Modes:" in output
    assert "- no MIDI sending" in output
    assert result.stderr == ""


def test_style_crates_queue_journal_report_json_exits_zero_and_is_deterministic():
    first = run_cli("style-crates-queue-journal-report", "--json")
    second = run_cli("style-crates-queue-journal-report", "--json")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    payload = json.loads(first.stdout)
    model = payload["style_crates_queue_journal"]
    assert model["crate_count"] == 9
    assert model["queue"][0]["crate_key"] == "dark_hypnotic"
    assert model["journal"][0]["seed"] == "style-journal-warehouse-0001"
    assert payload["safety"][0] == "passive/read-only"
    assert first.stderr == ""
    assert second.stderr == ""


def test_rytm_live_macro_hardware_rehearsal_report_cli_text_and_json_are_deterministic():
    first = run_cli("rytm-live-macro-hardware-rehearsal-report")
    second = run_cli("rytm-live-macro-hardware-rehearsal-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert "RytmRandomizer passive Rytm live macro hardware rehearsal" in first.stdout
    assert "Pad lane checks:" in first.stdout
    assert "Pads 5, 9, 10, 11: SRC stays important" in first.stdout
    assert first.stderr == ""
    assert second.stderr == ""

    json_first = run_cli("rytm-live-macro-hardware-rehearsal-report", "--json")
    json_second = run_cli("rytm-live-macro-hardware-rehearsal-report", "--json")

    assert json_first.returncode == 0
    assert json_second.returncode == 0
    assert normalize_newlines(json_first.stdout) == normalize_newlines(json_second.stdout)
    payload = json.loads(json_first.stdout)
    assert payload["macros"][0]["name"] == "kit-core"
    assert payload["pad_lane_checks"][0]["pads"] == [5, 9, 10, 11]
    assert payload["safety"][2] == "does not send MIDI"
    assert json_first.stderr == ""
    assert json_second.stderr == ""


def test_list_style_profiles_exits_zero_and_lists_keys():
    result = run_cli("list-style-profiles")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style profile list" in output
    assert "- birmingham_pressure: Birmingham Pressure" in output
    assert "- warehouse_peak: Warehouse Peak" in output
    assert result.stderr == ""


def test_inspect_style_profile_known_key_exits_zero_and_describes_routing():
    result = run_cli("inspect-style-profile", "birmingham_pressure")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style profile inspection" in output
    assert "Key: birmingham_pressure" in output
    assert "Found: True" in output
    assert "Scenes: s3b, s4a, s4b" in output
    assert "Rytm focus:" in output
    assert "Analog Four focus:" in output
    assert result.stderr == ""


def test_inspect_style_profile_unknown_key_fails_safely():
    result = run_cli("inspect-style-profile", "DOES_NOT_EXIST")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "RytmRandomizer passive style profile inspection" in result.stderr
    assert "Found: False" in result.stderr
    assert "No MIDI was sent." in result.stderr


def test_search_style_profiles_known_query_exits_zero():
    result = run_cli("search-style-profiles", "hardgroove")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style profile search" in output
    assert "Query: hardgroove" in output
    assert "Match count: 1" in output
    assert "- hardgroove_percussive: Hardgroove Percussive" in output
    assert result.stderr == ""


def test_search_style_profiles_no_match_exits_zero():
    result = run_cli("search-style-profiles", "NO_MATCH")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Match count: 0" in output
    assert "- no matches found. No MIDI was sent. No command executed." in output
    assert result.stderr == ""


def test_unknown_style_profile_report_arguments_fail_safely():
    result = run_cli("style-profile-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_style_crates_queue_journal_arguments_fail_safely():
    result = run_cli("style-crates-queue-journal-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert (
        normalize_newlines(result.stderr)
        == "Error: style-crates-queue-journal-report accepts only optional --json"
    )


def test_missing_inspect_style_profile_key_fails_safely():
    result = run_cli("inspect-style-profile")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_search_style_profile_query_fails_safely():
    result = run_cli("search-style-profiles")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_style_target_report_command_exits_zero_and_is_passive():
    result = run_cli("style-target-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style target vector report" in output
    assert "- Targets: 10" in output
    assert "- no MIDI sending" in output
    assert result.stderr == ""


def test_inspect_style_target_known_key_exits_zero():
    result = run_cli("inspect-style-target", "birmingham_pressure")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style target vector inspection" in output
    assert "Key: birmingham_pressure" in output
    assert "drive_pressure: 95" in output
    assert result.stderr == ""


def test_inspect_style_target_unknown_key_fails_safely():
    result = run_cli("inspect-style-target", "ghost_style")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Style target not found" in result.stderr
    assert "No MIDI was sent" in result.stderr


def test_style_target_report_rejects_unknown_argument():
    result = run_cli("style-target-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_top_level_help_exposes_no_active_execution_commands():
    result = run_cli("--help")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "open-port" not in output
    assert "send-midi" not in output


def test_cli_source_does_not_evaluate_active_boundary_or_construct_sender():
    import inspect

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    import rytm_randomizer.cli as cli

    source = inspect.getsource(cli)

    assert "evaluate_mock_active_boundary" not in source
    assert "evaluate_mock_runtime_active_bridge" not in source
    assert "MockMidiSender" not in source
    assert "evaluate_anchor_profile_behavior" not in source
    assert "evaluate_pad1_lane_behavior" not in source


def test_project_status_report_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Report" in result.stdout
    assert result.stderr == ""


def test_project_status_report_summary_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--summary']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Summary" in result.stdout
    assert result.stderr == ""


def test_project_status_report_check_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--check']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RytmRandomizer Project Status Check" in result.stdout
    assert result.stderr == ""


def test_project_status_report_json_command_imports_no_real_midi_libraries():
    script = "\n".join(
        [
            "import runpy",
            "import sys",
            "sys.argv = ['rytm_randomizer.cli', 'project-status-report', '--json']",
            "runpy.run_module('rytm_randomizer.cli', run_name='__main__')",
            "assert 'mido' not in sys.modules",
            "assert 'rtmidi' not in sys.modules",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert '"title": "RytmRandomizer Project Status Report"' in result.stdout
    assert result.stderr == ""


def test_mock_mapper_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-mapper-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_runtime_plan_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['runtime-plan-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_active_boundary_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['active-boundary-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-runtime-active-bridge-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "sys.modules.pop('rytm_randomizer.mock_runtime_active_bridge', None)\n"
                "sys.modules.pop('rytm_randomizer.mock_midi', None)\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['mock-runtime-active-bridge-report'])\n"
                "assert code == 0\n"
                "assert 'rytm_randomizer.mock_runtime_active_bridge' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_behavior_report_modules():
    # After WS-P the per-report shim modules were collapsed into the unified
    # ``rytm_randomizer.reports`` module. Importing ``rytm_randomizer.cli``
    # must still keep the consolidated reports module (and any
    # report-adjacent behavior modules) out of ``sys.modules`` until a report
    # subcommand actually triggers a lazy import.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.reports' not in sys.modules\n"
                "assert 'rytm_randomizer.behavior.selected_isolated_pad' not in sys.modules\n"
                "assert 'rytm_randomizer.state.selected_isolated_pad_validation' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_runtime_or_bridge_report_modules():
    # After WS-P the runtime-plan and bridge report shim modules were
    # collapsed into the unified ``rytm_randomizer.reports`` module. The
    # lazy-load contract still applies: ``rytm_randomizer.reports`` must not
    # appear in ``sys.modules`` from importing ``rytm_randomizer.cli`` alone.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.reports' not in sys.modules\n"
                "assert 'rytm_randomizer.runtime_plan' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_runtime_active_bridge' not in sys.modules\n"
                "assert 'rytm_randomizer.mock_midi' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_registry_report_module():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.registry_report' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_cli_does_not_load_passive_metadata_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "import rytm_randomizer.cli\n"
                "assert 'rytm_randomizer.commands' not in sys.modules\n"
                "assert 'rytm_randomizer.scenes' not in sys.modules\n"
                "assert 'rytm_randomizer.profiles' not in sys.modules\n"
                "assert 'rytm_randomizer.registry' not in sys.modules\n"
                "assert 'rytm_randomizer.inspection' not in sys.modules\n"
                "assert 'rytm_randomizer.validation' not in sys.modules\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_anchor_profile_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['anchor-profile-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_behavior_parity_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['behavior-parity-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_inspect_command_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-command", "P3A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_command_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_command_known_key_is_deterministic():
    first = run_cli("inspect-command", "P3A")
    second = run_cli("inspect-command", "P3A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_scene_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-scene", "S1A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_inspect_scene_known_expected.txt")
    assert result.stderr == ""


def test_inspect_scene_known_key_is_deterministic():
    first = run_cli("inspect-scene", "S1A")
    second = run_cli("inspect-scene", "S1A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_group_profile_known_key_exits_zero_and_matches_fixture():
    result = run_cli("inspect-group-profile", "2")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_inspect_group_profile_known_expected.txt"
    )
    assert result.stderr == ""


def test_inspect_group_profile_known_key_is_deterministic():
    first = run_cli("inspect-group-profile", "2")
    second = run_cli("inspect-group-profile", "2")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_commands_exits_zero_and_matches_fixture():
    result = run_cli("list-commands")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_commands_expected.txt")
    assert result.stderr == ""


def test_list_scenes_exits_zero_and_matches_fixture():
    result = run_cli("list-scenes")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_scenes_expected.txt")
    assert result.stderr == ""


def test_list_group_profiles_exits_zero_and_matches_fixture():
    result = run_cli("list-group-profiles")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_list_group_profiles_expected.txt")
    assert result.stderr == ""


def test_list_commands_are_deterministic():
    first = run_cli("list-commands")
    second = run_cli("list-commands")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_scenes_are_deterministic():
    first = run_cli("list-scenes")
    second = run_cli("list-scenes")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_list_group_profiles_are_deterministic():
    first = run_cli("list-group-profiles")
    second = run_cli("list-group-profiles")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_commands_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "guarded")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_known_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "Wild")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_known_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_known_query_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "Hard")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_known_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-commands", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_commands_none_expected.txt"
    )
    assert result.stderr == ""


def test_search_scenes_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-scenes", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_search_scenes_none_expected.txt")
    assert result.stderr == ""


def test_search_group_profiles_no_match_exits_zero_and_matches_fixture():
    result = run_cli("search-group-profiles", "NO_MATCH")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_search_group_profiles_none_expected.txt"
    )
    assert result.stderr == ""


def test_search_commands_are_case_insensitive_and_deterministic():
    first = run_cli("search-commands", "guarded")
    second = run_cli("search-commands", "GUARDED")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert "Query: <input omitted>" in normalize_newlines(first.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_scenes_are_deterministic():
    first = run_cli("search-scenes", "Wild")
    second = run_cli("search-scenes", "Wild")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_search_group_profiles_are_deterministic():
    first = run_cli("search-group-profiles", "Hard")
    second = run_cli("search-group-profiles", "Hard")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_command_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-command", "J")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_command_known_expected.txt"
    )
    assert result.stderr == ""


def test_preview_command_known_key_is_deterministic():
    first = run_cli("preview-command", "J")
    second = run_cli("preview-command", "J")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_scene_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-scene", "S1A")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("cli_preview_scene_known_expected.txt")
    assert result.stderr == ""


def test_preview_scene_known_key_is_deterministic():
    first = run_cli("preview-scene", "S1A")
    second = run_cli("preview-scene", "S1A")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_preview_group_profile_known_key_exits_zero_and_matches_fixture():
    result = run_cli("preview-group-profile", "2")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_preview_group_profile_known_expected.txt"
    )
    assert result.stderr == ""


def test_preview_group_profile_known_key_is_deterministic():
    first = run_cli("preview-group-profile", "2")
    second = run_cli("preview-group-profile", "2")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""


def test_inspect_command_unknown_key_fails_safely():
    result = run_cli("inspect-command", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_command_unknown_expected.txt"
    )


def test_inspect_scene_unknown_key_fails_safely():
    result = run_cli("inspect-scene", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_scene_unknown_expected.txt"
    )


def test_inspect_group_profile_unknown_key_fails_safely():
    result = run_cli("inspect-group-profile", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_inspect_group_profile_unknown_expected.txt"
    )


def test_preview_command_unknown_key_fails_safely():
    result = run_cli("preview-command", "UNKNOWN")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_command_unknown_expected.txt"
    )


def test_preview_scene_unknown_key_fails_safely():
    result = run_cli("preview-scene", "DOES_NOT_EXIST")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_scene_unknown_expected.txt"
    )


def test_preview_group_profile_unknown_key_fails_safely():
    result = run_cli("preview-group-profile", "DOES_NOT_EXIST")

    assert result.returncode == 1
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == fixture_text(
        "cli_preview_group_profile_unknown_expected.txt"
    )


def test_missing_arguments_fail_safely():
    result = run_cli()

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_arguments_fail_safely():
    result = run_cli("mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_report_arguments_fail_safely():
    result = run_cli("report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_project_status_report_arguments_fail_safely():
    result = run_cli("project-status-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_mock_mapper_report_arguments_fail_safely():
    result = run_cli("mock-mapper-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_runtime_plan_report_arguments_fail_safely():
    result = run_cli("runtime-plan-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_active_boundary_report_arguments_fail_safely():
    result = run_cli("active-boundary-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_mock_runtime_active_bridge_report_arguments_fail_safely():
    result = run_cli("mock-runtime-active-bridge-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_anchor_profile_report_arguments_fail_safely():
    result = run_cli("anchor-profile-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_behavior_parity_report_arguments_fail_safely():
    result = run_cli("behavior-parity-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_list_arguments_fail_safely():
    result = run_cli("list-commands", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_search_query_fails_safely():
    result = run_cli("search-commands")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_unknown_search_arguments_fail_safely():
    result = run_cli("search-scenes", "Wild", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_command_key_fails_safely():
    result = run_cli("inspect-command")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_scene_key_fails_safely():
    result = run_cli("inspect-scene")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_inspect_group_profile_key_fails_safely():
    result = run_cli("inspect-group-profile")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_command_key_fails_safely():
    result = run_cli("preview-command")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_scene_key_fails_safely():
    result = run_cli("preview-scene")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_missing_preview_group_profile_key_fails_safely():
    result = run_cli("preview-group-profile")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE


def test_report_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("report")
    output = normalize_newlines(result.stdout)

    assert "- dispatches_commands: False" in output
    assert "- executes_commands: False" in output
    assert "- mutates_hardware: False" in output
    assert "- opens_ports: False" in output
    assert "- sends_midi: False" in output
    assert "- writes_sysex: False" in output
    assert "- no Pads 5-12 support" in output
    assert "- no Analog Four support" in output
    assert "- Pads 5-12" in output
    assert "- Analog Four" in output


def test_project_status_report_tracks_convergence_behind_arm_flag():
    result = run_cli("project-status-report")
    output = normalize_newlines(result.stdout)

    # Convergence wave: active execution is present, but only behind --arm.
    # The default landing mode stays passive and the monolith stays untouched.
    assert "- real_midi: present_behind_arm_flag" in output
    assert "- port_opening: present_behind_arm_flag" in output
    assert "- active_execution: present_behind_arm_flag" in output
    assert "- dispatch: present_behind_arm_flag" in output
    assert "- command_execution: present_behind_arm_flag" in output
    assert "- default_mode: passive" in output
    assert "- hardware_required: False" in output
    assert "- hardware_behavior: opt_in_behind_arm_flag" in output
    assert "- analog_four_support: absent" in output
    assert "- pads_5_12_support: absent" in output
    assert "- v134_reference: untouched" in output
    assert "- package_metadata: untouched" in output
    assert "- active_execution_gate: --arm flag" in output
    assert "- active_modes_present: 2" in output
    assert "- total_modes: 3" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output


def test_mock_mapper_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("mock-mapper-report")
    output = normalize_newlines(result.stdout)

    assert "- 2: My BD Hard (Pad 1 / BD Hard)" in output
    assert "- 3: My BD Classic (Pad 2 / BD Classic)" in output
    assert (
        "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - intentionally unsupported until separately approved"
        in output
    )
    assert "- mock_only: True" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- cli_wiring: absent" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_required: False" in output
    assert "- analog_four_support: absent" in output
    assert "- pads_5_12_support: absent" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("runtime-plan-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Supported Planning Inputs:" in output
    assert "- group_profile:2 -> Pad 1 / My BD Hard" in output
    assert "- group_profile:3 -> Pad 2 / My BD Classic" in output
    assert "Parked Planning Inputs:" in output
    assert "- group_profile:4 -> Pad 1 / My BD Acoustic" in output
    assert "- would_execute: False" in output
    assert "- mock_only: True" in output
    assert "- sends_real_midi: False" in output
    assert "- ports_allowed: False" in output
    assert "- hardware_required: False" in output
    assert "- runtime_execution: absent" in output
    assert "- cli_execution_wiring: absent" in output
    assert "- dispatch: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output


def test_active_boundary_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert "- group_profile 2: My BD Hard (Pad 1 / BD Hard)" in output
    assert "- boundary: mock_active_boundary" in output
    assert "- supported_candidate: group_profile:2" in output
    assert (
        "- fields: source_kind, source_key, target, armed, dry_run_confirmed, operator_intent, mock_only, sends_real_midi"
        in output
    )
    assert "- failure_reason: included on failure paths" in output
    assert (
        "- 3: My BD Classic (Pad 2 / BD Classic) - mock mapper/report scope only; not active-boundary supported"
        in output
    )
    assert "- 4: My BD Acoustic (Pad 4 / BD Acoustic) - parked until separately approved" in output
    assert "- explicit arming" in output
    assert "- dry-run confirmation" in output
    assert "- injected MockMidiSender" in output
    assert "- mock_only: True" in output
    assert "- hardware_required: False" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- active_cli_behavior: absent" in output
    assert "- dispatch: absent" in output
    assert "- command_execution: absent" in output
    assert "- scene_execution: absent" in output
    assert "- hardware_behavior: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_mock_runtime_active_bridge_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("mock-runtime-active-bridge-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Accepted Candidate:" in output
    assert "- group_profile:2 / My BD Hard -> Pad 1 / BD Hard" in output
    assert "Rejected Cases:" in output
    assert "- group_profile:3 / My BD Classic: bridge rejected" in output
    assert "Parked Cases:" in output
    assert "- group_profile:4 / My BD Acoustic: parked until separately approved" in output
    assert "- read_only: True" in output
    assert "- mock_only: True" in output
    assert "- invokes_bridge: False" in output
    assert "- constructs_sender: False" in output
    assert "- emits_messages: False" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- hardware_required: False" in output
    assert "- cli_execution_wiring: absent" in output
    assert "- runtime_execution: absent" in output
    assert "- dispatch: absent" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_behavior: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_active_boundary_report_output_keeps_boundary_profiles_explicit():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Unsupported Active Boundary Profiles:" in output
    assert "3: My BD Classic" in output
    assert "not active-boundary supported" in output
    assert "4: My BD Acoustic" in output
    assert "parked until separately approved" in output


def test_active_boundary_report_output_keeps_passive_safety_explicit():
    result = run_cli("active-boundary-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- active_cli_behavior: absent" in output
    assert "- dispatch: absent" in output
    assert "- command_execution: absent" in output
    assert "- scene_execution: absent" in output
    assert "- hardware_behavior: absent" in output


def test_anchor_profile_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("anchor-profile-report")
    output = normalize_newlines(result.stdout)

    assert "- direct_packet_2_anchor_profile: BH, BC, BS, BF" in output
    assert "- pad1_lane_anchor_profile: FZ, BP, PBH, BI, SBH, BA" in output
    assert "- pad2_lane_anchor_profile: P2B, P2H, P2C, P2F, P2Z" in output
    assert "- pad3_anchor: P3A, SA" in output
    assert "- pad4_anchor: P4A" in output
    assert "- group_anchor: O, Z" in output
    assert "- current_anchor_state: B, E" in output
    assert "- selected_profile_workflow: P, M" in output
    assert "- selected_isolated_pad_target: L" in output
    assert (
        "- PZ: selected_isolated_pad_anchor_return - deferred_selected_isolated_pad_anchor_return"
        in output
    )
    assert (
        "- 4: group_profile_mock_mapper_support - profile 4 mock mapper support remains parked until separately approved"
        in output
    )
    assert "- read_only: True" in output
    assert "- passive_cli_visibility: present" in output
    assert "- real_midi: absent" in output
    assert "- port_opening: absent" in output
    assert "- midi_sending: absent" in output
    assert "- active_behavior: absent" in output
    assert "- active_cli_wiring: absent" in output
    assert "- hardware_required: False" in output
    assert "- runtime_state: absent" in output
    assert "- package_metadata_changes: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_behavior_parity_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("behavior-parity-report")
    output = normalize_newlines(result.stdout)

    assert "- Packet 11A L selected isolated pad target intent" in output
    assert "- Packet 11B PZ selected isolated pad anchor-return readiness" in output
    assert "Selected Isolated Pad Packet Coverage:" in output
    assert "- Packet 11A: L - selected isolated pad target intent" in output
    assert "- Packet 11B: PZ - selected isolated pad anchor-return readiness" in output
    assert "Runtime-Adjacent Mock-Only Safe Failures:" in output
    assert "- PZ" in output
    assert "- B" in output
    assert "- L" in output
    assert "Parked Scope:" in output
    assert "- fourth runtime-adjacent candidate" in output
    assert "- profile 4 mock mapper support" in output
    assert "- Packet 12 CLI visibility" not in output
    assert "Absent Behavior:" in output
    assert "- dispatch" in output
    assert "- command execution" in output
    assert "- scene execution" in output
    assert "- runtime mutation" in output
    assert "- active CLI commands" in output
    assert "- real MIDI dependencies" in output
    assert "- port opening" in output
    assert "- MIDI sending" in output
    assert "- hardware behavior" in output
    assert "- Analog Four support" in output
    assert "- Pads 5-12 support" in output
    assert "Protected File State:" in output
    assert "- v134_reference: untouched" in output
    assert "- package_metadata: untouched" in output
    assert "- runtime_execution_logic: absent" in output
    assert "- read_only: True" in output
    assert "- in_memory_only: True" in output
    assert "- cli_visibility: present" in output
    assert "- active_behavior: absent" in output
    assert "- hardware_required: False" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output


def test_inspect_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-command", "P3A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_inspect_scene_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-scene", "S1A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_inspect_group_profile_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("inspect-group-profile", "2")
    output = normalize_newlines(result.stdout)

    assert "Machine value: 0" in output
    assert "Group pad: 1" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_commands_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-commands")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive command list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_scenes_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-scenes")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive scene list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_list_group_profiles_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("list-group-profiles")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive group profile list" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_commands_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-commands", "guarded")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive command search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_scenes_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-scenes", "Wild")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive scene search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_search_group_profiles_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("search-group-profiles", "Hard")
    output = normalize_newlines(result.stdout)

    assert "RytmRandomizer passive group profile search" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_command_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-command", "J")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "No MIDI would be sent." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_scene_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-scene", "S1A")
    output = normalize_newlines(result.stdout)

    assert "Executable: False" in output
    assert "No MIDI would be sent." in output
    assert "No scene would execute." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no scene execution" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


def test_preview_group_profile_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("preview-group-profile", "2")
    output = normalize_newlines(result.stdout)

    assert "Machine value: 0" in output
    assert "Group pad: 1" in output
    assert "No MIDI would be sent." in output
    assert "No command would execute." in output
    assert "No hardware would be mutated." in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no command execution" in output
    assert "- no hardware mutation" in output
    assert "Pad 5" not in output
    assert "Pad 6" not in output
    assert "Pad 7" not in output
    assert "Pad 8" not in output
    assert "Pad 9" not in output
    assert "Pad 10" not in output
    assert "Pad 11" not in output
    assert "Pad 12" not in output
    assert "Analog Four support" not in output


if __name__ == "__main__":
    test_importing_cli_prints_nothing()
    test_top_level_help_exits_zero_and_matches_fixture()
    test_report_help_exits_zero_and_matches_fixture()
    test_project_status_report_help_exits_zero_and_matches_fixture()
    test_mock_mapper_report_help_exits_zero_and_matches_fixture()
    test_runtime_plan_report_help_exits_zero_and_matches_fixture()
    test_active_boundary_report_help_exits_zero_and_matches_fixture()
    test_mock_runtime_active_bridge_report_help_exits_zero_and_matches_fixture()
    test_anchor_profile_report_help_exits_zero_and_matches_fixture()
    test_behavior_parity_report_help_exits_zero_and_matches_fixture()
    test_inspect_command_help_exits_zero_and_matches_fixture()
    test_inspect_scene_help_exits_zero_and_matches_fixture()
    test_inspect_group_profile_help_exits_zero_and_matches_fixture()
    test_list_commands_help_exits_zero_and_matches_fixture()
    test_list_scenes_help_exits_zero_and_matches_fixture()
    test_list_group_profiles_help_exits_zero_and_matches_fixture()
    test_search_commands_help_exits_zero_and_matches_fixture()
    test_search_scenes_help_exits_zero_and_matches_fixture()
    test_search_group_profiles_help_exits_zero_and_matches_fixture()
    test_preview_command_help_exits_zero_and_matches_fixture()
    test_preview_scene_help_exits_zero_and_matches_fixture()
    test_preview_group_profile_help_exits_zero_and_matches_fixture()
    test_report_command_exits_zero_and_matches_fixture()
    test_project_status_report_command_exits_zero_and_matches_fixture()
    test_project_status_report_summary_command_exits_zero_and_matches_fixture()
    test_project_status_report_check_command_exits_zero_and_matches_fixture()
    test_project_status_report_json_command_exits_zero_and_returns_json()
    test_mock_mapper_report_command_exits_zero_and_matches_fixture()
    test_runtime_plan_report_command_exits_zero_and_matches_fixture()
    test_active_boundary_report_command_exits_zero_and_matches_fixture()
    test_mock_runtime_active_bridge_report_command_exits_zero_and_matches_fixture()
    test_anchor_profile_report_command_exits_zero_and_matches_fixture()
    test_behavior_parity_report_command_exits_zero_and_matches_fixture()
    test_report_command_is_deterministic()
    test_project_status_report_command_is_deterministic()
    test_project_status_report_summary_command_is_deterministic()
    test_project_status_report_check_command_is_deterministic()
    test_project_status_report_json_command_is_deterministic()
    test_mock_mapper_report_command_is_deterministic()
    test_runtime_plan_report_command_is_deterministic()
    test_active_boundary_report_command_is_deterministic()
    test_mock_runtime_active_bridge_report_command_is_deterministic()
    test_anchor_profile_report_command_is_deterministic()
    test_behavior_parity_report_command_is_deterministic()
    test_top_level_help_exposes_no_active_execution_commands()
    test_cli_source_does_not_evaluate_active_boundary_or_construct_sender()
    test_project_status_report_command_imports_no_real_midi_libraries()
    test_project_status_report_summary_command_imports_no_real_midi_libraries()
    test_project_status_report_check_command_imports_no_real_midi_libraries()
    test_project_status_report_json_command_imports_no_real_midi_libraries()
    test_mock_mapper_report_command_imports_no_real_midi_libraries()
    test_runtime_plan_report_command_imports_no_real_midi_libraries()
    test_active_boundary_report_command_imports_no_real_midi_libraries()
    test_mock_runtime_active_bridge_report_command_imports_no_real_midi_libraries()
    test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi()
    test_importing_cli_does_not_load_behavior_report_modules()
    test_importing_cli_does_not_load_runtime_or_bridge_report_modules()
    test_importing_cli_does_not_load_registry_report_module()
    test_importing_cli_does_not_load_passive_metadata_modules()
    test_anchor_profile_report_command_imports_no_real_midi_libraries()
    test_behavior_parity_report_command_imports_no_real_midi_libraries()
    test_inspect_command_known_key_exits_zero_and_matches_fixture()
    test_inspect_command_known_key_is_deterministic()
    test_inspect_scene_known_key_exits_zero_and_matches_fixture()
    test_inspect_scene_known_key_is_deterministic()
    test_inspect_group_profile_known_key_exits_zero_and_matches_fixture()
    test_inspect_group_profile_known_key_is_deterministic()
    test_list_commands_exits_zero_and_matches_fixture()
    test_list_scenes_exits_zero_and_matches_fixture()
    test_list_group_profiles_exits_zero_and_matches_fixture()
    test_list_commands_are_deterministic()
    test_list_scenes_are_deterministic()
    test_list_group_profiles_are_deterministic()
    test_search_commands_known_query_exits_zero_and_matches_fixture()
    test_search_scenes_known_query_exits_zero_and_matches_fixture()
    test_search_group_profiles_known_query_exits_zero_and_matches_fixture()
    test_search_commands_no_match_exits_zero_and_matches_fixture()
    test_search_scenes_no_match_exits_zero_and_matches_fixture()
    test_search_group_profiles_no_match_exits_zero_and_matches_fixture()
    test_search_commands_are_case_insensitive_and_deterministic()
    test_search_scenes_are_deterministic()
    test_search_group_profiles_are_deterministic()
    test_preview_command_known_key_exits_zero_and_matches_fixture()
    test_preview_command_known_key_is_deterministic()
    test_preview_scene_known_key_exits_zero_and_matches_fixture()
    test_preview_scene_known_key_is_deterministic()
    test_preview_group_profile_known_key_exits_zero_and_matches_fixture()
    test_preview_group_profile_known_key_is_deterministic()
    test_inspect_command_unknown_key_fails_safely()
    test_inspect_scene_unknown_key_fails_safely()
    test_inspect_group_profile_unknown_key_fails_safely()
    test_preview_command_unknown_key_fails_safely()
    test_preview_scene_unknown_key_fails_safely()
    test_preview_group_profile_unknown_key_fails_safely()
    test_missing_arguments_fail_safely()
    test_unknown_arguments_fail_safely()
    test_unknown_report_arguments_fail_safely()
    test_unknown_project_status_report_arguments_fail_safely()
    test_unknown_mock_mapper_report_arguments_fail_safely()
    test_unknown_runtime_plan_report_arguments_fail_safely()
    test_unknown_active_boundary_report_arguments_fail_safely()
    test_unknown_mock_runtime_active_bridge_report_arguments_fail_safely()
    test_unknown_anchor_profile_report_arguments_fail_safely()
    test_unknown_behavior_parity_report_arguments_fail_safely()
    test_unknown_list_arguments_fail_safely()
    test_missing_search_query_fails_safely()
    test_unknown_search_arguments_fail_safely()
    test_missing_inspect_command_key_fails_safely()
    test_missing_inspect_scene_key_fails_safely()
    test_missing_inspect_group_profile_key_fails_safely()
    test_missing_preview_command_key_fails_safely()
    test_missing_preview_scene_key_fails_safely()
    test_missing_preview_group_profile_key_fails_safely()
    test_report_command_exposes_no_active_behavior_or_support_expansion()
    test_project_status_report_tracks_convergence_behind_arm_flag()
    test_mock_mapper_report_exposes_no_active_behavior_or_support_expansion()
    test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion()
    test_active_boundary_report_exposes_no_active_behavior_or_support_expansion()
    test_mock_runtime_active_bridge_report_exposes_no_active_behavior_or_support_expansion()
    test_active_boundary_report_output_keeps_boundary_profiles_explicit()
    test_active_boundary_report_output_keeps_passive_safety_explicit()
    test_anchor_profile_report_exposes_no_active_behavior_or_support_expansion()
    test_behavior_parity_report_exposes_no_active_behavior_or_support_expansion()
    test_inspect_command_exposes_no_active_behavior_or_support_expansion()
    test_inspect_scene_exposes_no_active_behavior_or_support_expansion()
    test_inspect_group_profile_exposes_no_active_behavior_or_support_expansion()
    test_list_commands_exposes_no_active_behavior_or_support_expansion()
    test_list_scenes_exposes_no_active_behavior_or_support_expansion()
    test_list_group_profiles_exposes_no_active_behavior_or_support_expansion()
    test_search_commands_exposes_no_active_behavior_or_support_expansion()
    test_search_scenes_exposes_no_active_behavior_or_support_expansion()
    test_search_group_profiles_exposes_no_active_behavior_or_support_expansion()
    test_preview_command_exposes_no_active_behavior_or_support_expansion()
    test_preview_scene_exposes_no_active_behavior_or_support_expansion()
    test_preview_group_profile_exposes_no_active_behavior_or_support_expansion()
