#!/usr/bin/env python

from cobra_py.rl import Screen
from cobra_py.terminal import RayTerminal

screen = Screen(800, 600)
term = RayTerminal(screen)
screen.run()
