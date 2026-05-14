from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.ps1"
CROSS_PLATFORM_CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.py"


def _script_text():
    return CLOSEOUT_SCRIPT.read_text()


def test_closeout_tracks_failed_python_test_steps():
    script = _script_text()

    assert "$script:closeoutFailures" in script
    assert "function Register-CloseoutStepExit" in script
    assert "Closeout failed. Failed step count:" in script
    assert "exit 1" in script


def test_every_python_test_step_registers_exit_status():
    lines = _script_text().splitlines()
    test_invocation_indexes = [
        index
        for index, line in enumerate(lines)
        if line.strip().startswith("& $pythonExe @pythonArgs .\\tests\\")
    ]

    assert test_invocation_indexes

    for index in test_invocation_indexes:
        following_lines = lines[index + 1 : index + 4]
        assert any(
            line.strip().startswith("Register-CloseoutStepExit")
            for line in following_lines
        ), lines[index]


def test_closeout_contract_test_is_included_in_closeout():
    script = _script_text()

    assert "=== Test: Closeout Contract ===" in script
    assert ".\\tests\\test_closeout_contract.py" in script


def test_project_status_check_is_included_in_closeout():
    script = _script_text()

    assert "=== Test: Project Status Check ===" in script
    assert "-m rytm_randomizer.cli project-status-report --check" in script
    assert 'Register-CloseoutStepExit "Project Status Check"' in script


def test_cross_platform_closeout_script_exists_and_runs_core_gates():
    script = CROSS_PLATFORM_CLOSEOUT_SCRIPT.read_text(encoding="utf-8")

    assert "RytmRandomizer Cross-Platform Closeout Summary" in script
    assert "python -m pytest" in script
    assert "--cov=rytm_randomizer" in script
    assert "--cov-fail-under=84" in script
    assert "project-status-report" in script
    assert "rytm_hybrid_randomizer_v134.py" in script
    assert "git status --short" in script
    assert "latest_cross_platform_closeout_summary.txt" in script


def test_docs_mention_cross_platform_closeout_script():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    contributing = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "python .\\Scripts\\closeout_check.py" in readme
    assert "python .\\Scripts\\closeout_check.py" in contributing


if __name__ == "__main__":
    test_closeout_tracks_failed_python_test_steps()
    test_every_python_test_step_registers_exit_status()
    test_closeout_contract_test_is_included_in_closeout()
    test_project_status_check_is_included_in_closeout()
    test_cross_platform_closeout_script_exists_and_runs_core_gates()
    test_docs_mention_cross_platform_closeout_script()
