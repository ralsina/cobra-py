from pathlib import Path

from cobra_py import rl

screen_width = 800
screen_height = 450

rl.init_window(screen_width, screen_height, b"Shader example")
im_blank = rl.gen_image_color(1024, 1024, rl.BLUE)
texture = rl.load_texture_from_image(im_blank)
rl.unload_image(im_blank)


shader_path = Path(__file__).parent / "resources" / "cubes_panning.fs"
shader = rl.load_shader(rl.ffi.NULL, bytes(shader_path))

time = 0.0
time_loc = rl.get_shader_location(shader, b"uTime")
rl.set_shader_value(shader, time_loc, rl.ffi.new("float*", time), rl.UNIFORM_FLOAT)

rl.set_target_fps(60)

while not rl.window_should_close():
    time = rl.get_time()
    rl.set_shader_value(shader, time_loc, rl.ffi.new("float*", time), rl.UNIFORM_FLOAT)
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)
    rl.begin_shader_mode(shader)
    rl.draw_texture(texture, 0, 0, rl.WHITE)
    rl.end_shader_mode()
    rl.draw_text(
        b"BACKGROUND is PAINTED and ANIMATED on SHADER!", 10, 10, 20, rl.MAROON
    )
    rl.end_drawing()
rl.unload_shader(shader)
rl.close_window()
