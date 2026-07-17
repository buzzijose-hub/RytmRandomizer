# Local Model Copilot Design

## Goal

Build one bundled, passive local model support surface for RytmRandomizer:

- docs/MIDI Q&A packets
- staged natural-language mutation-intent packets
- Analog Four patch co-design packets over the existing patch genome

The feature must not send MIDI, open MIDI devices, mutate hardware, write SysEx,
require cloud services, or talk to a model over HTTP.

## Local Model Boundary

`local_ai/local_model.py` supports local model execution by subprocess:

- `LOCAL_MODEL_COMMAND` points to a local executable command template.
- `{model}` is replaced with the requested model name when present.
- `{prompt}` is replaced with the full prompt when present.
- If `{prompt}` is absent, the prompt is passed through stdin.
- stdout must be exactly one JSON object.
- stderr/non-zero exit, timeout, missing executable, or invalid JSON is reported
  as local-AI error metadata; the report remains passive.

Examples of supported command shapes:

```text
LOCAL_MODEL_COMMAND="my-local-runner --model {model}"
LOCAL_MODEL_COMMAND="my-local-runner --model {model} --prompt {prompt}"
```

The project intentionally does not choose or vendor a model runner. Operators
can point the command at any locally installed runner that returns JSON stdout.

## Signal Flow

```text
question / description
  -> deterministic docs, mutation, and A4 patch packets
  -> optional local executable structured-output call
  -> schema validation
  -> staged report JSON/text
```

The output is never promoted to a MIDI send path. A4 patch co-design reuses
`style_analysis/analog_four_patch_genome.py` and returns staged review metadata
only.

## CLI

```bash
python -m rytm_randomizer.cli local-model-copilot-report --question <text> [--description <text>] [--workflow docs|mutation|patch|all] [--model <name>] [--ask-local-model] [--json]
```

Default workflow is `all`. Without `--ask-local-model`, the report shows source
chunks, schemas, prompt packets, safety boundaries, and staged outputs that can
be reviewed or manually pasted into a local model runner.

## Safety Invariants

- no HTTP client
- no host/URL configuration
- no model subprocess launch unless `--ask-local-model` is set
- no MIDI import
- no MIDI port open
- no MIDI send
- no SysEx write
- no hardware mutation
- no generated send plan promotion
