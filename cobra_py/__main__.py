import threading
from functools import partial
from pathlib import Path
from queue import Empty, Queue
from typing import Tuple

from cobra_py import rl
from cobra_py.raylib import ffi

sw = 800
sh = 450

window = rl.init_window(sw, sh, b"Cobra Py!")

font_path = str(
    Path(rl.__file__).parent / "resources" / "fonts" / "Kepler-452b.ttf"
).encode("utf-8")
font = rl.load_font_ex(font_path, 24, ffi.NULL, 0)
text_size = rl.measure_text_ex(font, b"X", font.baseSize, 0)
sw = int(80 * text_size.x)
sh = int(25 * text_size.y)
rl.set_window_size(sw, sh)
rl.set_target_fps(60)

rl.set_trace_log_level(rl.LOG_NONE)


class Screen:
    def __init__(self):
        self.command_queue = Queue(maxsize=100)
        self._screen = []
        for y in range(25):  # rows
            self._screen.append([])
            for x in range(80):  # columns
                self._screen[-1].append(b" ")
        self._buffer = rl.gen_image_color(sw, sh, (rl.RAYWHITE))
        self._buffer_texture = None
        self._update_buffer_texture()

    def _update_buffer_texture(self):
        if self._buffer_texture is not None:
            rl.unload_texture(self._buffer_texture)
        self._buffer_texture = rl.load_texture_from_image(self._buffer)

    def event_loop(self):
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)
        # Draw text mode screen
        for y, row in enumerate(self._screen):
            rl.draw_text_ex(
                font,
                b"".join(row),
                (0, y * text_size.y),
                font.baseSize,
                0,
                rl.RED,
            )
        # Draw graphics buffer
        rl.draw_texture(self._buffer_texture, 0, 0, rl.WHITE)
        rl.draw_fps(10, 10)
        rl.end_drawing()

    def process_commands(self):
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                getattr(self, command)(*a, **kw)
                self.command_queue.task_done()
        except Empty:
            pass

    def print_at(self, x: int = 0, y: int = 0, text: str = ""):
        for i, c in enumerate(text):
            self._screen[x + i % 80][y] = c.encode("utf-8")

    def circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int, int]):
        rl.image_draw_circle(ffi.addressof(self._buffer), x, y, radius, color)
        self._update_buffer_texture()


screen = Screen()


def command(cmdname, *a, **kw):
    screen.command_queue.put((cmdname, a, kw))


print_at = partial(command, "print_at")
circle = partial(command, "circle")


def prompt():
    while True:
        cmd = input("> ")
        if cmd:
            eval(cmd)


x = threading.Thread(target=prompt)
x.start()

screen.circle(100, 100, 50, rl.RED)

while not rl.window_should_close():
    screen.process_commands()
    screen.event_loop()
