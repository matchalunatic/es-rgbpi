#!/bin/bash
system=$1
emu=$2
rom=$3

# aspect_ratio_index = "23" is needed for custom display resolutions

cat >> /dev/shm/retroarch.cfg <<EOF
aspect_ratio_index = "23"
EOF

cat /opt/retropie/extras/es-rgbpi/data/rgbpi-retroarch-cfg/${system}-60.cfg >> /dev/shm/retroarch.cfg
