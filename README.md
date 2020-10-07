Nothing to see here yet, but maybe read [this](https://ralsina.me/weblog/posts/possible-new-project.html)


If you really, really, really want to try this out while it doesn't work:

* In a venv
* poetry install
* python -m cobra_py
* *stuff* may or may not happen

---

This has grown a [raylib](https://raylib.com) CFFI wrapper ... example:

```python
from cobra_py import rl

sw = 800
sh = 450

# Same as the raylib example, just using snake_case instead of CamelCase for functions
rl.init_window(sw, sh, b"Example")
rl.set_target_fps(60)
while not rl.window_should_close():
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)
    rl.draw_text(
        b"Congrats! You created your first window!",
        190,
        200,
        20,
        rl.RED,
    )
    rl.end_drawing()
# Actually you can still use CamelCase, be free
rl.CloseWindow()
```

<img src="https://i.imgur.com/54SSJqp.png">
