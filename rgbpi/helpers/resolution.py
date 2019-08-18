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
import logging

logger = logging.getLogger(__name__)

TIMINGS_FILE_DIR = os.environ.get('RGBPI_DATA_DIR', os.path.abspath('../data'))

TIMINGS_FILE_CONSOLE = '{}/{}'.format(TIMINGS_FILE_DIR, 'console-timings.cfg')
TIMINGS_FILES_ARCADE = {
    'advmame': '{}/{}'.format(TIMINGS_FILE_DIR, 'advmame-timings.cfg'),
    'lr-fba': '{}/{}'.format(TIMINGS_FILE_DIR, 'advmame-timings.cfg'),
    'lr-mame2003-plus': '{}/{}'.format(TIMINGS_FILE_DIR, 'advmame-timings.cfg'),
    'lr-mame2003': '{}/{}'.format(TIMINGS_FILE_DIR, 'advmame-timings.cfg'),
    'lr-mame2010': '{}/{}'.format(TIMINGS_FILE_DIR, 'advmame-timings.cfg'),
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


CRTINFO_CLI_FIX = CRTInfo(320, 10, 60, 13, 240, 5, 1, 9, 60, 6400000)
CRTINFO_CLI_STD = CRTInfo(320, 10, 30, 40, 240, 3, 4, 6, 60, 6400000)

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
    

def prepare_crtinfo_config(vi):
    """Take a VideoInfo, make it a CRT info"""
    # this is critical timing computations 
    # most display issues will come from this function being fucked with
    h_fp = vi.h_fp - vi.h_zoom * 4 - vi.h_pos * 4
    h_bp = vi.h_bp - vi.h_zoom * 4 + vi.h_pos * 4
    if h_fp < 0:
        h_fp = 0
    if h_bp < 0:
        h_bp = 0
    h_fp = max(vi.h_fp - 4 * (vi.h_zoom + vi.h_pos), 0)
    h_bp = max(vi.h_bp - 4 * (vi.h_zoom - vi.h_pos), 0)
    h_total = vi.h_res + vi.h_sync + h_fp + h_bp
    v_total = int(ceil(vi.h_freq / vi.r_rate))
    logger.debug("H_Freq: %s / R_Rate: %s -> V_Total: %s", vi.h_freq, vi.r_rate, v_total)
    horizontal = int(ceil(v_total * vi.r_rate))
    logger.debug("V_Total: %s R_Rate: %s -> Horizontal: %s", v_total, vi.r_rate, horizontal)                                                                          

    pixel_clock = horizontal * h_total
    logger.debug("Horizontal: %s H_Total: %s -> Pixel_Clock: %s", horizontal, h_total, pixel_clock)
    v_fp = int(floor(((v_total - vi.v_res) - vi.v_sync) /2))
    
    v_fp -= min(vi.v_pos, v_fp)

    logger.debug("V_Total: %s V_Res: %s V_Sync: %s V_Pos: %s -> V_FP: %s", v_total, vi.v_res, vi.v_sync, vi.v_pos, v_fp)
    v_bp = v_total - vi.v_res
    v_bp = v_bp - vi.v_sync
    v_bp = int(v_bp - v_fp)
    logger.debug("V_Total: %s V_Res: %s V_Sync: %s V_FP: %s -> V_BP: %s", v_total, vi.v_res, vi.v_sync, v_fp, v_bp)
    info = CRTInfo(
        h_res=vi.h_res, h_fp=h_fp, h_sync=vi.h_sync, h_bp=h_bp,
        v_res=vi.v_res, v_fp=v_fp, v_sync=vi.v_sync, v_bp=v_bp,
        r_rate=vi.r_rate, pixel_clock=pixel_clock)

    return info
    
def set_gui_resolution(x_offset=6, y_offset=3, h_size=-288, frequency=FREQ_NTSC, trinitron_fix=False):
    if trinitron_fix:
        crtinfo = CRTINFO_CLI_FIX
    else:
        crtinfo = CRTINFO_CLI_STD
    return apply_hdmi_timings(crtinfo)


def set_console_system_resolution(system, x_offset=6, y_offset=3,
                               h_size=-288, frequency=FREQ_NTSC, trinitron_fix=False):
    """Prepare a VideoInfo for a console using local preferences and
       the systems database
    """
    system_video = load_system_details(system, frequency)

    if system_video is None:
        raise RuntimeError("Missing timing infos for system {}".format(system))
    logger.debug("Base system video details for system %s/freq %s: %s)", system, frequency, str(system_video))
    if trinitron_fix:
        logger.debug("Applying Trinitron fixes")
        system_video = apply_trinitron_fix(system_video)
        logger.debug("New config: %s", system_video)
    logger.debug("Applying video offset")
    system_video = apply_video_offset(system_video, frequency,
                                        x_offset, y_offset, h_size)
    logger.debug("Video offset applied: %s", system_video)
    crtinfo = prepare_crtinfo_config(system_video)
    logger.debug("Final video settings: %s", str(system_video))
    logger.debug("CRT details: %s", str(crtinfo))
    return apply_hdmi_timings(crtinfo)


def set_arcade_system_resolution(emulator, game, x_offset=6,
                                     y_offset=3, h_size=-288,
                                     frequency=FREQ_NTSC, trinitron_fix=False,
                                     arcade_format=ARCADE_DISPLAY_FORCED):
    system_video = load_system_details_arcade(emulator, game)
    system_video = apply_arcade_core_video_tweaks(emulator, arcade_format,
                                                  system_video)
    system_video = apply_trinitron_fix(system_video)
    system_details = apply_video_offset(system_video, frequency,
                                        x_offset, y_offset, h_size,
                                        True, arcade_format)
    crtinfo = prepare_crtinfo_config(system_video)
    return apply_hdmi_timings(crtinfo)


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


def apply_video_offset(vi, frequency,
                       x_offset, y_offset, h_size,
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
    logger.debug("Computed h_pos: %s", new_h_pos)
    # manage v position
    if frequency == FREQ_NTSC:
        new_v_pos += y_offset
    elif frequency == FREQ_PAL:
        new_v_pos += y_offset + 4
    else:
        raise RuntimeError("Unhandled case: frequency == ".format(frequency))
    # manage zoom
    if vi.system in SPECIAL_RES_SYSTEMS:
        new_h_zoom += min(h_size / 16, 40)
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


__all__ = [
    'VideoInfo',
    'CRTInfo',
    'set_console_system_resolution',
    'set_arcade_system_resolution',
    'TIMINGS_FILE_CONSOLE',
    'TIMINGS_FILES_ARCADE',
    'HD_XFACTOR',
]

