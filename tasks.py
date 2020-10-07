import cffi
import pathlib
from invoke import task


@task
def bind_raylib(c):
    print("Building CFFI")
    ffi = cffi.FFI()
    includes = pathlib.Path().absolute() / "includes"
    h_file =  includes / "raylib.h"
    with open(h_file) as inf:
        ffi.cdef(inf.read())
    ffi.set_source(
        "cobra_py.raylib",
        '#include "raylib.h"',
        libraries=["raylib"],
        extra_link_args=["-Wl,-rpath,."],
    )
    ffi.compile()
