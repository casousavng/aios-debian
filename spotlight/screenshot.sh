#!/bin/bash
set -e
if [ "${1:-}" = "--delay" ]; then
    sleep 0.35
fi
mkdir -p "$HOME/Temp"
OUT="$HOME/Temp/captura.png"
DISPLAY="${DISPLAY:-:0}" scrot -o "$OUT"
printf "@Temp/captura.png " > /tmp/aios_attach.txt
pkill -USR1 -f "^python3 /opt/ai-os/spotlight/spotlight_ui.py" || true
