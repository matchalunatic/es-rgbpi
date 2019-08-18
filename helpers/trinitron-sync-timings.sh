#!/bin/bash
# Set a basic trinitron fixed mode for displaying a console or other basic
# things

MODE=${1:-off}

# Trinitron sets can be very picky about their sync rates and
# 

if [ "$MODE" = "off" ]; then
    vcgencmd hdmi_timings 1920 1 48 192 240 240 1 9 5 9 0 0 0 60.0 0 37872000 1
else
    vcgencmd hdmi_timings 1920 1 48 100 240 240 1 9 4 9 0 0 0 60.0 0 36420240 1
fi

fbset -g 1920 240 1920 240 32
