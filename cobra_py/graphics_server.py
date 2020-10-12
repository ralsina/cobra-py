"""Server for the CobraPy graphics protocol."""

from queue import Empty
from ipcqueue.posixmq import Queue
from cobra_py import rl
from typing import Tuple


class Server(rl.Layer):
    """A server for the protocol.

    * It listens on a queue
    * It accepts commands
    * Does something with them
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.command_queue = Queue("/foo")

    def update(self):
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                getattr(self, command)(*a, **kw)
        except Empty:
            pass

    # Below here: things that draw things and whatnot

    def circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int, int]):
        rl.BeginTextureMode(self.texture)
        rl.draw_circle(x, y, int(radius), color)
        rl.EndTextureMode()


exported = tuple(fname for fname in dir(Server) if not fname.startswith("__"))
