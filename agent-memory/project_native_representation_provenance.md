---
name: Native representation and source-kind boundaries
description: Distinct labels/native/wire values, replay-compatible presentation, and passive working-KIT restrictions.
metadata:
  type: project
---

A4 F1 and ordinary Rytm LFO Depth have separate verified representation
contracts under `data/` and `devices/strategies/`. Their helpers are not senders
or runtime evidence. Preserve native-fields-v1 sampling and stored label/reason
text; operator projections can change without rewriting replay records.

Working A4 0x58 frames can share the indexed 0x52 body hash, but raw provenance
and saved-state authority differ. Source adoption, retained import, saved
recapture and preflight must use the indexed raw-frame validator even for a
fully locked candidate. Protocol/storage versions do not identify firmware.

See `.claude/rules/native-representation-provenance.md`,
`docs/NATIVE_REPRESENTATION_INTEGRATION.md` and the six-file studio experiment.
