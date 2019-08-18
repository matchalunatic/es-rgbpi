#!/bin/bash
system="${1:- }"
emu="${2:- }"
rom="${3:- }"
cmdline="${4:- }"
export RGBPI_DATA_DIR="/opt/retropie/extras/es-rgbpi/data"

cd /opt/retropie/extras/es-rgbpi
echo "Starting..."
python change-resolution.py "$system" "$emu" "$rom" "$cmdline"
echo "finished."

