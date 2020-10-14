# type: ignore
"""A wrapper to the raylib CFFI binding so that names are snake_case instead of CamelCase"""

import inspect
import re
from pathlib import Path
from types import BuiltinFunctionType

import cobra_py.raylib.lib as rl
from cobra_py.raylib import ffi


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


# In this file we **have** to use the CamelCase raylib identifiers, c'est la vie.

# Doesn't work with CFFI functions (yet!) but hey, it's an idea
def wrap_bytes(f):
    try:
        sig = inspect.signature(f)
    except ValueError:
        return f
    byte_args = [
        i for i, p in enumerate(sig.parameters) if sig.parameters[p].annotation == bytes
    ]

    def g(*a):
        _a = list(a)
        for i in byte_args:
            _a[i] = _a[i].encode("utf-8")
        f(*a)

    return g


for name, value in inspect.getmembers(rl):
    if isinstance(value, BuiltinFunctionType):
        locals()[camel_to_snake(name)] = wrap_bytes(value)
    locals()[name] = value


class Screen:
    """A screen.

    It takes a number of buffers and will compose them in order and display them.
    Also, it has an "event loop" that will make all buffers update and display.
    """

    show_fps = True
    ctrl = False
    shift = False
    alt = False
    altgr = False

    def __init__(self, width, height):
        self.width = width
        self.height = height
        rl.InitWindow(width, height, b"CobraPy")
        font_path = str(
            Path(__file__).parent / "resources" / "fonts" / "monoid.ttf"
        ).encode("utf-8")
        self.font = rl.LoadFontEx(font_path, 24, ffi.NULL, 256)
        self.text_size = rl.MeasureTextEx(self.font, b"X", self.font.baseSize, 0)
        rl.SetTargetFPS(60)

        # Hook into key events
        self.__cb = ffi.callback("void(int,int,int,int)")(lambda *a: self.key_event(*a))
        rl.SetKeyCallback(self.__cb)

        self.layers = []

    def add_layer(self, layer):
        self.layers.append(layer)

    def update(self):
        for layer in self.layers:
            layer.update()

    def run(self):
        while not rl.WindowShouldClose():
            self.update()
            rl.BeginDrawing()
            rl.ClearBackground(rl.BLACK)

            # Draw all layers
            for layer in self.layers:
                rl.DrawTextureRec(
                    layer.texture.texture,
                    (
                        0,
                        0,
                        layer.texture.texture.width,
                        -layer.texture.texture.height,
                    ),
                    (0, 0),
                    rl.WHITE,
                )
            if self.show_fps:
                rl.DrawFPS(10, 10)
            rl.EndDrawing()

    def key_event(self, key, scancode, action, mods):
        """Process one keyboard event.

        :key: as in glfw
        :scancode: as in glfw
        :action: as in glfw (X11 KeyCode)
        :mods: 0 is key release, 1 key press, 2 key repeat
        """
        # FIXME: cook the event more (specifically action)

        if mods == 0:  # Key release
            # FIXME: get mod codes from xmodmap
            if action in {37, 105}:  # ctrl
                self.ctrl = False
            elif action in {50, 62}:  # shift
                self.shift = False
            elif action == 64:  # Alt
                self.alt = False
            elif action == 108:  # AltGr
                self.alt_gr = False
            return

        # Key press (mods=1) or repeat (mods=2)

        # Modifiers
        if action in {37, 105}:
            self.ctrl = True
        elif action in {50, 62}:
            self.shift = True
        elif action == 64:  # Alt
            self.alt = True
        elif action == 108:  # AltGr
            self.alt_gr = True

        for layer in self.layers:
            layer.key_event(
                action,
                mods,
                ctrl=self.ctrl,
                shift=self.shift,
                alt=self.alt,
                altgr=self.altgr,
            )


class Layer:
    """A class for 'things that draw in a buffer'

    Screen will compose these and display them.
    """

    def __init__(self, screen: Screen):
        screen.add_layer(self)
        self.texture = rl.LoadRenderTexture(screen.width, screen.height)
        self._screen = screen
        rl.BeginTextureMode(self.texture)
        rl.ClearBackground((0, 0, 0, 0))
        rl.EndTextureMode()

    def update(self):
        """Update the contents of self.buffer as needed.

        Try not to take too long.
        """
        pass

    def key_event(
        self,
        action: int,
        mods: int,
        ctrl: bool,
        shift: bool,
        alt: bool,
        altgr: bool,
    ):
        """Keyboard event forwarded from the Screen.

        :action: code identifying the key
        :mods: 0 is key release, 1 key press, 2 key repeat
        :ctrl: whether the Ctrl key is pressed
        :shift: whether the Shift key is pressed
        :alt: whether the Alt key is pressed
        :altgr: whether the AltGr key is pressed


        Implement as needed on each layer.
        """
        pass
