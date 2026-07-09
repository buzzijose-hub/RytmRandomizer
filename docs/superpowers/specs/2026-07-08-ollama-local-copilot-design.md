# Ollama Local Copilot Design

## Goal

Build one bundled, passive Ollama integration for RytmRandomizer that supports three operator workflows:

- a local docs and MIDI knowledge assistant,
- natural-language to staged mutation intent,
- Analog Four patch DNA co-design.

The feature must not send MIDI, open MIDI devices, mutate hardware, write SysEx, or require any cloud service. Ollama calls are optional and explicit; deterministic prompt packets remain useful when Ollama is not installed.

## Architecture

The new surface lives under a new `rytm_randomizer/local_ai/` subpackage plus one passive report module:

- `local_ai/provider.py` defines frozen DTOs, a provider protocol, schema helpers, and validation errors.
- `local_ai/ollama.py` implements the Ollama HTTP adapter with stdlib `urllib`; it performs network I/O only when a caller explicitly invokes the adapter.
- `local_ai/rag.py` builds deterministic source packets for docs and MIDI catalog questions.
- `local_ai/mutation_intent.py` builds and validates staged mutation-intent packets from natural language.
- `style_analysis/analog_four_patch_codesigner.py` composes existing patch-genome output into passive co-designer prompts.
- `reports/ollama_local_copilot.py` exposes the operator report and passive CLI command.

No new top-level `.py` module is added. No `mido`, `rtmidi`, `real_midi_adapter`, `midi_io`, `shell`, or `app` imports are introduced.

## Data Flow

```text
operator question/description
  -> deterministic context builder
  -> JSON schema + prompt packet
  -> optional Ollama structured-output call
  -> strict local validator
  -> passive report payload
  -> staged recommendation only
```

For patch work:

```text
description/audio FeatureReport
  -> existing Analog Four patch genome
  -> local co-designer prompt packet
  -> optional Ollama structured suggestion
  -> strict validator
  -> passive report
```

## Safety

- Default command output is a readiness/prompt packet; it does not contact Ollama.
- `--ask-ollama` is required before local HTTP is attempted.
- Provider output is parsed as JSON and validated against small expected shapes.
- Mutation intent is advisory and includes blocked actions plus safety lines.
- Patch co-design emits candidate/rationale metadata only; it does not create a send plan or touch any armed path.
- The passive CLI safety sweep auto-enrolls the new command through `cli.py`'s lazy-command manifest.

## Ollama Behavior

The adapter targets Ollama's local HTTP API:

- `POST /api/chat` with `stream: false` and `format` set to a JSON schema.
- `POST /api/embed` for future semantic search support; the first PR exposes the adapter and validates response parsing.
- `OLLAMA_HOST` may override the default `http://localhost:11434`.

The code does not add the Ollama Python package. This keeps installation unchanged and avoids a new dependency for users who only want deterministic packets.

## CLI

One bundled command is added:

```text
python -m rytm_randomizer.cli ollama-local-copilot-report --question <text> [--description <text>] [--workflow docs|mutation|patch|all] [--model <name>] [--ask-ollama] [--json]
```

Default workflow is `all`. Without `--ask-ollama`, the report shows source chunks, schemas, prompt packets, safety boundaries, and staged outputs that can be pasted into a local Ollama session.

## Testing

Tests cover:

- provider request/response parsing with an injected transport,
- schema validation failures,
- docs/MIDI packet ranking,
- mutation-intent packet validation,
- patch co-designer composition over existing patch-genome builders,
- report text and JSON output,
- CLI parsing, help, bad-argument handling, and no-real-MIDI import behavior through the existing passive sweep.

## Scope Limits

This PR does not add a GUI panel, vector database, persistent index, autonomous hardware control, or any real MIDI send path. Those can build on the provider and packet contracts later.
