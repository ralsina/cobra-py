"""Client for the CobraPy graphics protocol."""

from functools import partial

from cobra_py import graphics_server
from ipcqueue.posixmq import Queue

__command_queue = Queue("/foo")


def __command(cmdname, *a, **kw):
    __command_queue.put((cmdname, a, kw))


functions = {}

# Create a local proxy for each thing exported by the server
for endpoint in graphics_server.exported:
    client = partial(__command, endpoint)
    locals()[endpoint] = client
    functions[endpoint] = client
