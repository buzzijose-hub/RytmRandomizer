"""Tests for rytm_randomizer.reports.formatter (PassiveReportFormatter).

All tests in this file are FAILING (RED phase) because the module
``rytm_randomizer/reports/formatter.py`` does not exist yet.

Naming convention: test_<unit>_<behavior>_when_<condition>
"""

from __future__ import annotations

import dataclasses
import sys
import types

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Helper: import target (must fail until formatter.py exists)
# ---------------------------------------------------------------------------


def _import_formatter() -> types.ModuleType:
    import importlib

    return importlib.import_module("rytm_randomizer.reports.formatter")


# ---------------------------------------------------------------------------
# 1. Module public surface — __all__
# ---------------------------------------------------------------------------


class TestModuleSurface:
    """The formatter module exports a well-defined public surface via __all__."""

    def test_module_surface_all_contains_PassiveReportHeader(self) -> None:
        mod = _import_formatter()
        assert "PassiveReportHeader" in mod.__all__

    def test_module_surface_all_contains_SAFETY_SECTION_HEADER(self) -> None:
        mod = _import_formatter()
        assert "SAFETY_SECTION_HEADER" in mod.__all__

    def test_module_surface_all_contains_PASSIVE_FOOTER_SOURCE_TEMPLATE(self) -> None:
        mod = _import_formatter()
        assert "PASSIVE_FOOTER_SOURCE_TEMPLATE" in mod.__all__

    def test_module_surface_all_contains_PASSIVE_FOOTER_MEMORY_LINE(self) -> None:
        mod = _import_formatter()
        assert "PASSIVE_FOOTER_MEMORY_LINE" in mod.__all__

    def test_module_surface_all_contains_PASSIVE_FOOTER(self) -> None:
        mod = _import_formatter()
        assert "PASSIVE_FOOTER" in mod.__all__

    def test_module_surface_all_contains_safety_section_lines(self) -> None:
        mod = _import_formatter()
        assert "safety_section_lines" in mod.__all__

    def test_module_surface_all_contains_passive_footer_lines(self) -> None:
        mod = _import_formatter()
        assert "passive_footer_lines" in mod.__all__

    def test_module_surface_all_contains_render_passive_report(self) -> None:
        mod = _import_formatter()
        assert "render_passive_report" in mod.__all__

    def test_module_surface_all_contains_passive_report_lines(self) -> None:
        mod = _import_formatter()
        assert "passive_report_lines" in mod.__all__


# ---------------------------------------------------------------------------
# 2. Constants — canonical literal values and types
# ---------------------------------------------------------------------------


class TestConstants:
    """Module-level constants must match the exact canonical literals."""

    def test_SAFETY_SECTION_HEADER_exact_value(self) -> None:
        mod = _import_formatter()
        assert mod.SAFETY_SECTION_HEADER == "Safety:"

    def test_PASSIVE_FOOTER_SOURCE_TEMPLATE_formats_registry(self) -> None:
        mod = _import_formatter()
        result = mod.PASSIVE_FOOTER_SOURCE_TEMPLATE.format(module="registry")
        assert result == "Source: rytm_randomizer.registry"

    def test_PASSIVE_FOOTER_SOURCE_TEMPLATE_formats_arbitrary_module(self) -> None:
        mod = _import_formatter()
        result = mod.PASSIVE_FOOTER_SOURCE_TEMPLATE.format(module="state.anchor")
        assert result == "Source: rytm_randomizer.state.anchor"

    def test_PASSIVE_FOOTER_MEMORY_LINE_exact_value(self) -> None:
        mod = _import_formatter()
        assert mod.PASSIVE_FOOTER_MEMORY_LINE == "In-memory only: True"

    def test_PASSIVE_FOOTER_is_tuple(self) -> None:
        mod = _import_formatter()
        assert isinstance(mod.PASSIVE_FOOTER, tuple)

    def test_PASSIVE_FOOTER_is_immutable_two_element_tuple(self) -> None:
        mod = _import_formatter()
        footer = mod.PASSIVE_FOOTER
        assert len(footer) == 2

    def test_PASSIVE_FOOTER_first_element_is_template(self) -> None:
        mod = _import_formatter()
        assert mod.PASSIVE_FOOTER[0] == mod.PASSIVE_FOOTER_SOURCE_TEMPLATE

    def test_PASSIVE_FOOTER_second_element_is_memory_line(self) -> None:
        mod = _import_formatter()
        assert mod.PASSIVE_FOOTER[1] == mod.PASSIVE_FOOTER_MEMORY_LINE

    def test_PASSIVE_FOOTER_cannot_be_mutated(self) -> None:
        mod = _import_formatter()
        with pytest.raises(TypeError):
            mod.PASSIVE_FOOTER[0] = "mutated"  # type: ignore[index]


