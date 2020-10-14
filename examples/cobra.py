#!/usr/bin/env python

from cobra_py.graphics_server import Server
from cobra_py.rl import Screen
from cobra_py.terminal import Terminal


class Cobrapy(Screen):
    def __init__(self):
        super().__init__(800, 600)
        self.term = Terminal(self, cmd="sweepleg")
        self.graphics = Server(self)

        self.editor = Terminal(self, cmd="micro tasks.py", enabled=False)


def main():
    cobra = Cobrapy()
    cobra.run()


if __name__ == "__main__":
    main()
