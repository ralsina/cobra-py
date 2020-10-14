import os
import pty
import select
import shutil
import shlex

import pyte

from cobra_py import rl
from cobra_py.kbd_layout import read_xmodmap

# TODO:
# * mouse support
# * generalize keyboard support for screens/layers

# Codes for ctrl+keys


def ctrl_key(char: bytes):
    if 96 < char[0] < 123:
        return chr(ord(char) & 31).encode("utf8")
    return char


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


class Terminal(pyte.HistoryScreen, rl.Layer):
    """A simple terminal with a graphical interface implemented using Raylib."""

    ctrl = False
    shift = False
    alt = False
    alt_gr = False
    mouse_pressed = False
    p_out = None
    last_cursor = (-1, -1)

    # Ideally this should change when we get the SGR switch escape sequence
    # but Pyte doesn't support that yet
    mouse_enabled = False

    def __init__(self, screen, cmd="bash"):
        """Create terminal.

        :cmd: command to run in the terminal.
        """

        rl.Layer.__init__(self, screen)
        self.text_size = screen.text_size
        self.font = screen.font
        self.rows = int(self._screen.height // self.text_size.y)
        self.columns = int(self._screen.width // self.text_size.x)
        pyte.HistoryScreen.__init__(self, self.columns, self.rows)
        self._init_kbd()
        self._spawn_shell(cmd)

    def _init_kbd(self):
        self.keymap = read_xmodmap()

    def write_process_input(self, data):
        if self.p_out is not None:
            self.p_out.write(data.encode("utf-8"))

    def _spawn_shell(self, cmd):
        self.stream = pyte.ByteStream(self)
        cmd = shlex.split(cmd)
        cmd_path = shutil.which(cmd[0])
        p_pid, master_fd = pty.fork()
        if p_pid == 0:  # Child process
            os.execvpe(
                cmd_path,
                cmd,
                env=dict(
                    TERM="xterm",
                    COLUMNS=str(self.columns),
                    LINES=str(self.rows),
                    LC_ALL="en_US.UTF-8",
                    PATH="/usr/bin:/bin",
                ),
            )
        self.p_out = os.fdopen(master_fd, "w+b", 0)

    def set_margins(self, *args, **kwargs):
        # See https://github.com/selectel/pyte/issues/67
        kwargs.pop("private", None)
        return super().set_margins(*args, **kwargs)

    def mouse_event(self):
        if not self.mouse_enabled:
            return
        # See https://github.com/prompt-toolkit/python-prompt-toolkit/blob/master/prompt_toolkit/key_binding/bindings/mouse.py#L23
        # For examples of decoding these events we are generating
        x = int(rl.get_mouse_x() // self.text_size.x) + 1
        y = int(rl.get_mouse_y() // self.text_size.y) + 1

        if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON):
            self.mouse_pressed = True

            # This is using SGR mouse codes, which work on some apps and not in others
            self.p_out.write(b"\x1b" + f"[<0;{str(x)};{str(y)}M".encode("utf-8"))
            # This is "typical" (seems broken)
            # self.p_out.write(b"\x1b" + f"M{chr(32)}{chr(x)}{chr(y)}".encode("utf-8"))

        elif self.mouse_pressed and not rl.is_mouse_button_pressed(
            rl.MOUSE_LEFT_BUTTON
        ):
            self.mouse_pressed = False
            # This is using SGR mouse codes, which work on some apps and not in others
            self.p_out.write(b"\x1b" + f"[<0;{str(x)};{str(y)}m".encode("utf-8"))
            # This is "typical" (seems broken)
            # self.p_out.write(b"\x1b" + f"M{chr(35)}{chr(x)}{chr(y)}".encode("utf-8"))

    def key_event(
        self,
        action: int,
        mods: int,
        ctrl: bool,
        shift: bool,
        alt: bool,
        altgr: bool,
    ):
        """Process one keyboard event, convert to terminal-appropriate data and feed to app."""
        if mods == 0:  # key release
            return

        elif ctrl:
            letter = ctrl_key(self.keymap[action][0])
        elif alt:
            letter = b"\x1b" + self.keymap[action][0]
        elif shift:
            if altgr:
                letter = self.keymap[action][3]
            else:
                letter = self.keymap[action][1]
        else:
            if altgr:
                letter = self.keymap[action][2]
            else:
                letter = self.keymap[action][0]
        self.p_out.write(letter)

    def draw_cell(self, x, y):
        char = self.buffer[y][x]
        if char.fg == "default":
            fg = rl.RAYWHITE
        else:
            fg = _colors.get(char.fg, None) or parse_color(char.fg)
        if char.bg == "default":
            bg = rl.BLACK
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
        if (x, y) == (self.cursor.x, self.cursor.y):
            self.last_cursor = (x, y)
            rl.draw_rectangle(
                int(self.cursor.x * self.text_size.x),
                int(self.cursor.y * self.text_size.y),
                int(self.text_size.x),
                int(self.text_size.y),
                (255, 255, 255, 100),
            )

    def update(self):
        self.mouse_event()

        # Honestly, this could go in a thread and block on select, but who cares
        ready, _, _ = select.select([self.p_out], [], [], 0)
        if ready:
            try:
                data = self.p_out.read(65535)
                if data:
                    self.stream.feed(data)
            except OSError:  # Program went away
                return
        rl.begin_texture_mode(self.texture)

        self.draw_cell(*self.last_cursor)
        self.draw_cell(self.cursor.x, self.cursor.y)
        for y in self.dirty:
            for x in range(self.columns):  # Can't enumerate, it's sparse
                self.draw_cell(x, y)
        self.dirty.clear()

        rl.end_texture_mode()
