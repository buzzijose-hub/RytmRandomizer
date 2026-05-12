from pathlib import Path
import importlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def assert_mapping_is_immutable(mapping):
    try:
        mapping["mutation_attempt"] = "blocked"
    except TypeError:
        return
    raise AssertionError("mapping should be immutable")


def test_importing_runtime_plan_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.runtime_plan"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_runtime_safety_envelope_defaults_are_inert():
    from rytm_randomizer.runtime_plan import RuntimeSafetyEnvelope

    safety = RuntimeSafetyEnvelope()

    assert safety.mock_only is True
    assert safety.sends_real_midi is False
    assert safety.ports_allowed is False
    assert safety.hardware_required is False
    assert safety.reason == "mock-only runtime planning"


def test_runtime_intent_metadata_is_copied_and_immutable():
    from rytm_randomizer.runtime_plan import RuntimeIntent

    metadata = {"operator_intent": "preview only"}
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
        metadata=metadata,
    )

    metadata["operator_intent"] = "changed"

    assert intent.metadata["operator_intent"] == "preview only"
    assert_mapping_is_immutable(intent.metadata)


def test_create_blocked_runtime_preview_never_executes():
    from rytm_randomizer.runtime_plan import (
        RuntimeIntent,
        create_blocked_runtime_preview,
    )

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
        armed=False,
        metadata={"mock_only": True},
    )

    preview = create_blocked_runtime_preview(intent, "missing arming")

    assert preview.intent == intent
    assert preview.safety.mock_only is True
    assert preview.safety.sends_real_midi is False
    assert preview.safety.ports_allowed is False
    assert preview.safety.hardware_required is False
    assert preview.status == "blocked"
    assert preview.reason == "missing arming"
    assert preview.would_execute is False


def test_supported_group_profile_2_is_still_blocked():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "execution not implemented"
    assert preview.would_execute is False


def test_supported_group_profile_3_is_still_blocked():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="3",
        target="Pad 2 / My BD Classic",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "execution not implemented"
    assert preview.would_execute is False


def test_unknown_key_fails_safely():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="unknown",
        target="unknown",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "unsupported key"
    assert preview.would_execute is False


def test_profile_4_remains_parked():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="4",
        target="Pad 1 / My BD Acoustic",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "profile 4 parked"
    assert preview.would_execute is False


def test_unsupported_source_kind_fails_safely():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="scene",
        source_key="S1A",
        target="Rolling Light",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "unsupported source kind"
    assert preview.would_execute is False


def test_mock_runtime_provider_records_in_memory_only():
    from rytm_randomizer.runtime_plan import (
        MockRuntimeProvider,
        RuntimeIntent,
        create_blocked_runtime_preview,
    )

    provider = MockRuntimeProvider()
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
    )
    preview = create_blocked_runtime_preview(intent, "execution not implemented")

    assert provider.records == ()

    recorded = provider.record(preview)

    assert recorded == preview
    assert provider.records == (preview,)

    provider.clear()
    assert provider.records == ()


def test_runtime_plan_does_not_import_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.runtime_plan", None)
    importlib.import_module("rytm_randomizer.runtime_plan")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_runtime_plan_is_not_cli_execution_wiring():
    runtime_plan = importlib.import_module("rytm_randomizer.runtime_plan")

    exposed_names = set(dir(runtime_plan))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


if __name__ == "__main__":
    test_importing_runtime_plan_prints_nothing()
    test_runtime_safety_envelope_defaults_are_inert()
    test_runtime_intent_metadata_is_copied_and_immutable()
    test_create_blocked_runtime_preview_never_executes()
    test_supported_group_profile_2_is_still_blocked()
    test_supported_group_profile_3_is_still_blocked()
    test_unknown_key_fails_safely()
    test_profile_4_remains_parked()
    test_unsupported_source_kind_fails_safely()
    test_mock_runtime_provider_records_in_memory_only()
    test_runtime_plan_does_not_import_real_midi_libraries()
    test_runtime_plan_is_not_cli_execution_wiring()