# ---------------------------------------------------------------------------
# 3. PassiveReportHeader — frozen dataclass
# ---------------------------------------------------------------------------


class TestPassiveReportHeader:
    """PassiveReportHeader must be a frozen dataclass."""

    def test_PassiveReportHeader_is_dataclass(self) -> None:
        mod = _import_formatter()
        assert dataclasses.is_dataclass(mod.PassiveReportHeader)

    def test_PassiveReportHeader_is_frozen(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="My Report")
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            header.title = "changed"  # type: ignore[misc]

    def test_PassiveReportHeader_title_required(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="Test Title")
        assert header.title == "Test Title"

    def test_PassiveReportHeader_source_module_defaults_to_None(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="T")
        assert header.source_module is None

    def test_PassiveReportHeader_include_memory_line_defaults_to_True(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="T")
        assert header.include_memory_line is True

    def test_PassiveReportHeader_accepts_all_fields(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(
            title="Full Report",
            source_module="registry",
            include_memory_line=False,
        )
        assert header.title == "Full Report"
        assert header.source_module == "registry"
        assert header.include_memory_line is False

    def test_PassiveReportHeader_without_title_raises_TypeError(self) -> None:
        mod = _import_formatter()
        with pytest.raises(TypeError):
            mod.PassiveReportHeader()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# 4. safety_section_lines
# ---------------------------------------------------------------------------


class TestSafetySectionLines:
    """safety_section_lines returns 'Safety:' header + sorted items."""

    def test_safety_section_lines_empty_dict_returns_header_only(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({})
        assert result == ["Safety:"]

    def test_safety_section_lines_single_item(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({"read_only": True})
        assert result == ["Safety:", "- read_only: True"]

    def test_safety_section_lines_header_is_first(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({"a": 1, "b": 2})
        assert result[0] == "Safety:"

    def test_safety_section_lines_items_formatted_as_dash_key_value(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({"sends_midi": False})
        assert "- sends_midi: False" in result

    def test_safety_section_lines_preserves_insertion_order(self) -> None:
        """Items must preserve insertion order (dict is ordered in Python 3.7+)."""
        mod = _import_formatter()
        safety = {
            "read_only": True,
            "active_behavior": False,
            "hardware_required": False,
        }
        result = mod.safety_section_lines(safety)
        assert result == [
            "Safety:",
            "- read_only: True",
            "- active_behavior: False",
            "- hardware_required: False",
        ]

    def test_safety_section_lines_multiple_types_of_values(self) -> None:
        mod = _import_formatter()
        safety = {"count": 0, "label": "none", "flag": True}
        result = mod.safety_section_lines(safety)
        assert "- count: 0" in result
        assert "- label: none" in result
        assert "- flag: True" in result

    def test_safety_section_lines_returns_list(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({})
        assert isinstance(result, list)

    def test_safety_section_lines_special_characters_in_value(self) -> None:
        mod = _import_formatter()
        result = mod.safety_section_lines({"key": "val/ue: x"})
        assert "- key: val/ue: x" in result


# ---------------------------------------------------------------------------
# 5. passive_footer_lines
# ---------------------------------------------------------------------------


class TestPassiveFooterLines:
    """passive_footer_lines builds the trailing Source/In-memory pair."""

    def test_passive_footer_lines_with_memory_line(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry", include_memory_line=True)
        assert result == [
            "Source: rytm_randomizer.registry",
            "In-memory only: True",
        ]

    def test_passive_footer_lines_without_memory_line(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry", include_memory_line=False)
        assert result == ["Source: rytm_randomizer.registry"]

    def test_passive_footer_lines_default_includes_memory_line(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry")
        assert "In-memory only: True" in result

    def test_passive_footer_lines_source_uses_module_name(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("state.anchor")
        assert "Source: rytm_randomizer.state.anchor" in result

    def test_passive_footer_lines_returns_list(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry")
        assert isinstance(result, list)

    def test_passive_footer_lines_length_with_memory_true(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry", include_memory_line=True)
        assert len(result) == 2

    def test_passive_footer_lines_length_without_memory_line(self) -> None:
        mod = _import_formatter()
        result = mod.passive_footer_lines("registry", include_memory_line=False)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# 6. render_passive_report + passive_report_lines round-trip
# ---------------------------------------------------------------------------


class TestRenderPassiveReport:
    """render_passive_report and passive_report_lines must round-trip."""

    def _make_header(self, mod: types.ModuleType, **kwargs: object) -> object:
        return mod.PassiveReportHeader(title="Test Report", **kwargs)

    def test_passive_report_lines_starts_with_title(self) -> None:
        mod = _import_formatter()
        header = self._make_header(mod)
        result = mod.passive_report_lines(header, ["line A", "line B"])
        assert result[0] == "Test Report"

    def test_passive_report_lines_body_lines_included(self) -> None:
        mod = _import_formatter()
        header = self._make_header(mod)
        result = mod.passive_report_lines(header, ["alpha", "beta"])
        assert "alpha" in result
        assert "beta" in result

    def test_passive_report_lines_returns_list(self) -> None:
        mod = _import_formatter()
        header = self._make_header(mod)
        result = mod.passive_report_lines(header, [])
        assert isinstance(result, list)

    def test_passive_report_lines_empty_body(self) -> None:
        mod = _import_formatter()
        header = self._make_header(mod)
        result = mod.passive_report_lines(header, [])
        assert result[0] == "Test Report"
        assert len(result) >= 1

    def test_passive_report_lines_with_source_module_appends_footer(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(
            title="Report", source_module="registry", include_memory_line=True
        )
        result = mod.passive_report_lines(header, [])
        assert "Source: rytm_randomizer.registry" in result
        assert "In-memory only: True" in result

    def test_passive_report_lines_no_source_module_no_footer(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="Report", source_module=None)
        result = mod.passive_report_lines(header, ["body"])
        assert all("Source:" not in line for line in result)

    def test_passive_report_lines_source_module_without_memory_line(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(
            title="Report",
            source_module="registry",
            include_memory_line=False,
        )
        result = mod.passive_report_lines(header, [])
        assert "Source: rytm_randomizer.registry" in result
        assert "In-memory only: True" not in result

    def test_render_passive_report_returns_newline_joined_string(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="Title")
        result = mod.render_passive_report(header, ["line1", "line2"])
        assert isinstance(result, str)
        assert "\n" in result

    def test_render_passive_report_matches_passive_report_lines_joined(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(
            title="Title", source_module="registry", include_memory_line=True
        )
        body = ["body line"]
        lines = mod.passive_report_lines(header, body)
        rendered = mod.render_passive_report(header, body)
        assert rendered == "\n".join(lines)

    def test_render_passive_report_empty_body_still_has_title(self) -> None:
        mod = _import_formatter()
        header = mod.PassiveReportHeader(title="My Title")
        result = mod.render_passive_report(header, [])
        assert result.startswith("My Title")

    def test_passive_report_lines_body_order_preserved(self) -> None:
        mod = _import_formatter()
        header = self._make_header(mod)
        body = ["first", "second", "third"]
        result = mod.passive_report_lines(header, body)
        body_start = result.index("first")
        assert result[body_start : body_start + 3] == ["first", "second", "third"]


# ---------------------------------------------------------------------------
# 7. Import safety — no mido/rtmidi; no _logger at module level
# ---------------------------------------------------------------------------


class TestImportSafety:
    """formatter.py must not pull in MIDI libs or attach a module-level logger."""

    def test_import_safety_mido_not_imported_by_formatter(self) -> None:
        # Remove formatter from cache to force fresh import analysis
        sys.modules.pop("rytm_randomizer.reports.formatter", None)
        before = set(sys.modules)
        _import_formatter()
        after = set(sys.modules)
        new_modules = after - before
        assert "mido" not in new_modules, f"mido was pulled in: {new_modules}"

    def test_import_safety_rtmidi_not_imported_by_formatter(self) -> None:
        sys.modules.pop("rytm_randomizer.reports.formatter", None)
        before = set(sys.modules)
        _import_formatter()
        after = set(sys.modules)
        new_modules = after - before
        assert "rtmidi" not in new_modules, f"rtmidi was pulled in: {new_modules}"

    def test_import_safety_no_logger_at_module_level(self) -> None:
        """Gate 7 carve-out: pure text rendering module must NOT attach _logger."""
        mod = _import_formatter()
        assert not hasattr(mod, "_logger"), (
            "formatter.py attached _logger at module level; "
            "Gate 7 carve-out requires pure-text modules to be logger-free"
        )
