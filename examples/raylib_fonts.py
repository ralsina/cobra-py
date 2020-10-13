#!/usr/bin/env python
from pathlib import Path

from cobra_py import rl
from cobra_py.raylib import ffi

sw = 800
sh = 450

rl.init_window(sw, sh, b"Raylib Fonts")

font_path = str(Path(rl.__file__).parent / "resources" / "fonts" / "monoid.ttf").encode(
    "utf-8"
)
kepler_font = rl.LoadFontEx(font_path, 48, ffi.NULL, 0)

message = b"This is the Monoid Font"
text_size = rl.MeasureTextEx(kepler_font, message, kepler_font.baseSize, 0)

while not rl.window_should_close():
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)
    rl.draw_text_ex(
        kepler_font,
        message,
        ((sw - text_size.x) / 2, (sh - text_size.y) / 2),
        kepler_font.baseSize,
        0,
        rl.RED,
    )
    rl.end_drawing()
