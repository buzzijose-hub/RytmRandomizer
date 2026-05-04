# RytmRandomizer — V1.34

## Current validated baseline

V1.33 is the fully validated expanded scene-depth layer. The combined V1.33 logs validated the Rolling, Deeper, Intense, and Wild A/B scene variants, clean anchor return, the main-prompt `1/2/3` guardrail, and clean script exit.

V1.34 is a documentation checkpoint. It does not introduce new musical behavior.

## Active script

```text
rytm_hybrid_randomizer_v134.py
```

## V1.34 focus

Documentation checkpoint / expanded scene layer complete.

This checkpoint locks in the validated scene system:

```text
S0  = Home / Clean anchors
S1  = Rolling
S1A = Rolling Light
S1B = Rolling Push
S2  = Deeper
S2A = Deeper Groove
S2B = Deeper Pressure
S3  = Intense
S3A = Intense Motion
S3B = Intense Grit
S4  = Wild
S4A = Wild Controlled
S4B = Wild Maximum
S5  = Back to Clean anchors
```

## Safety rules

- No new machine profiles were added.
- No new MIDI CC mappings were added.
- No new parameter ranges were added.
- No Pads 5–12 expansion yet.
- Main-prompt `1`, `2`, and `3` remain guarded and send no MIDI.
- Four-pad scene/global commands auto-load anchors if needed.

## Current four-lane layout

```text
Pad 1 = BD Hard / protected kick foundation
Pad 2 = BD Classic / secondary percussion lane
Pad 3 = SY Raw / bass + synth-percussion motion lane
Pad 4 = BD Acoustic / body + accent pressure lane
```

## Recommended quick validation flow

```text
SCN
GM
S1A
S3A
S3B
S4B
S5
1
Z
Q
```

Keep volume moderate for S3B and S4B.
