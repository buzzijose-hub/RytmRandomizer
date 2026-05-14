"""Application entry points for the modular passive CLI.

The validated V1.34 script remains the hardware-tested runner. This scaffold
does not open MIDI ports or send MIDI.
"""


def main(argv=None):
    from rytm_randomizer.cli import main as cli_main

    return cli_main(argv)
