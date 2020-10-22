"""Server for the CobraPy graphics protocol."""

import uuid
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

    def __init__(self, screen: rl.Screen, enabled: bool = True):
        self.sprites = SpriteLayer(screen, enabled=enabled)
        super().__init__(screen, enabled=enabled)
        self.enabled = enabled

        self.command_queue = Queue("/foo")
        self.result_queue = Queue("/bar")
        self.event_queues = []

        self.sounds = {}
        self.musics = {}
        self.music_playing = None
        rl.init_audio_device()

    def get_key_events(self) -> Queue:
        q_id = "/" + uuid.uuid4().hex
        self.event_queues.append(Queue(q_id))
        return q_id

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        self.sprites.enabled = value

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
        # print("key->", action)
        for q in self.event_queues:
            q.put_nowait(
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
        # FIXME move error check into Sprites
        if name not in self.sprites.sprites:
            return
        x = int(x)
        y = int(y)
        self.sprites.sprites[name].x = x
        self.sprites.sprites[name].y = y

    def r_check_collision(self, s1: str, s2: str) -> bool:
        return self.sprites.check_collision(s1, s2)

    def update(self):
        if self.music_playing:
            rl.update_music_stream(self.musics[self.music_playing])
        rl.BeginTextureMode(self.texture)
        try:
            while True:
                command, a, kw = self.command_queue.get(False)
                fn = getattr(self, command, None)
                if fn is None:
                    print("Unknown command:", command)
                    continue
                result = fn(*a, **kw)
                if command.startswith("r_"):  # Things that return values
                    self.result_queue.put(result)
        except Empty:
            pass
        rl.EndTextureMode()

    # Below here: things that draw things and whatnot
    def circle(self, x: int, y: int, radius: int, color: Tuple[int, int, int, int]):
        rl.draw_circle(x, y, int(radius), color)

    def load_sound(self, name, path):
        self.sounds[name] = rl.load_sound(path.encode("utf-8"))

    def play_sound(self, name):
        rl.play_sound(self.sounds[name])

    def load_music_stream(self, name, path):
        self.musics[name] = rl.load_music_stream(path.encode("utf-8"))

    def play_music_stream(self, name):
        rl.play_music_stream(self.musics[name])
        self.music_playing = name


reserved = {"update", "key_event"}
exported = [
    fname
    for fname in dir(Server)
    if fname not in reserved and not fname.startswith("__")
]
