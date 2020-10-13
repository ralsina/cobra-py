#!/usr/bin/env python

from cobra_py.graphics_server import Server
from cobra_py.rl import Screen
from cobra_py.terminal import Terminal

screen = Screen(800, 600)
term = Terminal(screen, cmd="sweepleg")
graphics = Server(screen)
screen.run()
