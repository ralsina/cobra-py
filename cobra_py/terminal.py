import os
import pty
import select
from pathlib import Path
from queue import Empty
from typing import Tuple

import pyte
from ipcqueue.posixmq import Queue

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


class RayTerminal(pyte.HistoryScreen):
    """A simple terminal with a graphical interface implemented using Raylib."""

    ctrl = False
    shift = False
    alt_gr = False
    p_out = None

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
        sw = int(self.text_size.x * columns)
        sh = int(self.text_size.y * rows)
        rl.set_window_size(sw, sh)
        rl.set_target_fps(fps)
        self.show_fps = show_fps
        self._buffer = rl.gen_image_color(sw, sh, (255, 0, 0, 0))
        self._buffer_texture = rl.load_render_texture(sw, sh)
        rl.BeginTextureMode(self._buffer_texture)
        rl.ClearBackground((0, 0, 0, 0))
        rl.EndTextureMode()

        self.command_queue = Queue("/foo")

    def process_commands(self):
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                getattr(self, command)(*a, **kw)
        except Empty:
            pass

    def _init_kbd(self):
        self.keymap = read_xmodmap()

    def write_process_input(self, data):
        if self.p_out is not None:
            self.p_out.write(data.encode("utf-8"))

    def _init_window(self):
        rl.init_window(1, 1, b"CobraPy Terminal!")
        font_path = str(
            Path(rl.__file__).parent / "resources" / "fonts" / "monoid.ttf"
        ).encode("utf-8")
        self.font = rl.load_font_ex(font_path, 24, ffi.NULL, 1024)
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
                    TERM="xterm-256color",
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

    def run(self):
        while not rl.window_should_close():
            self.process_commands()
            rl.begin_drawing()
            rl.clear_background(rl.BLACK)

            ready, _, _ = select.select([self.p_out], [], [], 0)
            if ready:
                try:
                    data = self.p_out.read(1024)
                    if data:
                        self.stream.feed(data)
                except OSError:  # Program went away
                    break

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

            # Draw graphics buffer
            rl.draw_texture_rec(
                self._buffer_texture.texture,
                (
                    0,
                    0,
                    self._buffer_texture.texture.width,
                    -self._buffer_texture.texture.height,
                ),
                (0, 0),
                rl.WHITE,
            )

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

    def circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int, int]):
        rl.BeginTextureMode(self._buffer_texture)
        rl.draw_circle(x, y, int(radius), color)
        rl.EndTextureMode()
