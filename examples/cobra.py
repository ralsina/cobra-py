#!/usr/bin/env python

from multiprocessing import Process

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
        if self.child is not None:
            self.child.kill()
            self.child = None

        user_code = open("foo.py").read()

        # TODO: analyze user_code

        program = f"""
from cobra_py.graphics_client import *
import time

{user_code}

while True:
    t1 = time.time()
    gameloop()
    t2 = time.time()
    delta = t2 - t1
    if delta < 1 / 60:
        time.sleep(1 / 60 - delta)
        """

        with open("bar.py", "w+") as outf:
            outf.write(program)

        def run():
            import bar  # noqa: F401

        self.child = Process(target=run)
        self.child.start()

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
            self.child = None

    def show_editor(self):
        for layer in self.layers:
            layer.enabled = False
        self.editor.enabled = True
        if self.child:
            self.child.kill()
            self.child = None

    def show_graphics(self):
        for layer in self.layers:
            layer.enabled = False
        self.graphics.enabled = True
        self.run_program()


def main():
    cobra = Cobrapy()
    cobra.run()


if __name__ == "__main__":
    main()
