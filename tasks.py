import os
import pathlib

import cffi
from invoke import task


@task
def checkout_raylib(c):
    if os.path.isdir("raylib"):
        return
    c.run("git clone https://github.com/raysan5/raylib.git")
    with c.cd("raylib"):
        c.run("git checkout 3.0.0")
        c.run("patch -p1 < ../raylib.patch")


@task
def build_raylib(c):
    with c.cd("raylib/src"):
        c.run("make clean")
        c.run("make PLATFORM=PLATFORM_DESKTOP")


@task
def check(c):
    print("Formatting")
    c.run("isort .")
    c.run("black .")
    c.run("flake8 .")


@task(build_raylib)
def bind_raylib(c):
    print("Building raylib CFFI")
    ffi = cffi.FFI()
    includes = pathlib.Path().absolute() / "include"
    lib_dir = pathlib.Path().absolute() / "raylib" / "src"
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
        libraries=["raylib", "X11"],
        library_dirs=[lib_dir.as_posix()],
        extra_link_args=["-Wl,-rpath,."],
        include_dirs=[includes, lib_dir],
    )
    ffi.compile()
