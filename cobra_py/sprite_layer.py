from dataclasses import dataclass
from typing import Any

from cobra_py import rl


@dataclass
class Sprite:
    name: str
    x: int = 200
    y: int = 200
    texture: Any = None

    def rect(self):
        if not self.texture:
            return (0, 0, 0, 0)
        return (self.x, self.y, self.texture.width, self.texture.height)


class SpriteLayer(rl.Layer):
    """A layer for named sprites.

    Sprites have image, size, position, rotation and so on.
    """

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self.sprites = {}
        self.textures = {}

    def load_sprite(self, name: str, image: bytes):
        """Load image, create a sprite, call it name.

        If the name is already in use, then the new image is loaded in that sprite.

        TODO: think about animation and whatnot

        :name: Name of the sprite.
        :image: Path to the image to display.
        """
        if image not in self.textures:
            self.textures[image] = rl.load_texture(image)
        self.sprites[name] = Sprite(name=name, texture=self.textures[image])

    def check_collision(self, _s1: str, _s2: str):
        """Check if sprites _s1 and _s2 collide."""
        if _s1 not in self.sprites or _s2 not in self.sprites:
            print("???", _s1, _s2, self.sprites)
            return False
        s1 = self.sprites[_s1]
        s2 = self.sprites[_s2]
        return rl.check_collision_recs(s1.rect(), s2.rect())

    def update(self):
        rl.begin_texture_mode(self.texture)
        rl.clear_background((0, 0, 0, 0))
        for sprite in self.sprites.values():
            rl.draw_texture(sprite.texture, sprite.x, sprite.y, rl.WHITE)

        rl.end_texture_mode()
