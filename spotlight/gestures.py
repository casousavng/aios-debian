#!/usr/bin/env python3
"""Lightweight 3-finger touchpad swipe daemon for AI-OS using libinput debug-events."""
import re
import subprocess
import sys

SWIPE_RE = re.compile(r"GESTURE_SWIPE_(BEGIN|UPDATE|END)\s+\S+\s+(\d+)\s*(?:([\d.-]+)/([\d.-]+))?")


def switch_ws(delta: int):
    try:
        out = subprocess.check_output(["wmctrl", "-d"], text=True, stderr=subprocess.DEVNULL)
        lines = out.splitlines()
        cur = 0
        for i, l in enumerate(lines):
            parts = l.split()
            if len(parts) >= 2 and parts[1] == "*":
                cur = i
                break
        nxt = max(0, min(len(lines) - 1, cur + delta))
        if nxt != cur:
            subprocess.Popen(["wmctrl", "-s", str(nxt)])
    except Exception:
        pass


def main():
    try:
        proc = subprocess.Popen(
            ["libinput", "debug-events"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError:
        sys.exit(0)

    dx_sum = 0.0
    dy_sum = 0.0
    fingers = 0

    for line in proc.stdout:
        m = SWIPE_RE.search(line)
        if not m:
            continue
        kind, f_str, dx_s, dy_s = m.groups()
        f = int(f_str)
        if kind == "BEGIN":
            dx_sum = 0.0
            dy_sum = 0.0
            fingers = f
        elif kind == "UPDATE" and dx_s and dy_s:
            dx_sum += float(dx_s)
            dy_sum += float(dy_s)
        elif kind == "END" and fingers == 3:
            if abs(dx_sum) > abs(dy_sum) and abs(dx_sum) >= 35:
                # Swipe left -> next workspace; swipe right -> previous workspace
                switch_ws(1 if dx_sum < 0 else -1)
            elif dy_sum <= -35 and abs(dy_sum) > abs(dx_sum):
                subprocess.Popen(["pkill", "-USR1", "-f", "^python3 /opt/ai-os/spotlight/spotlight_ui.py"])
            dx_sum = 0.0
            dy_sum = 0.0
            fingers = 0


if __name__ == "__main__":
    main()
