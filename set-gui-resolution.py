#!/usr/bin/env python
"""change-resolution.py

A runcommand script for EmulationStation. Sets proper resolution for the
emulator.

Usage:

change-resolution.py SYSTEM EMULATOR ROM COMMAND_LINE
"""
from rgbpi.helpers import resolution

import sys
import logging
import os

DISPLAY_X_OFFSET = int(os.environ.get('RGBPI_X_OFFSET', '6'))
DISPLAY_Y_OFFSET = int(os.environ.get('RGBPI_Y_OFFSET', '6'))
"""Play with DISPLAY_Y_OFFSET and DISPLAY_X_OFFSET to be able to see the
   combo moves in Xenogears and other titles very much unaware of display
   safe zones
"""
# used only for some specific emulators
DISPLAY_H_SIZE = int(os.environ.get('RGBPI_H_SIZE', '-288'))
# used for most emulators. Good values in [-60;+60]
DISPLAY_H_ZOOM = int(os.environ.get('RGBPI_H_ZOOM', '100'))
"""this is the physical horizontal zoom factor for the image. Good to
   compensate overscan and shite (you may read RPG texts this way).

   Values beyond -60 and 60 are ignored.
"""

# careful: this is PAL|NTSC, not numbers
DISPLAY_FREQUENCY = str(os.environ.get('DISPLAY_FREQUENCY', 'NTSC'))
DISPLAY_TRINITRON_FIX = bool(os.environ.get('TRINITRON_FIX', False))


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def main(system, emu, rom, cmdline):
    logger.debug("System: %s Emu: %s ROM: %s\nCMDLINE: %s", system, emu, rom, cmdline)
    if DISPLAY_FREQUENCY == 'PAL':
        frequency = resolution.FREQ_PAL
    elif DISPLAY_FREQUENCY == 'NTSC':
        frequency = resolution.FREQ_NTSC
    else:
        raise RuntimeError("Unknown DISPLAY_FREQUENCY %s", DISPLAY_FREQUENCY)
    if system == 'arcade':
        pass
    else:
        logger.debug("Changing resolution...")
        resolution.set_gui_resolution(
            x_offset=DISPLAY_X_OFFSET,
            y_offset=DISPLAY_Y_OFFSET,
            h_size=DISPLAY_H_SIZE,
            h_zoom=DISPLAY_H_ZOOM,
            frequency=frequency,
            trinitron_fix=DISPLAY_TRINITRON_FIX)
        logger.debug("Done changing resolution.")

    return 0


if __name__ == '__main__':
    try:
        system, emu, rom, cmdline = sys.argv[1:]
        sys.exit(main(system, emu, rom, cmdline))
    except Exception as e:
        print(e)
        print(__doc__)
        sys.exit(1)


