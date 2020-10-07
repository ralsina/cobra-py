import pyglet
from PIL import Image, ImageDraw
from typing import Optional
from queue import Queue, Empty
import threading
from functools import partial

# Calculate window size
test_label = pyglet.text.Label("X", font_name="Courier", font_size=24)
fw = test_label.content_width
fh = int(test_label.content_height * 0.8)
sw = 80 * fw
sh = 25 * fh

# Create a basic window
window = pyglet.window.Window(width=sw, height=sh)

# graphical buffers
pil_buffer = Image.new("RGB", (sw, sh))
pyg_buffer = pyglet.image.ImageData(sw, sh, "RGB", pil_buffer.tobytes())
pil_draw = ImageDraw.Draw(pil_buffer)

batch = pyglet.graphics.Batch()


class Screen:
    def __init__(self):
        self.command_queue = Queue(maxsize=100)
        self._screen = []
        for x in range(80):  # rows
            self._screen.append([])
            for y in range(25):  # columns
                self._screen[-1].append(
                    pyglet.text.Label(
                        "",
                        font_name="Courier",
                        font_size=24,
                        x=x * fw,
                        y=y * fh,
                        batch=batch,
                    )
                )

    def process_events(self, _):
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                getattr(self, command)(*a, **kw)
                self.command_queue.task_done()
        except Empty:
            pass

    def print_at(self, x: int = 0, y: int = 0, text: str = ""):
        for i, c in enumerate(text):
            self._screen[x + i % 80][y].text = c

    def ellipse(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        outline: str = "white",
        fill: Optional[str] = None,
    ):
        pil_draw.ellipse((x0, y0, x1, y1), outline=outline, fill=fill)


screen = Screen()


def command(cmdname, *a, **kw):
    screen.command_queue.put((cmdname, a, kw))


print_at = partial(command, "print_at")
ellipse = partial(command, "ellipse")


def prompt():
    while True:
        cmd = input("> ")
        if cmd:
            eval(cmd)


x = threading.Thread(target=prompt)
x.start()

pyglet.clock.schedule(screen.process_events)


@window.event
def on_draw():
    window.clear()
    pyg_buffer.set_data("RGB", pyg_buffer.width * 3, pil_buffer.tobytes())
    pyg_buffer.blit(0, 0)
    batch.draw()


pyglet.app.run()
