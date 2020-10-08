#!/usr/bin/env python
# This is literally the pygame hello world example.

import os
import pty
import select
from pathlib import Path

import pyte

from cobra_py import rl
from cobra_py.raylib import ffi

sw = 800
sh = 450


rl.init_window(sw, sh, b"CobraPy Terminal!")
font_path = str(
    Path(rl.__file__).parent / "resources" / "fonts" / "Kepler-452b.ttf"
).encode("utf-8")
font = rl.load_font_ex(font_path, 24, ffi.NULL, 0)
text_size = rl.measure_text_ex(font, b"X", font.baseSize, 0)
sw = int(80 * text_size.x)
sh = int(25 * text_size.y)
rl.set_window_size(sw, sh)
rl.set_target_fps(60)


term = pyte.Screen(80, 24)
stream = pyte.ByteStream(term)

p_pid, master_fd = pty.fork()
if p_pid == 0:  # Child process
    os.execvpe(
        "bash",
        ["bash"],
        env=dict(TERM="linux", COLUMNS="80", LINES="24", LC_ALL="en_US.UTF-8"),
    )

p_out = os.fdopen(master_fd, "w+b", 0)


@ffi.callback("void(int,int,int,int)")
def key_event(key, scancode, action, mods):
    print("scancode=>", key, scancode, action)
    if mods == 1:  # Key release
        return
    if action == 36:
        p_out.write(b"\n")


rl.set_key_callback(key_event)


while not rl.window_should_close():
    key = rl.get_key_pressed()
    while key > 0:
        k = chr(key).encode("utf-8")
        print("===>", k, chr(key), key)
        p_out.write(k)
        key = rl.get_key_pressed()
        print("===>", k, chr(key), key)

    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)

    ready, _, _ = select.select([p_out], [], [], 0)
    if ready:
        data = p_out.read(1024)
        if data:
            stream.feed(data)

    for i, row in enumerate(term.display):
        text = row.encode("utf-8")
        rl.draw_text_ex(
            font,
            text,
            (0, i * text_size.y),
            font.baseSize,
            0,
            rl.RED,
        )
    # rl.draw_fps(10, 10)
    rl.end_drawing()
