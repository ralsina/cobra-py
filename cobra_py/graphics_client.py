"""Client for the CobraPy graphics protocol."""

import threading
from functools import partial

from ipcqueue.posixmq import Queue

from cobra_py import graphics_server

__command_queue = Queue("/foo")
__event_queue = Queue("/bar")

input_status = {}
input_lock = threading.Lock()


def _event_picker():
    global input_status
    while True:
        event = __event_queue.get()
        input_lock.acquire()
        input_status = {"last_event": event}
        input_lock.release()


def get_status():
    input_lock.acquire()
    r = input_status.copy()
    input_lock.release()
    return r


def __command(cmdname, *a, **kw):
    __command_queue.put((cmdname, a, kw))


functions = {"get_status": get_status}

# Create a local proxy for each thing exported by the server
for endpoint in graphics_server.exported:
    client = partial(__command, endpoint)
    locals()[endpoint] = client
    functions[endpoint] = client

t = threading.Thread(target=_event_picker)
t.start()
