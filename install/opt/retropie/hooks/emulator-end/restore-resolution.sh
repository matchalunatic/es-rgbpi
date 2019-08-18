#!/bin/bash
export RGBPI_DATA_DIR="/opt/retropie/extras/es-rgbpi/data"

cd /opt/retropie/extras/es-rgbpi
echo "Starting..."
python set-gui-resolution.py "$1" "$2" "$3" "$4"
echo "finished."

