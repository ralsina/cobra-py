"""A simple python REPL with a few extras:

* Support for some non-python "commands"
* Based on prompt_toolkiot, so editing is like ptpython.
* More "normal" keybindings.
"""

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers import PythonLexer

from cobra_py.prompt_utils import document_is_multiline_python

bindings = KeyBindings()


@bindings.add("enter")
def _(event):
    b = event.current_buffer
    if document_is_multiline_python(b.document) and not b.document.text.endswith("\n"):
        b.insert_text("\n")
    else:
        b.validate_and_handle()


_globals = {}
_locals = {}


def _execute(line: str) -> None:
    try:
        code = compile(line, "INPUT", "eval")
        result = eval(code, _globals, _locals)
        print("-->", result)
    except SyntaxError:  # Not an expression
        code = compile(line, "INPUT", "exec")
        exec(code, _globals, _locals)


def run():
    session = PromptSession(
        lexer=PygmentsLexer(PythonLexer),
        key_bindings=bindings,
        prompt_continuation="... ",
    )
    while True:
        try:
            text = session.prompt(">>> ")
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            _execute(text)
    print("EOF")


if __name__ == "__main__":
    run()
