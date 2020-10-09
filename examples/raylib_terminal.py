#!/usr/bin/env python

import os
import pty
import select
from pathlib import Path

import pyte

from cobra_py import rl
from cobra_py.raylib import ffi


def _esc(d: bytes):
    return b"\x1b" + d


keys = {
    36: b"\n",  # Enter
    23: b"\t",  # Tab
    66: b"\x1b",  # ESC
    111: _esc(b"[A"),  # Cursor up
    116: _esc(b"[B"),  # Cursor down
    114: _esc(b"[C"),  # Cursor right
    113: _esc(b"[D"),  # Cursor left
    22: b"\b",  # Backspace
    119: _esc(b"[3~"),  # Delete
    67: _esc(b"OP"),  # F1
    68: _esc(b"OQ"),  # F2
    69: _esc(b"OR"),  # F3
    70: _esc(b"OS"),  # F4
    71: _esc(b"[15~"),  # F5
    72: _esc(b"[17~"),  # F6
    73: _esc(b"[18~"),  # F7
    74: _esc(b"[19~"),  # F8
    75: _esc(b"[20~"),  # F9
    76: _esc(b"[21~"),  # F10
    95: _esc(b"[23~"),  # F11
    96: _esc(b"[24~"),  # F12
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


class RayTerminal(pyte.HistoryScreen):
    ctrl = False

    def __init__(self, columns, rows):
        super().__init__(columns, rows)
        self.rows = rows
        self._init_window()
        self._spawn_shell()
        rl.set_window_size(
            int(self.text_size.x * columns), int(self.text_size.y * rows)
        )
        rl.set_target_fps(24)

    def _init_window(self):
        rl.init_window(1, 1, b"CobraPy Terminal!")
        font_path = str(
            Path(rl.__file__).parent / "resources" / "fonts" / "monoid.ttf"
        ).encode("utf-8")
        self.font = rl.load_font_ex(font_path, 24, ffi.NULL, 0)
        self.text_size = rl.measure_text_ex(self.font, b"X", self.font.baseSize, 0)

        self.__cb = ffi.callback("void(int,int,int,int)")(lambda *a: self.key_event(*a))
        rl.set_key_callback(self.__cb)

    def _spawn_shell(self):
        self.stream = pyte.ByteStream(self)
        p_pid, master_fd = pty.fork()
        if p_pid == 0:  # Child process
            os.execvpe(
                "bash",
                ["bash"],
                env=dict(
                    TERM="vt220",
                    COLUMNS=str(self.columns),
                    LINES=str(self.rows),
                    LC_ALL="en_US.UTF-8",
                ),
            )
        self.p_out = os.fdopen(master_fd, "w+b", 0)

    def key_event(self, key, scancode, action, mods):
        print("in-scancode=>", key, scancode, action, self.ctrl, mods)
        if mods == 0:  # Key release
            if action == 37:  # ctrl
                print("ctrl-off")
                self.ctrl = False
            print("out-scancode=>", key, scancode, action, self.ctrl, mods)
            return

        # Key press or repeat
        if action == 37:
            print("ctrl-on")
            self.ctrl = True
        if self.ctrl and mods == 1:  # ctrl-key doesn't repeat
            if data := ctrl_keys.get(action):
                print("--->", repr(data))
                self.p_out.write(data)
        elif data := keys.get(action):
            print("--->", repr(data))
            self.p_out.write(data)
        print("out-scancode=>", key, scancode, action, self.ctrl, mods)

    def run(self):
        while not rl.window_should_close():
            # FIXME: can probably handle it all in key_event
            key = rl.get_key_pressed()
            while key > 0:
                k = chr(key).encode("utf-8")
                self.p_out.write(k)
                key = rl.get_key_pressed()

            rl.begin_drawing()
            rl.clear_background(rl.DARKBLUE)

            ready, _, _ = select.select([self.p_out], [], [], 0)
            if ready:
                try:
                    data = self.p_out.read(1024)
                    if data:
                        self.stream.feed(data)
                except OSError:  # Program went away
                    break

            for y, line in enumerate(term.display):
                line = term.buffer[y]
                for x in range(term.columns):  # Can't enumerate, it's sparse
                    char = line[x]

                    fg = colors.get(char.fg, rl.WHITE)
                    bg = colors.get(char.bg, rl.BLACK)
                    if char.reverse:
                        fg, bg = bg, fg

                    rl.draw_rectangle(
                        int(x * self.text_size.x),
                        int(y * self.text_size.y),
                        int(self.text_size.x),
                        int(self.text_size.y),
                        bg,
                    )
                    rl.draw_text_ex(
                        self.font,
                        char.data.encode("utf-8"),
                        (x * self.text_size.x, y * self.text_size.y),
                        self.font.baseSize,
                        0,
                        fg,
                    )
            term.dirty.clear()

            # draw cursor
            rl.draw_rectangle(
                int(term.cursor.x * self.text_size.x),
                int(term.cursor.y * self.text_size.y),
                int(self.text_size.x),
                int(self.text_size.y),
                (100, 108, 100, 100),
            )
            rl.draw_fps(850, 10)
            rl.end_drawing()


if __name__ == "__main__":
    term = RayTerminal(80, 25)
    term.run()
