#!/usr/bin/env python

import subprocess

from cobra_py.graphics_server import Server
from cobra_py.rl import Screen
from cobra_py.terminal import Terminal


class Cobrapy(Screen):
    def __init__(self):
        super().__init__(800, 600)
        self.term = Terminal(self, cmd="sweepleg", enabled=False)
        self.graphics = Server(self, enabled=False)
        self.editor = Terminal(self, cmd="micro foo.py", enabled=False)
        self.child = None
        self.show_prompt()

    def run_program(self):
        """Execute our one and only program, which is being edited."""
        # FIXME: run it with graphics_client imported
        self.child = subprocess.Popen(["python", "foo.py"])

    def key_event(self, key, scancode, action, mods):
        "Eat F1 / F2 / F3 to switch modes, pass the rest down"

        if action == 67:  # F1
            self.show_prompt()
            return
        elif action == 68:  # F2
            self.show_editor()
            return
        elif action == 69:  # F2
            self.show_graphics()
            return

        super().key_event(key, scancode, action, mods)

    def show_prompt(self):
        for layer in self.layers:
            layer.enabled = False
        self.term.enabled = True
        self.graphics.enabled = True
        if self.child:
            self.child.kill()

    def show_editor(self):
        for layer in self.layers:
            layer.enabled = False
        self.editor.enabled = True
        if self.child:
            self.child.kill()

    def show_graphics(self):
        for layer in self.layers:
            layer.enabled = False
        self.graphics.enabled = True
        # self.run_program()


def main():
    cobra = Cobrapy()
    cobra.run()


if __name__ == "__main__":
    main()
