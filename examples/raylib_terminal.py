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
rl.set_target_fps(24)


term = pyte.HistoryScreen(80, 25)
stream = pyte.ByteStream(term)

p_pid, master_fd = pty.fork()
if p_pid == 0:  # Child process
    os.execvpe(
        "bash",
        ["bash"],
        env=dict(TERM="xterm", COLUMNS="80", LINES="25", LC_ALL="en_US.UTF-8"),
    )

p_out = os.fdopen(master_fd, "w+b", 0)


def esc(d: bytes):
    return b"\x1b" + d


keys = {
    36: b"\n",  # Enter
    23: b"\t",  # Tab
    66: b"\x1b",  # ESC
    111: esc(b"[A"),  # Cursor up
    116: esc(b"[B"),  # Cursor down
    114: esc(b"[C"),  # Cursor right
    113: esc(b"[D"),  # Cursor left
    22: b"\b",  # Backspace
    119: esc(b"[3~"),  # Delete
    67: esc(b"OP"),  # F1
    68: esc(b"OQ"),  # F2
    69: esc(b"OR"),  # F3
    70: esc(b"OS"),  # F4
    71: esc(b"[15~"),  # F5
    72: esc(b"[17~"),  # F6
    73: esc(b"[18~"),  # F7
    74: esc(b"[19~"),  # F8
    75: esc(b"[20~"),  # F9
    76: esc(b"[21~"),  # F10
    95: esc(b"[23~"),  # F11
    96: esc(b"[24~"),  # F12
}

ctrl_keys = {40: b"\x04", 54: b"\x03", 27: b"\x12"}  # D  # C  # R

colors = {
    "black": rl.BLACK,
    "red": rl.RED,
    "green": rl.GREEN,
    "brown": rl.BROWN,
    "blue": rl.BLUE,
    "magenta": rl.MAGENTA,
    "cyan": (0, 255, 255, 255),
    "white": rl.WHITE,
}

ctrl = False


@ffi.callback("void(int,int,int,int)")
def key_event(key, scancode, action, mods):
    global ctrl
    print("in-scancode=>", key, scancode, action, ctrl, mods)
    if mods == 0:  # Key release
        if action == 37:  # ctrl
            print("ctrl-off")
            ctrl = False
        print("out-scancode=>", key, scancode, action, ctrl, mods)
        return

    # Key press or repeat
    if action == 37:
        print("ctrl-on")
        ctrl = True
    if ctrl and mods == 1:  # ctrl-key doesn't repeat
        if data := ctrl_keys.get(action):
            print("--->", repr(data))
            p_out.write(data)
    elif data := keys.get(action):
        print("--->", repr(data))
        p_out.write(data)
    print("out-scancode=>", key, scancode, action, ctrl, mods)


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
