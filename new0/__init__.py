# ruff: noqa: PLC0415
from __future__ import annotations, barry_as_FLUFL

import os
import site
import sys
from _pyrepl.console import InteractiveColoredConsole  # type: ignore[import-not-found]
from typing import TYPE_CHECKING

from new0.compat import Python0API, run_code_string

if TYPE_CHECKING:
    from _typeshed import StrPath


def can_use_pyrepl() -> bool:
    flag = True
    if not os.getenv("PYTHON_BASIC_REPL"):
        from _pyrepl.main import CAN_USE_PYREPL  # type: ignore[import-not-found]

        flag = CAN_USE_PYREPL
    return flag


def run_console(console: Python0Console) -> None:
    sys.audit("cpython.run_stdin")
    interactive_hook = getattr(sys, "__interactivehook__", None)

    if interactive_hook is not None:
        sys.audit("cpython.run_interactivehook", interactive_hook)
        interactive_hook()

    if interactive_hook is site.register_readline:
        # TODO(bswck): Adapt for Python 0.9.1
        try:
            import rlcompleter
        except BaseException:  # noqa: S110,BLE001
            pass
        else:
            try:
                import readline
            except ImportError:
                pass
            else:
                completer = rlcompleter.Completer(console.locals)
                readline.set_completer(completer.complete)

    if can_use_pyrepl():
        from _pyrepl.simple_interact import (  # type: ignore[import-not-found]
            run_multiline_interactive_console,
        )

        console.api.initall()
        run_multiline_interactive_console(
            console,
            future_flags=barry_as_FLUFL.compiler_flag,  # for if 1 <> 2: syntax
        )
    else:
        console.interact(
            banner="new0, a modern Python 0.9.1 interactive console",
            exitmsg="Exiting new0, a modern Python 0.9.1 console.",
        )


class Python0Console(InteractiveColoredConsole):  # type: ignore[misc]
    def __init__(
        self,
        locals: dict[str, object] | None = None,  # noqa: A002
        *,
        lib_path: StrPath | None = None,
    ) -> None:
        if lib_path is None:
            lib_path = os.environ.get("PYTHON0_LIB", None)
            if lib_path is None:
                msg = (
                    "Pass lib_path to Python0Console or set "
                    "the PYTHON0_LIB environment variable."
                )
                raise ValueError(msg)

        self.api = Python0API(os.fspath(lib_path))
        super().__init__(
            locals, filename="<stdin>"
        )  # TODO(bswck): Propagate locals to the REPL

    def runsource(
        self,
        source: str,
        filename: str = "<input>",
        symbol: str = "single",  # TODO(bswck): Handle this parameter?  # noqa: ARG002
    ) -> None:
        if not source.endswith("\n"):
            source += "\n"
        run_code_string(self.api, source, filename)
