from dataclasses import dataclass
from typing import Any

from cobra_py import rl


@dataclass
class Sprite:
    name: str
    x: int = 200
    y: int = 200
    texture: Any = None


class SpriteLayer(rl.Layer):
    """A layer for named sprites.

    Sprites have image, size, position, rotation and so on.
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self.sprites = {}

    def load_sprite(self, name: str, image: bytes):
        """Load image, create a sprite, call it name.

        If the name is already in use, then the new image is loaded in that sprite.

        TODO: think about animation and whatnot

        :name: Name of the sprite.
        :image: Path to the image to display.
        """
        texture = rl.load_texture(image)
        self.sprites[name] = Sprite(name=name, texture=texture)

    def update(self):
        rl.begin_texture_mode(self.texture)
        rl.clear_background((0, 0, 0, 0))
        for sprite in self.sprites.values():
            rl.draw_texture(sprite.texture, sprite.x, sprite.y, rl.WHITE)

        rl.end_texture_mode()
