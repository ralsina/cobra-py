#!/usr/bin/env python

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
font_path = str(Path(rl.__file__).parent / "resources" / "fonts" / "monoid.ttf").encode(
    "utf-8"
)
font = rl.load_font_ex(font_path, 24, ffi.NULL, 0)
text_size = rl.measure_text_ex(font, b"X", font.baseSize, 0)
sw = int(80 * text_size.x)
sh = int(25 * text_size.y)
rl.set_window_size(sw, sh)
rl.set_target_fps(60)


term = pyte.HistoryScreen(80, 25)
stream = pyte.ByteStream(term)

p_pid, master_fd = pty.fork()
if p_pid == 0:  # Child process
    os.execvpe(
        "bash",
        ["bash"],
        env=dict(TERM="linux", COLUMNS="80", LINES="25", LC_ALL="en_US.UTF-8"),
    )

p_out = os.fdopen(master_fd, "w+b", 0)


def esc(d: bytes):
    return b"\x1b[" + d


keys = {
    36: b"\n",  # Enter
    111: esc(b"A"),  # Cursor up
    116: esc(b"B"),  # Cursor down
    114: esc(b"C"),  # Cursor right
    113: esc(b"D"),  # Cursor left
    22: b"\b",  # Backspace
}

colors = {
    "black": rl.BLACK,
    "red": rl.RED,
    "green": rl.GREEN,
    "brown": rl.BROWN,
    "blue": rl.BLUE,
    "magenta": rl.MAGENTA,
    "cyan": (0,255,255,255),
    "white": rl.WHITE,
}


@ffi.callback("void(int,int,int,int)")
def key_event(key, scancode, action, mods):
    print("scancode=>", key, scancode, action)
    if mods == 1:  # Key release
        return
    if data := keys.get(action):
        p_out.write(data)


rl.set_key_callback(key_event)


while not rl.window_should_close():
    # FIXME: can probably handle it all in key_event
    key = rl.get_key_pressed()
    while key > 0:
        k = chr(key).encode("utf-8")
        p_out.write(k)
        key = rl.get_key_pressed()

    rl.begin_drawing()
    rl.clear_background(rl.DARKBLUE)

    ready, _, _ = select.select([p_out], [], [], 0)
    if ready:
        data = p_out.read(1024)
        if data:
            stream.feed(data)

    for y, line in enumerate(term.display):
        line = term.buffer[y]
        for x in range(term.columns):  # Can't enumerate, it's sparse
            char = line[x]

            fg = colors.get(char.fg, rl.WHITE)
            bg = colors.get(char.bg, rl.BLACK)
            if char.reverse:
                fg, bg = bg, fg

            rl.draw_rectangle(
                int(x * text_size.x),
                int(y * text_size.y),
                int(text_size.x),
                int(text_size.y),
                bg,
            )
            rl.draw_text_ex(
                font,
                char.data.encode("utf-8"),
                (x * text_size.x, y * text_size.y),
                font.baseSize,
                0,
                fg,
            )
    term.dirty.clear()

    # draw cursor
    rl.draw_rectangle(
        int(term.cursor.x * text_size.x),
        int(term.cursor.y * text_size.y),
        int(text_size.x),
        int(text_size.y),
        (100, 108, 100, 100),
    )
    rl.draw_fps(400, 50)
    rl.end_drawing()
