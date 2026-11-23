#!/bin/bash
IMG="$HOME/.ai-os/wallpaper.png"
if [ -f "$IMG" ]; then
    exec i3lock -i "$IMG" -c 0f1117 -t -e
else
    exec i3lock -c 0f1117 -e
fi
