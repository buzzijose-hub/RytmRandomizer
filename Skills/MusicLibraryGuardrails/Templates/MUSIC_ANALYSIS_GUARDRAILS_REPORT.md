# Music Analysis to Mutation Guardrails Report

## Source
- Source name:
- Source type:
- Device target:
- Confidence:
- Date:

## Summary

## Style Tags
-

## Musical Findings

### Tempo / Groove

### Low-End Behavior

### Percussion Density

### Bass / Tonal Movement

### Texture / Noise

### FX / Space

### Arrangement / Energy Arc

## Rytm Role Mapping

| Pad | Role | Finding | Mutation Direction |
|---|---|---|---|
| Pad 1 | Kick / low-end foundation |  |  |
| Pad 2 | Snare / secondary percussion |  |  |
| Pad 3 | Bass / synth-percussion / SY Raw motion |  |  |
| Pad 4 | Body / impact / accent |  |  |

## Analog Four Role Mapping

| Track | Role | Finding | Mutation Direction |
|---|---|---|---|
| Track 1 | Mono bass / low synth |  |  |
| Track 2 | Stab / rhythmic synth |  |  |
| Track 3 | Pad / drone / chord pressure |  |  |
| Track 4 | FX / noise / tension |  |  |

## Live-Safe Guardrails

| Device | Pad/Track | Scope | Parameter Group | Range/Behavior | Notes |
|---|---|---|---|---|---|

## Studio-Discovery Guardrails

| Device | Pad/Track | Scope | Parameter Group | Range/Behavior | Notes |
|---|---|---|---|---|---|

## Locked by Default

| Parameter/Behavior | Reason |
|---|---|

## Forbidden

| Parameter/Behavior | Reason |
|---|---|

## Suggested Scene Behavior

| Scene | Risk | Device Behavior | Notes |
|---|---|---|---|

## Hardware Validation Tests

- Load known anchors.
- Apply live-safe mutation.
- Confirm low-end stability.
- Confirm no volume spike.
- Confirm anchor return works.
- Confirm no pattern, transport, or clock messages are sent.
- Confirm locked parameters remain untouched.
- Save useful results on hardware manually.

## Decision

Approved for:
- [ ] Documentation only
- [ ] Studio discovery
- [ ] Live-safe testing
- [ ] Code implementation
