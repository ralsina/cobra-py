import os
import pty
import select
from pathlib import Path

import pyte

from cobra_py import rl
from cobra_py.kbd_layout import read_xmodmap
from cobra_py.raylib import ffi


# prepend ESC
def _esc(d: bytes):
    return b"\x1b" + d


# Codes for special keys
_keys = {
    36: b"\n",  # Enter
    23: b"\t",  # Tab
    66: b"\x1b",  # ESC
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


class RayTerminal(pyte.HistoryScreen):
    """A simple terminal with a graphical interface implemented using Raylib."""

    ctrl = False
    shift = False
    alt_gr = False

    def __init__(self, columns=80, rows=25, cmd="bash", fps=30, show_fps=False):
        """Create terminal.

        :columns: width in characters.
        :rows: height in characters.
        :cmd: command to run in the terminal.
        :fps: aim to this many FPS
        :show_fps: display a FPS counter.
        """

        super().__init__(columns, rows)
        self.rows = rows
        self._init_window()
        self._init_kbd()
        self._spawn_shell()
        rl.set_window_size(
            int(self.text_size.x * columns), int(self.text_size.y * rows)
        )
        rl.set_target_fps(fps)
        self.show_fps = show_fps

    def _init_kbd(self):
        self.keymap = read_xmodmap()

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
                    TERM="xterm",
                    COLUMNS=str(self.columns),
                    LINES=str(self.rows),
                    LC_ALL="en_US.UTF-8",
                ),
            )
        self.p_out = os.fdopen(master_fd, "w+b", 0)

    def key_event(self, key, scancode, action, mods):
        """Process one keyboard event.

        :key: as in glfw
        :scancode: as in glfw
        :action: as in glfw (X11 KeyCode)
        :mods: 0 is key release, 1 key press, 2 key repeat
        """

        print("in-scancode=>", key, scancode, action, mods)
        print(self.keymap[action])
        if mods == 0:  # Key release
            # FIXME: get mod codes from xmodmap
            if action == 37:  # ctrl
                print("ctrl-off")
                self.ctrl = False
            elif action == 50:  # shift
                print("shift-off")
                self.shift = False
            elif action == 108:  # AltGr
                print("altgr-off")
                self.alt_gr = False
            return

        # Key press (mods=1) or repeat (mods=2)

        # Modifiers
        if action == 37:
            print("ctrl-on")
            self.ctrl = True
        elif action == 50:
            print("shift-on")
            self.shift = True
        elif action == 108:  # AltGr
            print("altgr-on")
            self.alt_gr = True

        # ctrl-key doesn't repeat
        elif self.ctrl and mods == 1:
            # FIXME: generalize to all ctrl-things, add column in self.keymap
            if data := _ctrl_keys.get(action):
                print("--->", repr(data))
                self.p_out.write(data)

        # FIXME: get rid of this, use self.keymap
        elif data := _keys.get(action):
            print("--->", repr(data))
            self.p_out.write(data)

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
            print("---->", letter)
            self.p_out.write(letter)

    def run(self):
        while not rl.window_should_close():
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

            for y, line in enumerate(self.display):
                line = self.buffer[y]
                for x in range(self.columns):  # Can't enumerate, it's sparse
                    char = line[x]

                    fg = _colors.get(char.fg, rl.WHITE)
                    bg = _colors.get(char.bg, rl.BLACK)
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
            if self.show_fps:
                rl.draw_fps(10, 10)
            rl.end_drawing()
