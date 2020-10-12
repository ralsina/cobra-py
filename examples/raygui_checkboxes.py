#!/usr/bin/env python
from cobra_py import rl

sw = 800
sh = 450

rl.init_window(sw, sh, b"CheckBoxes")
rl.set_target_fps(60)
cb = 1

while not rl.window_should_close():
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)
    cb = rl.gui_check_box((300, 300, 20, 20), b"Foo", cb)
    rl.draw_fps(10, 10)
    rl.end_drawing()
rl.close_window()
