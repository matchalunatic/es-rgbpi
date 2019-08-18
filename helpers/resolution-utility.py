#!/usr/bin/env python
"""Set proper framebuffer for a given console set

Made to work with RGB-Pi cable.

Compatible with Python 2.7 (because Retropie :'( )


"""
import os.path
from collections import namedtuple
from math import ceil, floor
import shlex
import time
import subprocess

TIMINGS_FILE_CONSOLE=os.path.abspath('../data/console-timings.cfg')
TIMINGS_FILES_ARCADE = {
    'advmame': os.path.abspath('../data/advmame-timings.cfg'),
    'lr-fba': os.path.abspath('../data/lr-fba-timings.cfg'),
    'lr-mame2003-plus': os.path.abspath('../data/lr-mame2003-plus-timings.cfg'),
    'lr-mame2003': os.path.abspath('../data/lr-mame2003-timings.cfg'),
    'lr-mame2010': os.path.abspath('../data/lr-mame2010-timings.cfg'),
}

HD_XFACTOR = 6

SPECIAL_RES_SYSTEMS = 'atarist scummvm pc videoplayer advmame'.split()

VideoInfo = namedtuple('VideoInfo', (
                                  'system h_res v_res r_rate h_pos '
                                  'h_zoom v_pos h_fp h_sync '
                                  'h_bp v_sync h_freq orientation').split())


CRTInfo = namedtuple('CRTInfo', (
                                'h_res h_fp h_sync h_bp '
                                'v_res v_fp v_sync v_bp ' 
                                'r_rate pixel_clock').split())

FREQ_PAL = 50.0
FREQ_NTSC = 60.0

ARCADE_DISPLAY_CROPPED = 'cropped'
ARCADE_DISPLAY_FORCED = 'forced'

def apply_hdmi_timings(crt_info):
    """Take a CRTInfo and apply its settings"""
    COMMAND = ('vcgencmd hdmi_timings {item.h_res} 1 '
              '{item.h_fp} {item.h_sync} {item.h_bp} {item.v_res} 1 '
              '{item.v_fp} {item.v_sync} {item.v_bp} 0 0 0 '
              '{item.r_rate} 0 {item.pixel_clock} 1').format(item=crt_info)
    com_toks = shlex.split(COMMAND)
    print("Running command: {}".format(COMMAND))
    out = subprocess.call(com_toks) == 0
    time.sleep(0.5)
    for i in (8, 24, 32):
        subprocess.call(['fbset', '-depth', str(i)])
    return out
    

def change_scart_resolution(vi):
    """Take a VideoInfo and make it into a CRTInfo"""
    # this is critical timing computations 
    h_fp = max(vi.h_fp - 4 * (vi.h_zoom + vi.h_pos), 0)
    h_bp = max(vi.h_bp - 4 * (vi.h_zoom - vi.h_pos), 0)
    h_total = vi.h_res + h_fp + vi.h_sync + vi.h_bp
    v_total = int(ceil(vi.h_freq / vi.r_rate))
    horizontal = int(ceil(v_total * vi.r_rate))
    pixel_clock = horizontal * h_total
    v_fp = int(floor(v_total - vi.v_res - vi.v_sync / 2))
    v_pos = min(vi.v_pos, v_fp)
    v_fp -= v_pos
    v_bp = v_total - vi.v_res - vi.v_sync
    v_bp = int(v_bp - v_fp)
    info = CRTInfo(
        h_res=vi.h_res, h_fp=h_fp, h_sync=vi.h_sync, h_bp=h_bp,
        v_res=vi.v_res, v_fp=v_fp, v_sync=vi.v_sync, v_bp=v_bp,
        r_rate=vi.r_rate, pixel_clock=pixel_clock)
    return apply_hdmi_timings(info)
    


def prepare_console_system_resolution(system, x_offset=0, y_offset=0,
                               h_size=320, frequency=FREQ_NTSC, trinitron_fix=False):
    """Prepare a VideoInfo for a console using local preferences and
       the systems database
    """
    system_video = load_system_details(system, frequency)

    if system_video is None:
        raise RuntimeError("Missing timing infos for system {}".format(system))
    if trinitron_fix:
        system_video = apply_trinitron_fix(system_video)
    system_details = apply_video_offset(system_video, frequency,
                                        x_offset, y_offset, h_size)
    change_scart_resolution(system_video)


def prepare_arcade_system_resolution(emulator, game, x_offset=0,
                                     y_offset=0, h_size=320,
                                     frequency=FREQ_NTSC, trinitron_fix=False,
                                     arcade_format=ARCADE_DISPLAY_FORCED):
    system_video = load_system_details_arcade(emulator, game)
    system_video = apply_arcade_core_video_tweaks(emulator, arcade_format,
                                                  system_video)
    system_video = apply_trinitron_fix(system_video)
    # todo: support screen rotation
    system_details = apply_video_offset(system_video, frequency,
                                        x_offset, y_offset, h_size,
                                        True, arcade_format)
    change_scart_resolution(system_video)


def apply_arcade_core_video_tweaks(arcade_format, vi):
    new_v_pos = vi.v_pos
    new_v_sync = vi.v_sync
    new_h_freq = vi.h_freq
    new_h_pos = vi.h_pos
    if vi.system in ('advmame', 'lr-fba'):
        new_v_pos -= 2
    if vi.v_res > 240:
        if arcade_format == ARCADE_DISPLAY_FORCED:
            new_v_pos += (vi.v_res - 240) / 2 + 6
            new_h_freq = 15840
        elif arcade_format == ARCADE_DISPLAY_CROPPED:
            if vi.r_rate < 55:
                new_v_pos -= (vi.v_res - 240) / 2 + 6
                new_h_freq = 15095
            else:
                new_v_pos -= 11
    elif vi.v_res == 240:
        if vi.r_rate < 60 and vi.orientation != 'V':
            new_v_pos -= 6

    return vi._replace(
        v_pos=new_v_pos,
        v_sync=new_v_sync,
        h_freq=new_h_freq,
        h_pos=new_h_pos
        )
    
    

