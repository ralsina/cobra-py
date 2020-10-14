"""Server for the CobraPy graphics protocol."""

from queue import Empty
from typing import Tuple

from ipcqueue.posixmq import Queue

from cobra_py import rl
from cobra_py.sprite_layer import SpriteLayer


class Server(rl.Layer):
    """A server for the protocol.

    * It listens on a queue
    * It accepts commands
    * Does something with them
    """

    def __init__(self, screen):
        super().__init__(screen)
        self.sprites = SpriteLayer(screen)

        self.command_queue = Queue("/foo")
        self.event_queue = Queue("/bar")

    def key_event(
        self,
        action: int,
        mods: int,
        ctrl: bool,
        shift: bool,
        alt: bool,
        altgr: bool,
    ):
        "Forward key events to the client process via event_queue"
        self.event_queue.put(
            {
                "action": action,
                "mods": mods,
                "ctrl": ctrl,
                "shift": shift,
                "alt": alt,
                "altgr": altgr,
            }
        )

    def load_sprite(self, name: str, image: str):
        """Add a sprite to the sprite layer."""
        self.sprites.load_sprite(name, image.encode("utf8"))

    def move_sprite(self, name: str, x: int, y: int):
        self.sprites.sprites[name].x = x
        self.sprites.sprites[name].y = y

    def update(self):
        rl.BeginTextureMode(self.texture)
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                getattr(self, command)(*a, **kw)
        except Empty:
            pass
        rl.EndTextureMode()

    # Below here: things that draw things and whatnot
    def circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int, int]):
        rl.draw_circle(x, y, int(radius), color)


reserved = {"update", "key_event"}
exported = tuple(
    fname
    for fname in dir(Server)
    if fname not in reserved and not fname.startswith("__")
)
