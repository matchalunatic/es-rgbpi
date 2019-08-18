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


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, filename="/tmp/rgbpi-resolution.log")

def main(system, emu, rom, cmdline):
    logger.debug("System: %s Emu: %s ROM: %s\nCMDLINE: %s", system, emu, rom, cmdline)
    if system == 'arcade':
        pass
    else:
        logger.debug("Changing resolution...")
        resolution.set_console_system_resolution(system=system, trinitron_fix=True)
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


