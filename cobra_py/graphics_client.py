"""Client for the CobraPy graphics protocol."""

import threading
from collections import defaultdict
from functools import partial

from ipcqueue.posixmq import Queue

from cobra_py import graphics_server

__command_queue = Queue("/foo")

input_lock = threading.Lock()
__is_pressed = defaultdict(lambda: False)


def _event_picker(q_id: str):
    __event_queue = Queue(q_id)
    global input_status
    try:
        while True:
            event = __event_queue.get()
            input_lock.acquire()
            __is_pressed[event["action"]] = event["mods"] != 0  # 0 is key release
            input_lock.release()
    finally:
        __event_queue.unlink()


def kbd_init(q_id: str):
    t = threading.Thread(target=lambda: _event_picker(q_id), daemon=True)
    t.start()


def is_pressed(key):
    try:
        input_lock.acquire()
        r = __is_pressed[key]
    finally:
        input_lock.release()
    return r


def __command(cmdname, *a, **kw):
    __command_queue.put((cmdname, a, kw))


functions = {"is_pressed": is_pressed}

# Create a local proxy for each thing exported by the server
for endpoint in graphics_server.exported:
    client = partial(__command, endpoint)
    globals()[endpoint] = client
    functions[endpoint] = client
