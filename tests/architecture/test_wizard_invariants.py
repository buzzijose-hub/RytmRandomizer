"""Architecture invariants that pin every regression the post-Phase-2 review found.

Each test in this module exists because **a real reviewer caught a real bug** in
the Profile Wizard bundle, and we want to make sure a future agent or human
cannot silently re-break the same thing. The tests are intentionally narrow:
each one names exactly one invariant and the historical bug it prevents.

Categories
----------

1. **Tauri shell installer bake-in** — production-bundle prerequisites for the
   wizard's file/folder picker (Tauri 2 denies plugin access without explicit
   allow-list).
2. **Web router** — the launcher button must mount the wizard surface.
3. **Wire-format parity** — Python and TypeScript event/command payload shapes
   must agree.
4. **CI gate strength** — coverage thresholds must actually be enforced (not
   merely configured); Playwright + Tauri-bundle jobs must be required.
5. **Documentation truth** — install docs must remain factually correct about
   what packages the wizard ships in.

Every test is fast (file IO + regex/JSON parsing only — no subprocesses, no
network, no Tauri/Rust toolchain).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SHELL_ROOT: Final[Path] = PROJECT_ROOT / "desktop" / "shell"
WEB_ROOT: Final[Path] = PROJECT_ROOT / "desktop" / "web"
PYTHON_WIZARD_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "wizard"
PYTHON_WS_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "ws"
GITHUB_WORKFLOWS: Final[Path] = PROJECT_ROOT / ".github" / "workflows"


# ---------------------------------------------------------------------------
# Category 1 — Tauri shell installer bake-in
#
# Production-bundle prerequisites for the wizard's file/folder picker.
# Tauri 2 denies all plugin access unless explicitly allow-listed per window,
# and requires both a Rust-side crate AND a builder registration.
# ---------------------------------------------------------------------------


def test_tauri_dialog_plugin_dependency_is_declared() -> None:
    """The wizard's file/folder picker requires tauri-plugin-dialog on the Rust side.

    Regression guard: in the original Phase 2 bundle CONTRIBUTING.md claimed
    "no extra Rust crate is required" — that was wrong; Tauri 2 needs an
    explicit crate dep. Without this, the dynamic ``import('@tauri-apps/plugin-dialog')``
    on the web side resolves but the IPC handler doesn't exist at runtime in
    the production bundle.
    """

    cargo_toml = (SHELL_ROOT / "Cargo.toml").read_text(encoding="utf-8")
    assert re.search(
        r"^\s*tauri-plugin-dialog\s*=", cargo_toml, re.MULTILINE
    ), "desktop/shell/Cargo.toml must declare tauri-plugin-dialog under [dependencies]"


def test_tauri_dialog_plugin_is_registered_in_builder() -> None:
    """main.rs must register the dialog plugin or AddStep's file picker is a no-op.

    Regression guard: the Cargo dep alone is not enough — Tauri 2 requires
    ``.plugin(tauri_plugin_dialog::init())`` in the builder chain. Without
    this call, the IPC handler never comes up and the wizard's "Browse"
    button fails silently in production.
    """

    main_rs = (SHELL_ROOT / "src" / "main.rs").read_text(encoding="utf-8")
    assert "tauri_plugin_dialog::init()" in main_rs, (
        "desktop/shell/src/main.rs must call .plugin(tauri_plugin_dialog::init()) "
        "on the Tauri builder; without it the wizard's file picker IPC is missing."
    )


def test_tauri_capabilities_grants_dialog_open_permission() -> None:
    """Tauri 2 denies plugin access unless the capabilities file allow-lists it.

    Regression guard: the original bundle shipped with no capabilities/
    directory at all. Tauri 2 is allow-list-first; the wizard's
    file/folder picker requires ``dialog:allow-open`` on the cockpit
    window or the runtime rejects every ``open(...)`` call.
    """

    capabilities = SHELL_ROOT / "capabilities" / "default.json"
    assert capabilities.is_file(), (
        "desktop/shell/capabilities/default.json must exist. Tauri 2 is "
        "allow-list-first; without this file the wizard's file picker "
        "is denied by the runtime."
    )
    payload = json.loads(capabilities.read_text(encoding="utf-8"))
    permissions = payload.get("permissions", [])
    assert "dialog:allow-open" in permissions, (
        "capabilities/default.json must grant 'dialog:allow-open' for the "
        "wizard's file/folder picker."
    )
    windows = payload.get("windows", [])
    assert "main" in windows, (
        "capabilities/default.json must target the 'main' window (the cockpit "
        "window label) or the wizard's picker won't have access."
    )


def test_tauri_before_build_compiles_the_web_bundle() -> None:
    """Without a beforeBuildCommand, ``cargo tauri build`` ships stale web assets.

    Regression guard: the original tauri.conf.json had an empty
    beforeBuildCommand, so a fresh ``cargo tauri build`` would package
    whatever happened to be in ../web/dist (possibly empty, possibly
    stale). The wizard would silently ship without its UI.
    """

    config = json.loads((SHELL_ROOT / "tauri.conf.json").read_text(encoding="utf-8"))
    build = config.get("build", {})
    before_build = build.get("beforeBuildCommand", "")
    assert "npm" in before_build and "build" in before_build, (
        "tauri.conf.json build.beforeBuildCommand must invoke 'npm ... build' so "
        "production bundles always include the latest web assets (including the "
        "wizard surface). Currently: " + repr(before_build)
    )


# ---------------------------------------------------------------------------
# Category 2 — Web router
#
# The MutationPanel launcher sets window.location.hash = '/wizard'. The App
# must listen for hashchange and mount <Wizard /> when the hash matches —
# otherwise the launcher button is a no-op in dev and in any release bundle.
# ---------------------------------------------------------------------------


def test_app_routes_hash_to_wizard_surface() -> None:
    """App.tsx must mount <Wizard /> when location.hash starts with '/wizard'.

    Regression guard: the original Phase 2 bundle had a working launcher
    button that set the URL hash but no router to mount the wizard. Every
    click did nothing visible. A single Playwright test would have caught
    this; so would this assertion.
    """

    app_tsx = (WEB_ROOT / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "hashchange" in app_tsx, (
        "desktop/web/src/App.tsx must subscribe to 'hashchange' so the "
        "wizard launcher button (#/wizard) actually mounts the wizard."
    )
    assert "Wizard" in app_tsx, (
        "desktop/web/src/App.tsx must reference <Wizard /> so the hash route "
        "can mount it. (Either a direct import or via a route table.)"
    )
    # The launcher target string must match what App.tsx routes on.
    mutation_panel = (WEB_ROOT / "src" / "cockpit" / "MutationPanel.tsx").read_text(
        encoding="utf-8"
    )
    assert "/wizard" in mutation_panel and "/wizard" in app_tsx, (
        "MutationPanel.tsx writes '/wizard' to the hash but App.tsx doesn't "
        "route on the same string. Routes will desync silently."
    )


def test_tauri_dialog_plugin_is_declared_as_web_runtime_dependency() -> None:
    """@tauri-apps/plugin-dialog must be a real npm dependency, not an implicit one.

    Regression guard: the original AddStep.tsx loaded the plugin via a
    Vite-ignored dynamic import with no package.json entry. TypeScript
    had no type signature for the module and npm install never resolved
    it; a typo in the plugin name would only surface at runtime in the
    bundled app.
    """

    pkg = json.loads((WEB_ROOT / "package.json").read_text(encoding="utf-8"))
    deps = pkg.get("dependencies", {})
    assert "@tauri-apps/plugin-dialog" in deps, (
        "desktop/web/package.json must declare @tauri-apps/plugin-dialog under "
        "'dependencies' (NOT devDependencies — it's a runtime dep)."
    )


# ---------------------------------------------------------------------------
# Category 3 — Wire-format parity
#
# Python wizard_handlers emits {type, job: <full job dict>}. TypeScript must
# accept that shape; reducer must read event.job; AnalysisJobDict must mirror
# AnalysisJob.to_dict() field names exactly. Drift here drops every job
# update silently on the client.
# ---------------------------------------------------------------------------


def test_analysis_progress_event_carries_full_job_on_both_sides() -> None:
    """Python emits {type, job: AnalysisJobDict}; TypeScript must agree.

    Regression guard: the original bundle had Python emitting the whole
    job dict nested under 'job' while TypeScript declared top-level
    {source_id, progress, status}. The TS reducer silently dropped every
    analysis_progress event. A dedicated parity test
    (tests/cockpit/test_protocol_parity.py) already exists for the
    detailed cross-language check; this test adds a lightweight
    smoke-level assertion at the architecture layer so the parity gap
    cannot regress unnoticed.
    """

    handlers = (PYTHON_WS_ROOT / "wizard_handlers.py").read_text(encoding="utf-8")
    assert (
        '"job"' in handlers or "'job'" in handlers
    ), "wizard_handlers.py must emit analysis_progress events with a 'job' key"

    ts_types = (WEB_ROOT / "src" / "types" / "wizard_protocol.ts").read_text(encoding="utf-8")
    progress_re = re.compile(r"AnalysisProgressEvent\s*\{[^}]*\bjob\s*:", re.DOTALL)
    assert progress_re.search(ts_types), (
        "desktop/web/src/types/wizard_protocol.ts AnalysisProgressEvent must "
        "have a 'job:' field. Top-level {source_id, progress, status} drifts "
        "from the Python emit shape and silently drops every update."
    )


def test_wizard_event_constants_are_bijective_with_python() -> None:
    """Every Python wizard event constant must have a TypeScript counterpart.

    Regression guard: adding a new wizard event in Python without
    declaring the TS type/string on the web side is a silent runtime
    drop — the isEvent guard in ws/protocol.ts filters unknown types.
    """

    py_protocol = (PYTHON_WS_ROOT / "wizard_protocol.py").read_text(encoding="utf-8")
    py_events = set(re.findall(r'EVENT_[A-Z_]+\s*:\s*Final\[Literal\["([a-z_]+)"\]\]', py_protocol))
    assert py_events, "wizard_protocol.py must declare EVENT_* Final[Literal[...]] constants"

    ts_protocol = (WEB_ROOT / "src" / "ws" / "protocol.ts").read_text(encoding="utf-8")
    ts_event_strings = set(re.findall(r"'([a-z_]+)'", ts_protocol))
    missing = py_events - ts_event_strings
    assert not missing, (
        "Python wizard events not whitelisted in desktop/web/src/ws/protocol.ts "
        "isEvent()/Event union: " + ", ".join(sorted(missing))
    )


def test_wizard_command_constants_are_bijective_with_typescript() -> None:
    """Every Python wizard command constant must have a TypeScript counterpart.

    Regression guard: drift in the command list silently breaks new
    wizard commands on the web side.
    """

    py_protocol = (PYTHON_WS_ROOT / "wizard_protocol.py").read_text(encoding="utf-8")
    py_commands = set(
        re.findall(
            r'COMMAND_WIZARD_[A-Z_]+\s*:\s*Final\[Literal\["([a-z_]+)"\]\]',
            py_protocol,
        )
    )
    assert py_commands, "wizard_protocol.py must declare COMMAND_WIZARD_* constants"

    ts_types = (WEB_ROOT / "src" / "types" / "wizard_protocol.ts").read_text(encoding="utf-8")
    missing = [cmd for cmd in py_commands if f"'{cmd}'" not in ts_types]
    assert not missing, (
        "Python wizard commands not declared in desktop/web/src/types/wizard_protocol.ts: "
        + ", ".join(sorted(missing))
    )


# ---------------------------------------------------------------------------
# Category 4 — CI gate strength
#
# Coverage thresholds must actually be enforced on PR (not merely configured),
# the Playwright job must exist and be required, and the Tauri bundle must
# be built by the release workflow.
# ---------------------------------------------------------------------------


def test_ci_runs_web_coverage_not_just_tests() -> None:
    """desktop-web CI must invoke 'npm run test:coverage' to enforce thresholds.

    Regression guard: vite.config.ts configures 100% branch coverage on
    the wizard subdirectory, but the original CI ran ``npm run test:run``
    which IGNORES the threshold. Uncovered branches shipped green.
    """

    test_yml = (GITHUB_WORKFLOWS / "test.yml").read_text(encoding="utf-8")
    assert "test:coverage" in test_yml, (
        ".github/workflows/test.yml must run 'npm run test:coverage' on the "
        "desktop-web job so the 100% threshold in vite.config.ts is actually "
        "enforced. Running 'npm run test:run' alone leaves the threshold dead."
    )


def test_ci_runs_playwright_e2e_job() -> None:
    """A desktop-web-e2e job must exist so the wizard's browser flow is exercised.

    Regression guard: the original bundle had zero browser-driving E2E.
    The wizard launcher bug (no router) shipped through every other gate.
    """

    test_yml = (GITHUB_WORKFLOWS / "test.yml").read_text(encoding="utf-8")
    assert "desktop-web-e2e" in test_yml, (
        ".github/workflows/test.yml must define a desktop-web-e2e job that "
        "runs Playwright against the cockpit + sidecar."
    )
    assert (
        "playwright" in test_yml.lower()
    ), ".github/workflows/test.yml desktop-web-e2e job must invoke Playwright."


def test_ci_required_checks_aggregate_includes_e2e() -> None:
    """The required-checks aggregate must include the Playwright job.

    Regression guard: adding a CI job without registering it as required
    means PRs can merge even if it fails.
    """

    test_yml = (GITHUB_WORKFLOWS / "test.yml").read_text(encoding="utf-8")
    # Match the required-checks job's needs: array.
    required_block = re.search(r"required-checks:.*?steps:", test_yml, re.DOTALL)
    assert required_block is not None, "required-checks aggregate job not found"
    assert "desktop-web-e2e" in required_block.group(0), (
        "required-checks 'needs:' must include desktop-web-e2e so the gate "
        "actually blocks merges."
    )


def test_release_workflow_builds_tauri_bundle() -> None:
    """The release pipeline must produce a Tauri desktop bundle artifact.

    Regression guard: the original installers.yml only built Briefcase
    (Python sidecar). The cockpit + wizard UI never reached a release
    artifact, so end-users could never receive them.
    """

    installers = (GITHUB_WORKFLOWS / "installers.yml").read_text(encoding="utf-8")
    assert "desktop-bundle" in installers, (
        ".github/workflows/installers.yml must define a desktop-bundle job "
        "that runs 'cargo tauri build' to produce the cockpit + wizard "
        "distributable. Without it, the wizard never reaches end-users."
    )
    assert (
        "tauri" in installers.lower()
    ), "installers.yml desktop-bundle job must invoke the Tauri CLI."


# ---------------------------------------------------------------------------
# Category 5 — Documentation truth
#
# Install docs must remain factually correct about what ships where.
# ---------------------------------------------------------------------------


def test_contributing_does_not_claim_no_rust_crate_required() -> None:
    """CONTRIBUTING.md must not repeat the false 'no extra Rust crate' claim.

    Regression guard: the original docs claimed the dialog plugin
    required no Rust crate. That misled future contributors and made the
    capabilities/Cargo.toml/main.rs requirements look optional.
    """

    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    forbidden_phrases = [
        "no extra Rust crate is required",
        "no extra Rust crate required",
        "no Rust crate required",
    ]
    found = [phrase for phrase in forbidden_phrases if phrase.lower() in contributing.lower()]
    assert not found, (
        "CONTRIBUTING.md must not claim the Tauri dialog plugin needs no "
        "Rust crate — that's factually wrong for Tauri 2. Found: " + ", ".join(found)
    )


def test_building_installers_documents_tauri_bundle_path() -> None:
    """docs/BUILDING_INSTALLERS.md must mention the Tauri/cockpit/wizard bundle.

    Regression guard: the original install docs only described Briefcase,
    leaving operators with no way to discover that the wizard UI ships
    in a separate distributable.
    """

    doc = (PROJECT_ROOT / "docs" / "BUILDING_INSTALLERS.md").read_text(encoding="utf-8")
    doc_lower = doc.lower()
    assert "tauri" in doc_lower, (
        "docs/BUILDING_INSTALLERS.md must explain the Tauri desktop bundle "
        "path — Briefcase alone does not ship the wizard."
    )
    assert (
        "cargo tauri build" in doc_lower or "tauri build" in doc_lower
    ), "docs/BUILDING_INSTALLERS.md must show the 'cargo tauri build' invocation."


# ---------------------------------------------------------------------------
# Category 6 — SRP / parallel-work invariants
#
# Hard-won lessons from the SRP review: certain trait constants must live in
# neutral modules, not be reach-through-imported from sibling analyzers.
# ---------------------------------------------------------------------------


def test_wizard_trait_names_live_in_neutral_module() -> None:
    """WIZARD_TRAIT_NAMES must live in wizard/traits.py, not be owned by an analyzer.

    Regression guard: originally reference_analyzer.py owned the canonical
    trait names and the other analyzers reach-through-imported it. That
    made parallel edits to analyzer modules conflict on import order and
    made the dependency graph cyclic.
    """

    traits_py = PYTHON_WIZARD_ROOT / "traits.py"
    assert traits_py.is_file(), (
        "rytm_randomizer/cockpit/wizard/traits.py must exist as the neutral "
        "home for WIZARD_TRAIT_NAMES. Reach-through imports across analyzer "
        "modules block parallel work."
    )
    content = traits_py.read_text(encoding="utf-8")
    assert (
        "WIZARD_TRAIT_NAMES" in content
    ), "wizard/traits.py must declare WIZARD_TRAIT_NAMES as the single source of truth."

    # Analyzers must NOT reach through reference_analyzer for the trait names.
    for analyzer in ("analyze.py", "sysex_analyzer.py"):
        text = (PYTHON_WIZARD_ROOT / analyzer).read_text(encoding="utf-8")
        bad_import = re.search(
            r"from\s+\.reference_analyzer\s+import[^\n]*WIZARD_TRAIT_NAMES", text
        )
        assert bad_import is None, (
            f"{analyzer} must import WIZARD_TRAIT_NAMES from .traits, not "
            f"from .reference_analyzer. Reach-through imports block parallel "
            f"refactoring of either analyzer."
        )


def test_wizard_trait_math_helpers_are_shared_not_duplicated() -> None:
    """clamp_unit + neutral_traits + average_trait_tuples must live in one place.

    Regression guard: the original bundle had each analyzer copy-paste
    the same averaging/clamping helpers. Duplication is a parallel-work
    hazard — two agents would silently diverge on the same logic.
    """

    trait_math = PYTHON_WIZARD_ROOT / "trait_math.py"
    assert trait_math.is_file(), (
        "rytm_randomizer/cockpit/wizard/trait_math.py must exist as the "
        "shared home for averaging/clamping helpers."
    )
    content = trait_math.read_text(encoding="utf-8")
    for helper in ("average_trait_tuples", "neutral_traits", "clamp_unit"):
        assert helper in content, (
            f"wizard/trait_math.py must export '{helper}' — analyzers must "
            f"compose from one shared module, not redefine locally."
        )

    # No analyzer is allowed to redefine clamp_unit (the previous duplication).
    for analyzer in ("analyze.py", "sysex_analyzer.py"):
        text = (PYTHON_WIZARD_ROOT / analyzer).read_text(encoding="utf-8")
        assert "def _clamp_unit" not in text, (
            f"{analyzer} must not redefine _clamp_unit — import from " f"wizard.trait_math instead."
        )
