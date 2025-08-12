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


class PyTypeObject(ctypes.Structure):
    _fields_: ClassVar = [
        ("tp_dealloc", ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_void_p))),
    ]


class PyObject(ctypes.Structure):
    _fields_: ClassVar = [
        ("ob_refcnt", ctypes.c_int),
        ("ob_type", ctypes.POINTER(PyTypeObject)),
    ]


class Grammar(ctypes.Structure):
    _fields_: ClassVar = [
        ("g_ndfas", ctypes.c_int),
        ("g_dfa", ctypes.POINTER(ctypes.c_void_p)),
        ("g_labels", ctypes.c_void_p),
        ("g_start", ctypes.c_int),
    ]


class Python0API(ctypes.CDLL):
    """A ctypes wrapper for the Python 0.9.1 shared library."""

    E_DONE: Final = 16

    @cached_property
    def gram(self) -> Grammar:
        return Grammar.in_dll(self, "gram")

    @cached_property
    def initall(self) -> ctypes._FuncPointer:
        self._initall.argtypes = []
        self._initall.restype = None
        return self._initall

    @cached_property
    def parse_string(self) -> ctypes._FuncPointer:
        self._parse_string.argtypes = [
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._parse_string.restype = ctypes.c_int
        return self._parse_string

    @cached_property
    def add_module(self) -> ctypes._FuncPointer:
        self._add_module.argtypes = [ctypes.c_char_p]
        self._add_module.restype = ctypes.c_void_p
        return self._add_module

    @cached_property
    def getmoduledict(self) -> ctypes._FuncPointer:
        self._getmoduledict.argtypes = [ctypes.c_void_p]
        self._getmoduledict.restype = ctypes.c_void_p
        return self._getmoduledict

    @cached_property
    def eval_node(self) -> ctypes._FuncPointer:
        self._eval_node.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        self._eval_node.restype = ctypes.c_void_p
        return self._eval_node

    @cached_property
    def print_error(self) -> ctypes._FuncPointer:
        self._print_error.argtypes = []
        self._print_error.restype = None
        return self._print_error

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
        node, filename.encode("utf-8"), python0.dict, python0.dict
    )

    if not result:
        python0.print_error()
        decref(ctypes.cast(result, ctypes.POINTER(PyObject)))
        return
