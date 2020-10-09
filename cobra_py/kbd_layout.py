import subprocess

_special_keys = {
    # Keysym : (plain, shifted)
    "0xff51": (b"\x1b[D", b"\x1b[1;2D"),  # Left
    "0xff52": (b"\x1b[A", b"\x1b[1;2A"),  # Up
    "0xff53": (b"\x1b[C", b"\x1b[1;2C"),  # Right
    "0xff54": (b"\x1b[B", b"\x1b[1;2B"),  # Down
}


def _parsed(keysym):
    if len(keysym) < 2:
        return ["", ""]
    if keysym[1] in _special_keys:
        return _special_keys[keysym[1]]

    elif keysym[1].startswith("0x00"):  # Ordinary key
        plain = chr(int(keysym[1], 16)).encode("utf8")
        shifted = chr(int(keysym[3], 16)).encode("utf8")
        alt_gr = chr(int(keysym[9], 16)).encode("utf8") if len(keysym) >= 10 else b""
        alt_gr_shifted = (
            chr(int(keysym[11], 16)).encode("utf8") if len(keysym) >= 12 else b""
        )
        return (plain, shifted, alt_gr, alt_gr_shifted)

    # Who knows
    return (keysym[2].encode("utf8"), keysym[4].encode("utf8"))


def read_xmodmap():
    """Use xmodmap to figure out what key does what.

    Returns a map KeyCode -> KeySyms

    The KeySyms are:

    plain shift whoknows what else

    The KeyCode matches glfw's

    """

    keys = {}

    data = subprocess.check_output("xmodmap -pk".split(), encoding="utf-8")
    for line in data.splitlines()[5:]:
        keysyms = line.split()

        keys[int(keysyms[0])] = _parsed(keysyms)
    return keys


read_xmodmap()
