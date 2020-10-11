import subprocess

from cobra_py.keysyms import keysyms

_special_keys = {
    # Keysym : (plain, shifted)
    "0xff0d": (b"\n", b"\n"),  # Enter
    "0xff09": (b"\t", b"\x1b[[Z"),  # Tab
    "0xff1b": (b"\x1b", b"\x1b"),  # ESC
    "0xff08": (b"\b", b"\b"),  # Backspace
    "0xffff": (b"\x1b[3~", b"\x1b[3~"),  # Delete
    "0xffbe": (b"\x1bOP", b"\x1b[1;2P"),  # F1
    "0xffbf": (b"\x1bOQ", b"\x1b[1;2Q"),  # F2
    "0xffc0": (b"\x1bOR", b"\x1b[1;2R"),  # F3
    "0xffc1": (b"\x1bOS", b"\x1b[1;2S"),  # F4
    "0xffc2": (b"\x1b[15~", b"\x1b[15;2~"),  # F5
    "0xffc3": (b"\x1b[17~", b"\x1b[17;2~"),  # F6
    "0xffc4": (b"\x1b[18~", b"\x1b[18;2~"),  # F7
    "0xffc5": (b"\x1b[19~", b"\x1b[19;2~"),  # F8
    "0xffc6": (b"\x1b[20~", b"\x1b[20;2~"),  # F9
    "0xffc7": (b"\x1b[21~", b"\x1b[21;2~"),  # F10
    "0xffc8": (b"\x1b[23~", b"\x1b[23;2~"),  # F11
    "0xffc9": (b"\x1b[24~", b"\x1b[24;2~"),  # F12
    "0xff51": (b"\x1b[D", b"\x1b[1;2D"),  # Left
    "0xff52": (b"\x1b[A", b"\x1b[1;2A"),  # Up
    "0xff53": (b"\x1b[C", b"\x1b[1;2C"),  # Right
    "0xff54": (b"\x1b[B", b"\x1b[1;2B"),  # Down
    "0xff50": (b"\x1b[H", b"\x1b[1;2H"),  # Home
    "0xff57": (b"\x1b[F", b"\x1b[1;2F"),  # End
    "0xff55": (b"\x1b[5~", b"\x1b[5;2~"),  # PgUp
    "0xff56": (b"\x1b[6~", b"\x1b[6;2~"),  # PgDn
}


def _parsed(keysym):
    if len(keysym) < 2:
        return ["", ""]
    if keysym[1] in _special_keys:
        return _special_keys[keysym[1]]

    # Make deadkeys undead
    if "dead" in keysym[2].lower():
        keysym = [keysym[0]] + keysym[9:]

    plain = keysyms.get(keysym[1], "").encode("utf-8")
    shifted = keysyms.get(keysym[3], "").encode("utf-8")
    alt_gr = keysyms.get(keysym[9], "").encode("utf-8") if len(keysym) >= 10 else b""
    alt_gr_shifted = (
        keysyms.get(keysym[11], "").encode("utf-8") if len(keysym) >= 12 else b""
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
