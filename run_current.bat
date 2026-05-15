@echo off
REM Launch RytmRandomizer in --arm mode (opens a real MIDI port and runs the
REM interactive command shell). Use --dry-run for a mock-sender session, or no
REM flag for the passive read-only menu.
python -m rytm_randomizer.app --arm %*
