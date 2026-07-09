# Ollama Local Copilot Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one bundled, passive Ollama local-copilot feature covering docs/MIDI assistance, natural-language mutation intent, and Analog Four patch co-design.

**Architecture:** New generic local-AI code lives under `rytm_randomizer/local_ai/`; Analog Four co-design reuses the existing `style_analysis` patch-genome layer; one report module exposes the passive CLI command. Ollama network I/O is optional and explicit via `--ask-ollama`.

**Tech Stack:** Python stdlib (`http.client`, `urllib.parse`, `json`, dataclasses, protocols), existing `style_analysis` and `reports` patterns, no new third-party dependency, no MIDI imports.

---

## File Structure

- Create `rytm_randomizer/local_ai/__init__.py`: package docstring and public exports.
- Create `rytm_randomizer/local_ai/provider.py`: provider protocol, DTOs, schema constants, JSON validation helpers.
- Create `rytm_randomizer/local_ai/ollama.py`: stdlib Ollama HTTP provider.
- Create `rytm_randomizer/local_ai/rag.py`: deterministic docs/MIDI context packet builder.
- Create `rytm_randomizer/local_ai/mutation_intent.py`: staged natural-language mutation-intent packet builder and validator.
- Create `rytm_randomizer/style_analysis/analog_four_patch_codesigner.py`: passive co-designer packet over existing patch-genome output.
- Create `rytm_randomizer/reports/ollama_local_copilot.py`: report text/JSON formatter and `CliCommand`.
- Modify `rytm_randomizer/cli.py`: add lazy-command manifest entry.
- Modify `rytm_randomizer/help_text.py`: expose command in usage/help.
- Modify `docs/ARCHITECTURE.md`: document passive local-AI subpackage.
- Create `tests/test_local_ai_provider.py`.
- Create `tests/test_local_ai_rag.py`.
- Create `tests/test_local_ai_mutation_intent.py`.
- Create `tests/test_analog_four_patch_codesigner.py`.
- Create `tests/test_ollama_local_copilot_report.py`.

## Tasks

- [x] Write failing provider tests for chat JSON, embeddings, unavailable service, and schema validation.
- [x] Implement `local_ai/provider.py` and `local_ai/ollama.py` until provider tests pass.
- [x] Write failing RAG packet tests for ranked docs/MIDI source chunks and JSON payload shape.
- [x] Implement `local_ai/rag.py` until RAG tests pass.
- [x] Write failing mutation-intent tests for safe staged intents, blocked actions, and validator rejection.
- [x] Implement `local_ai/mutation_intent.py` until mutation-intent tests pass.
- [x] Write failing patch co-designer tests over an existing `FeatureReport`.
- [x] Implement `style_analysis/analog_four_patch_codesigner.py` until co-designer tests pass.
- [x] Write failing report/CLI tests for text, JSON, `--ask-ollama` with injected provider, bad args, and import silence.
- [x] Implement `reports/ollama_local_copilot.py`, wire `cli.py`, and update `help_text.py`.
- [x] Update architecture/docs for the passive local-AI layer.
- [x] Run focused tests, fast tests, architecture tests, lint trio, and full pytest.
- [ ] Commit, push `codex/ollama-local-copilot`, open one PR against `modularize-v1.34`, and include the 18-gate checklist.

## Verification Commands

```bash
python -m pytest tests/test_local_ai_provider.py tests/test_local_ai_rag.py tests/test_local_ai_mutation_intent.py tests/test_analog_four_patch_codesigner.py tests/test_ollama_local_copilot_report.py -n 0
python -m pytest -m fast
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest
```

## Rollback

Reverting the PR removes the new `local_ai` package, one report module, one style-analysis compiler, help/CLI manifest entries, and docs. No V1.34 parity fixtures or armed hardware paths are touched.
