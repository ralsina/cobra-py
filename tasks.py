import pathlib

import cffi
from invoke import task


@task
def bind_raylib(c):
    print("Building raylib CFFI")
    ffi = cffi.FFI()
    includes = pathlib.Path().absolute() / "include"
    h_file = includes / "_raylib.h"
    with open(h_file) as inf:
        ffi.cdef(inf.read())
    ffi.set_source(
        "cobra_py.raylib",
        """
            #define RAYGUI_IMPLEMENTATION
            #define RAYGUI_SUPPORT_ICONS
            #include "raylib.h"
            #include "raygui.h"
        """,
        libraries=["raylib"],
        extra_link_args=["-Wl,-rpath,."],
        include_dirs=[includes],
    )
    ffi.compile()


@task
def check(c):
    print("Formatting")
    c.run("isort --recursive .")
    c.run("black .")
