---
name: Analog Rytm SysEx project
description: User's goals and constraints for the AR MK2 SysEx generation project
type: project
originSessionId: f8ef60ca-d2ae-427a-84cc-cc526b5a31cb
---
User is building an AI-driven Analog Rytm MK2 SysEx generator on Windows.

**Scope decisions (from brainstorm):**
- Long-term wants all three modes: patch library generator, live sound design copilot, kit-aware generator
- **Start with kit-first generation** as the v0.1 surface — single command produces a cohesive 12-track kit `.syx`, not individual sounds
- Must work **offline** (no hosted dependencies beyond the Claude LLM call itself); no ElevenLabs / Replicate / Stable Audio in the loop
- SysEx files are the portable artifact; user loads them onto the device manually via Transfer/C6/MIDI-OX. No live MIDI bridge in v0.1.

**Why kit-first instead of single-sound-first:** User thinks in terms of cohesive kits (a kit for a track / genre), not individual patches. Generating one sound at a time would require N command invocations to build something useful; one-shot kit generation matches the actual workflow.

**How to apply:** When designing the rytm-mcp server, the primary tool is `rytm_generate_kit(description) → .syx`, not `rytm_generate_sound`. Single-sound generation is a *layer* underneath kit generation, exposed for power users but not the main UX. Live MIDI bridge is explicitly deferred to v0.2+.
