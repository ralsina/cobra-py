import os
import pty
import select
from pathlib import Path

import pyte

from cobra_py import rl
from cobra_py.kbd_layout import read_xmodmap
from cobra_py.raylib import ffi

# Codes for ctrl+keys
_ctrl_keys = {40: b"\x04", 54: b"\x03", 27: b"\x12"}

# Color palette
_colors = {
    "black": rl.BLACK,
    "red": rl.RED,
    "green": rl.GREEN,
    "brown": rl.BROWN,
    "blue": rl.BLUE,
    "magenta": rl.MAGENTA,
    "cyan": (0, 255, 255, 255),
    "white": rl.WHITE,
}


def parse_color(rgb):
    r = int(rgb[:2], 16)
    g = int(rgb[2:4], 16)
    b = int(rgb[4:6], 16)
    color = (r, g, b, 255)
    return color


class RayTerminal(pyte.HistoryScreen, rl.Layer):
    """A simple terminal with a graphical interface implemented using Raylib."""

    ctrl = False
    shift = False
    alt_gr = False
    p_out = None

    def __init__(self, screen, cmd="bash"):
        """Create terminal.

        :cmd: command to run in the terminal.
        """

        rl.Layer.__init__(self, screen)
        self.text_size = screen.text_size
        self.font = screen.font
        self.rows = int(self._screen.height // self.text_size.y)
        self.columns = int(self._screen.width // self.text_size.x)
        print(self.rows, self.columns)
        pyte.HistoryScreen.__init__(self, self.columns, self.rows)
        self._init_kbd()
        self._spawn_shell(cmd)
        self.__cb = ffi.callback("void(int,int,int,int)")(lambda *a: self.key_event(*a))
        rl.set_key_callback(self.__cb)

    def _init_kbd(self):
        self.keymap = read_xmodmap()

    def write_process_input(self, data):
        if self.p_out is not None:
            self.p_out.write(data.encode("utf-8"))

    def _spawn_shell(self, cmd):
        self.stream = pyte.ByteStream(self)
        p_pid, master_fd = pty.fork()
        if p_pid == 0:  # Child process
            os.execvpe(
                cmd,
                [cmd],
                env=dict(
                    TERM="xterm",
                    COLUMNS=str(self.columns),
                    LINES=str(self.rows),
                    LC_ALL="en_US.UTF-8",
                ),
            )
        self.p_out = os.fdopen(master_fd, "w+b", 0)

    def set_margins(self, *args, **kwargs):
        # See https://github.com/selectel/pyte/issues/67
        kwargs.pop("private", None)
        return super().set_margins(*args, **kwargs)

    def key_event(self, key, scancode, action, mods):
        """Process one keyboard event.

        :key: as in glfw
        :scancode: as in glfw
        :action: as in glfw (X11 KeyCode)
        :mods: 0 is key release, 1 key press, 2 key repeat
        """

        if mods == 0:  # Key release
            # FIXME: get mod codes from xmodmap
            if action in {37, 105}:  # ctrl
                self.ctrl = False
            elif action in {50, 62}:  # shift
                self.shift = False
            elif action == 108:  # AltGr
                self.alt_gr = False
            return

        # Key press (mods=1) or repeat (mods=2)

        # Modifiers
        if action == 37:
            self.ctrl = True
        elif action == 50:
            self.shift = True
        elif action == 108:  # AltGr
            self.alt_gr = True

        # ctrl-key doesn't repeat
        elif self.ctrl and mods == 1:
            # FIXME: generalize to all ctrl-things, add column in self.keymap
            self.p_out.write(_ctrl_keys.get(action, b""))

        else:
            if self.shift:
                if self.alt_gr:
                    letter = self.keymap[action][3]
                else:
                    letter = self.keymap[action][1]
            else:
                if self.alt_gr:
                    letter = self.keymap[action][2]
                else:
                    letter = self.keymap[action][0]
            self.p_out.write(letter)

    def update(self):
        ready, _, _ = select.select([self.p_out], [], [], 0)
        if ready:
            try:
                data = self.p_out.read(1024)
                if data:
                    self.stream.feed(data)
            except OSError:  # Program went away
                return
        rl.BeginTextureMode(self.texture)
        rl.clear_background(rl.BLACK)

        # FIXME: There is lots and lots to optimize here
        for y, line in enumerate(self.display):
            line = self.buffer[y]
            for x in range(self.columns):  # Can't enumerate, it's sparse
                char = line[x]
                if char.fg == "default":
                    fg = rl.RAYWHITE
                else:
                    fg = _colors.get(char.fg, None) or parse_color(char.fg)
                if char.bg == "default":
                    bg = (0, 0, 0, 0)  # Transparent
                else:
                    bg = _colors.get(char.bg, None) or parse_color(char.bg)

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
        self.dirty.clear()

        # draw cursor
        rl.draw_rectangle(
            int(self.cursor.x * self.text_size.x),
            int(self.cursor.y * self.text_size.y),
            int(self.text_size.x),
            int(self.text_size.y),
            (100, 108, 100, 100),
        )
        rl.end_texture_mode()
