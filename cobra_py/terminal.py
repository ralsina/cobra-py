import os
import pty
import select

import pyte

from cobra_py import rl
from cobra_py.kbd_layout import read_xmodmap
from cobra_py.raylib import ffi

# TODO:
# * mouse support
# * generalize keyboard support for screens/layers


# TODO: get rid of these dicts
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


class Terminal(pyte.HistoryScreen, rl.Layer):
    """A simple terminal with a graphical interface implemented using Raylib."""

    ctrl = False
    shift = False
    alt_gr = False
    mouse_pressed = False
    p_out = None
    last_cursor = (-1, -1)

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

    def mouse_event(self):
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
        # Honestly, this could go in a thread and block on select, but who cares

        self.mouse_event()

        ready, _, _ = select.select([self.p_out], [], [], 0)
        if ready:
            try:
                data = self.p_out.read(65535)
                if data:
                    self.stream.feed(data)
            except OSError:  # Program went away
                return
        rl.BeginTextureMode(self.texture)

        self.draw_cell(*self.last_cursor)
        self.draw_cell(self.cursor.x, self.cursor.y)
        if self.dirty:
            print(self.dirty, self.cursor.x, self.cursor.y)
        for y in self.dirty:
            for x in range(self.columns):  # Can't enumerate, it's sparse
                self.draw_cell(x, y)
        self.dirty.clear()

        rl.end_texture_mode()