def apply_trinitron_fix(vi):
    """not sure about this fix / need to check its relevance"""
    new_v_sync = 4
    new_h_sync = 100
    new_h_zoom = vi.h_zoom
    if vi.v_res < 240:
        if vi.r_rate >= 59.9 and vi.r_rate <= 60.0:
            new_h_sync = 100
        else:
            new_h_sync = 50
    if vi.system in SPECIAL_RES_SYSTEMS:
        new_h_zoom = vi.h_zoom - 10
    return vi._replace(h_sync=new_h_sync,
                       h_zoom=new_h_zoom,
                       v_pos=vi.v_pos+1,
                       v_sync=new_v_sync)


def apply_video_offset(vi, frequency=FREQ_NTSC,
                       x_offset=0, y_offset=0, h_size=320,
                       arcade=False, arcade_format=ARCADE_DISPLAY_FORCED):
    """Transform the display settings in order to account for preferred offset
       and zoom
    """
    new_h_pos = vi.h_pos
    new_v_pos = vi.v_pos
    new_h_zoom = vi.h_zoom

    # manage h position
    if vi.system in SPECIAL_RES_SYSTEMS:
        new_h_pos += x_offset / HD_XFACTOR + 4
    elif frequency == FREQ_NTSC:
        new_h_pos += x_offset / HD_XFACTOR - 2
    elif frequency == FREQ_PAL:
        new_h_pos += x_offset / HD_XFACTOR - 8
    else:
        raise RuntimeError("Unhandled case: frequency == ".format(frequency))
    # manage v position
    if frequency == FREQ_NTSC:
        new_v_pos += y_offset
    elif frequency == FREQ_PAL:
        new_v_pos += y_offset + 4
    else:
        raise RuntimeError("Unhandled case: frequency == ".format(frequency))
    # manage zoom
    if vi.system in SPECIAL_RES_SYSTEMS:
        new_h_zoom += max(h_size / 16, 40)
    return vi._replace(
        h_pos=new_h_pos,
        v_pos=new_v_pos,
        h_zoom=new_h_zoom)


def load_system_details(system, frequency=FREQ_NTSC, times=TIMINGS_FILE_CONSOLE):
    """Load and standardize data from the systems timing database (console)"""
    freq_int = int(frequency)
    systemfreq = '{}{}'.format(system, freq_int)
    searched = None
    with open(times, 'r') as fh:
        for line in fh:
            if line.strip().startswith(';'):
                continue
            tokens = line.split(' ')
            system_name = tokens[0]
            if system_name in (system, systemfreq):
                searched = tokens
                break
    if searched is None:
        raise RuntimeError("Cannot find system details for {}".format(system))
    tokies = ([system_name] + 
              [int(a) for a in searched[1:3]] +
              [float(searched[3])] +
              [int(a) for a in searched[4:]])
    # orientation is hardcoded as horizontal for consoles
    tokies += ['H']
    return VideoInfo(*tokies)
    return None


def load_system_details_arcade(arcade_emu, game):
    if arcade_emu not in TIMINGS_FILES_ARCADE:
        raise RuntimeError(("Unsupported arcade_emu: "
                           "no timings: {}").format(arcade_emu))
    searched = None
    with open(TIMINGS_FILES_ARCADE[arcade_emu], 'r') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith(';'):
                continue
            tokens = line.split(' ')
            if line[0] in (game_name, 'default'):
                searched = tokens
                break
    if searched is None:
        raise RuntimeError((
                           "Arcade game {g} not found for emu {e} and no "
                           "defaults are set").format(g=game, arcade_emu=e))
#    tokies = [str(arcade_emu)] + [int(a) for a in searched[1:13]] + [str(searched[13])]
    tokies = ([str(arcade_emu)] + 
              [int(a) for a in searched[1:3]] +
              [float(searched[3])] +
              [int(a) for a in searched[4:13]] +
              [str(searched[13])])
    # refresh rate is a float
#    tokies[3] = float(searched[3])
    return VideoInfo(*tokies)


if __name__ == '__main__':
    import sys
    print("Usage: resolution-utility.py [arcade|console] x_off y_off h_zoom [trinitron_fix|no_trinitron_fix] [pal|ntsc] <game>")
    sys.exit(0)
    print("seriously, don't use this crappy CLI, this is an ugly test")
    arcade = sys.argv[1] == 'arcade'
    x_offset, y_offset, h_zoom = (int(a) for a in sys.argv[2:5])
    trinitron_fix = sys.argv[5] == 'trinitron_fix'
    is_ntsc = sys.argv[6] == 'ntsc'
    if is_ntsc:
        frequency = FREQ_NTSC
    else:
        frequency = FREQ_PAL
    if arcade:
        emulator, game = sys.argv[7:]
        prepare_arcade_system_resolution(emulator, game, x_offset,
                                     y_offset, h_zoom,
                                     frequency, trinitron_fix,
                                     ARCADE_DISPLAY_FORCED)
    else:
        console = sys.argv[7]
        prepare_console_system_resolution(console, x_offset, y_offset,
                               h_zoom, frequency, trinitron_fix)
