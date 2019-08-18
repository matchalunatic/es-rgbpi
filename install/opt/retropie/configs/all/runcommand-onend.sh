#!/bin/bash
HOOK_TYPE="emulator-end"
for _ in 1; do
THE_SYSTEM="$1"
THE_CORE="$2"
THE_ROM="$3"
THE_COMMAND="$4"
date

[ -f /home/pi/RGBPI_PARAMS ] && source /home/pi/RGBPI_PARAMS
printf "Hooks %s\nParameters:\n\tSystem: %s\n\tCore: %s\n\tROM: %s\n\t Command line: %s\n" "${HOOK_TYPE}" "${THE_SYSTEM}" "${THE_CORE}" "${THE_ROM}" "${THE_COMMAND}"

for hookie in /opt/retropie/hooks/${HOOK_TYPE}/*; do
    echo "Running hook ${hookie}"
    if [ -f "$hookie" -a -x "$hookie" ]; then
        "$hookie" "${THE_SYSTEM}" "${THE_CORE}" "${THE_ROM}" "${THE_COMMAND}"
    fi

    done
done | tee -a /tmp/runcommand.log
clear
