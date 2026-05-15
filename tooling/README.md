# tooling/

Developer utilities that are *not* part of the shipped product. These scripts
are useful when working with real Analog Rytm MK2 hardware but are never
imported by `rytm_randomizer/`, by the tests, or by the monolith.

## capture_tools/

Interactive MIDI input recorders. They open a real input port (via `mido` /
`python-rtmidi`) and listen for CC streams from the hardware so a developer
can capture anchor / morph values when authoring new profiles. They require
real hardware to do anything useful and are run by hand:

```
python tooling/capture_tools/rytm_capture_bd_sharp_anchor_v02.py
```

Files:

- `rytm_capture_bd_sharp_anchor_v01.py` / `_v02.py` - BD Sharp anchor builder
  used while authoring the BD Sharp body/accent profile.
- `rytm_capture_generic_lfo_v01.py` - Generic LFO page parameter capture.
- `rytm_capture_syraw_morph_v01.py` - SY Raw morph capture used while
  authoring the SY Raw profile transitions.

These are historical capture sessions kept because a developer adding a new
profile may want to reuse the same listening loop.
