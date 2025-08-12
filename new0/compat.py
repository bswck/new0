from __future__ import annotations

import ctypes
from functools import cached_property
from typing import ClassVar, Final


def decref(op: ctypes._Pointer[PyObject]) -> None:
    if op:
        op.contents.ob_refcnt -= 1
        if (
            op.contents.ob_refcnt <= 0
            and op.contents.ob_type
            and op.contents.ob_type.contents.tp_dealloc
        ):
            op.contents.ob_type.contents.tp_dealloc(
                ctypes.cast(op, ctypes.POINTER(ctypes.c_void_p))
            )


class PyObject(ctypes.Structure):
    _fields_: ClassVar = [("ob_refcnt", ctypes.c_int), ("ob_type", ctypes.c_void_p)]


class Python0API(ctypes.CDLL):
    """A ctypes wrapper for the Python 0.9.1 shared library."""

    E_DONE: Final = 16

    @cached_property
    def dict(self) -> ctypes.c_void_p:
        main = self.add_module(b"__main__")
        return self.getmoduledict(main)


def run_code_string(
    python0: Python0API,
    source: str,
    filename: str = "<string>",
) -> None:
    """Parse and execute a Python 0.9.1 code string."""
    node = ctypes.c_void_p()
    err: int = python0.parse_string(source.encode("utf-8"), 256, ctypes.byref(node))

    if err != python0.E_DONE:
        python0.print_error()
        return

    result = python0.eval_node(
        node,
        filename.encode("utf-8"),
        python0.dict,
        python0.dict,
    )

    if not result:
        python0.print_error()
        decref(ctypes.cast(result, ctypes.POINTER(PyObject)))
        return
