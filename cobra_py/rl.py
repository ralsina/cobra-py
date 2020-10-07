"""A wrapper to the raylib CFFI binding so that names are snake_case instead of CamelCase"""

import cobra_py.raylib.lib as rl
import inspect
import re
from types import BuiltinFunctionType


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


# Doesn't work with CFFI functions (yet!) but hey, it's an idea
def wrap_bytes(f):
    try:
        sig = inspect.signature(f)
    except ValueError:
        return f
    byte_args = [
        i for i, p in enumerate(sig.parameters) if sig.parameters[p].annotation == bytes
    ]

    def g(*a):
        _a = list(a)
        for i in byte_args:
            _a[i] = _a[i].encode("utf-8")
        f(*a)

    return g


for name, value in inspect.getmembers(rl):
    if isinstance(value, BuiltinFunctionType):
        locals()[camel_to_snake(name)] = wrap_bytes(value)
    locals()[name] = value
