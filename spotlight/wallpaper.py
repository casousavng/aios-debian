#!/usr/bin/env python3
"""Generates a sleek flowing-wave dynamic wallpaper for AI-OS and applies it via PCManFM."""
import datetime
import math
import os
import subprocess
from pathlib import Path

import cairo

WALLPAPER_PATH = Path.home() / ".ai-os" / "wallpaper.png"
WIDTH, HEIGHT = 1920, 1200


def palette_for_hour(hour: int):
    if 6 <= hour < 12:  # Manhã
        return (0.07, 0.10, 0.14), (0.04, 0.06, 0.09), (0.20, 0.68, 0.72), (0.85, 0.58, 0.30)
    if 12 <= hour < 18:  # Tarde
        return (0.08, 0.11, 0.16), (0.05, 0.07, 0.11), (0.18, 0.65, 0.68), (0.76, 0.54, 0.30)
    if 18 <= hour < 22:  # Entardecer
        return (0.07, 0.10, 0.15), (0.04, 0.06, 0.10), (0.16, 0.58, 0.62), (0.78, 0.50, 0.28)
    # Noite
    return (0.06, 0.09, 0.13), (0.03, 0.05, 0.08), (0.14, 0.56, 0.60), (0.72, 0.46, 0.26)


def draw_wave(ctx, y_base, amp, phase, c1, c2, alpha):
    ctx.save()
    ctx.move_to(0, HEIGHT)
    ctx.line_to(0, y_base)
    ctx.curve_to(
        WIDTH * 0.28, y_base - amp * math.cos(phase),
        WIDTH * 0.62, y_base + amp * math.sin(phase),
        WIDTH, y_base - amp * 0.5,
    )
    ctx.line_to(WIDTH, HEIGHT)
    ctx.close_path()

    grad = cairo.LinearGradient(0, y_base - amp, WIDTH, HEIGHT)
    grad.add_color_stop_rgba(0.0, *c1, alpha)
    grad.add_color_stop_rgba(0.55, *c2, alpha * 0.65)
    grad.add_color_stop_rgba(1.0, 0.04, 0.06, 0.09, 0.95)
    ctx.set_source(grad)
    ctx.fill()
    ctx.restore()


def generate_and_apply():
    WALLPAPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    c_top, c_bot, teal, amber = palette_for_hour(now.hour)
    phase = (now.hour * 60 + now.minute) / 1440.0 * 2.0 * math.pi

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    # Deep slate base gradient
    bg = cairo.LinearGradient(0, 0, WIDTH, HEIGHT)
    bg.add_color_stop_rgb(0.0, *c_top)
    bg.add_color_stop_rgb(1.0, *c_bot)
    ctx.set_source(bg)
    ctx.paint()

    # Warm amber glow left-center
    g_amber = cairo.RadialGradient(
        WIDTH * 0.34, HEIGHT * 0.42, 40,
        WIDTH * 0.34, HEIGHT * 0.42, WIDTH * 0.48,
    )
    g_amber.add_color_stop_rgba(0.0, *amber, 0.26)
    g_amber.add_color_stop_rgba(1.0, *amber, 0.0)
    ctx.set_source(g_amber)
    ctx.paint()

    # Teal aurora glow upper-right
    g_teal = cairo.RadialGradient(
        WIDTH * 0.72, HEIGHT * 0.34, 40,
        WIDTH * 0.72, HEIGHT * 0.34, WIDTH * 0.50,
    )
    g_teal.add_color_stop_rgba(0.0, *teal, 0.32)
    g_teal.add_color_stop_rgba(1.0, *teal, 0.0)
    ctx.set_source(g_teal)
    ctx.paint()

    # Silky overlapping wave ribbons
    draw_wave(ctx, HEIGHT * 0.48, 220, phase + 0.4, amber, teal, 0.28)
    draw_wave(ctx, HEIGHT * 0.58, 260, phase + 1.2, teal, c_top, 0.42)
    draw_wave(ctx, HEIGHT * 0.70, 190, phase + 2.1, teal, c_bot, 0.65)

    surface.write_to_png(str(WALLPAPER_PATH))

    env = os.environ.copy()
    env.setdefault("DISPLAY", ":0")
    subprocess.run(
        ["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", f"file://{WALLPAPER_PATH}"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["gsettings", "set", "org.cinnamon.desktop.background", "picture-options", "zoom"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    generate_and_apply()
