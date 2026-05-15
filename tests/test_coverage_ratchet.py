import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_RATCHET_PATH = PROJECT_ROOT / "scripts" / "coverage_ratchet.py"


def _load_coverage_ratchet():
    spec = importlib.util.spec_from_file_location(
        "coverage_ratchet_under_test", COVERAGE_RATCHET_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_coverage_ratchet_uses_same_total_coverage_metric_as_coverage_py(
    tmp_path, monkeypatch, capsys
):
    coverage_ratchet = _load_coverage_ratchet()
    coveragerc = tmp_path / ".coveragerc"
    coveragerc.write_text("[report]\nfail_under = 86\n", encoding="utf-8")
    coverage_xml = tmp_path / "coverage.xml"
    coverage_xml.write_text(
        (
            '<coverage lines-valid="100" lines-covered="88" '
            'line-rate="0.8800" branches-valid="100" branches-covered="84" '
            'branch-rate="0.8400"></coverage>'
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(coverage_ratchet, "COVERAGERC", coveragerc)

    result = coverage_ratchet.main(["coverage_ratchet.py", str(coverage_xml)])

    captured = capsys.readouterr()
    assert result == 0
    assert "measured total coverage 86.00%" in captured.out
    assert coveragerc.read_text(encoding="utf-8") == "[report]\nfail_under = 86\n"
