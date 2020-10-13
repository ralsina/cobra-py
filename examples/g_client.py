#!/usr/bin/env python

from random import randint

from cobra_py import graphics_client as g

# Draw 100K circles of random sizes, positions and colors
for i in range(100000):
    g.circle(
        randint(1, 500),
        randint(1, 500),
        randint(1, 200),
        (randint(1, 255), randint(1, 255), randint(1, 255), randint(1, 255)),
    )
    if not i % 10000:
        print(i)
