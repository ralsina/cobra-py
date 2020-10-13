#!/usr/bin/env python

from cobra_py import rl
from cobra_py.graphics_server import Server

screen = rl.Screen(500, 500)
srv = Server(screen)

print("Starting server. You should run g_client.py to see things.")

screen.run()
