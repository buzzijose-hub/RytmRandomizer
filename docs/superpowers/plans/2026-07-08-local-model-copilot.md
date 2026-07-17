# Local Model Copilot Implementation Plan

> Status: in-flight

## Scope

Add one bundled, passive local model copilot feature covering docs/MIDI
assistance, natural-language mutation intent, and Analog Four patch co-design.

The optional model boundary must be local-only and executable-based: no HTTP
adapter, no host setting, no cloud service, no MIDI side effects.

## Architecture

- `rytm_randomizer/local_ai/provider.py`: DTOs, provider Protocol, validation
  helpers, and observability error taxonomy.
- `rytm_randomizer/local_ai/local_model.py`: subprocess-backed local executable
  provider. It reads `LOCAL_MODEL_COMMAND`, passes the prompt over stdin by
  default, supports `{model}` / `{prompt}` placeholders, and validates JSON
  stdout.
- `rytm_randomizer/local_ai/rag.py`: deterministic docs/MIDI source packets.
- `rytm_randomizer/local_ai/mutation_intent.py`: staged mutation-intent packets.
- `rytm_randomizer/style_analysis/analog_four_patch_codesigner.py`: A4
  patch-review packet compiler over the existing patch genome.
- `rytm_randomizer/reports/local_model_copilot.py`: passive report and
  `local-model-copilot-report` CLI command.

## Safety

- Default command output is deterministic packet metadata only.
- `--ask-local-model` is required before a local executable is launched.
- `LOCAL_MODEL_COMMAND` must be configured before the subprocess path can run.
- Model output is staged review metadata; it cannot open ports, send MIDI,
  write SysEx, mutate hardware, or promote a send plan.

## Checklist

- [x] Add local-AI DTO/provider/validation layer.
- [x] Add subprocess-backed local model provider; remove host/endpoint path.
- [x] Add docs/MIDI RAG packet compiler.
- [x] Add staged mutation-intent packet compiler.
- [x] Add A4 patch co-designer packet compiler over existing patch genome.
- [x] Add `local-model-copilot-report` text/JSON CLI command.
- [x] Update README, CLI reference, architecture docs/diagrams, STATUS, tests,
  and help fixtures.
- [ ] Commit, push, and update PR #209.

## Verification

```bash
python -m pytest tests/test_local_ai_provider.py tests/test_local_ai_rag.py tests/test_local_ai_mutation_intent.py tests/test_analog_four_patch_codesigner.py tests/test_local_model_copilot_report.py tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture tests/test_cli.py::test_lazy_help_text_entries_resolve_directly --cov=rytm_randomizer.local_ai --cov=rytm_randomizer.reports.local_model_copilot --cov=rytm_randomizer.style_analysis.analog_four_patch_codesigner --cov-branch --cov-report=term-missing:skip-covered -n 0 -q
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```
