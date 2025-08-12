from __future__ import annotations

import ctypes
from ctypes import POINTER, c_char_p, c_int, c_void_p
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
            op.contents.ob_type.contents.tp_dealloc(ctypes.cast(op, POINTER(c_void_p)))


class PyTypeObject(ctypes.Structure):
    _fields_: ClassVar = [
        ("tp_dealloc", ctypes.CFUNCTYPE(None, POINTER(c_void_p))),
    ]


class PyObject(ctypes.Structure):
    _fields_: ClassVar = [
        ("ob_refcnt", c_int),
        ("ob_type", POINTER(PyTypeObject)),
    ]


class Grammar(ctypes.Structure):
    _fields_: ClassVar = [
        ("g_ndfas", c_int),
        ("g_dfa", POINTER(c_void_p)),
        ("g_labels", c_void_p),
        ("g_start", c_int),
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
        self._parse_string.argtypes = [c_char_p, c_int, POINTER(c_void_p)]
        self._parse_string.restype = c_int
        return self._parse_string

    @cached_property
    def add_module(self) -> ctypes._FuncPointer:
        self._add_module.argtypes = [c_char_p]
        self._add_module.restype = c_void_p
        return self._add_module

    @cached_property
    def getmoduledict(self) -> ctypes._FuncPointer:
        self._getmoduledict.argtypes = [c_void_p]
        self._getmoduledict.restype = c_void_p
        return self._getmoduledict

    @cached_property
    def eval_node(self) -> ctypes._FuncPointer:
        self._eval_node.argtypes = [c_void_p, c_char_p, c_void_p, c_void_p]
        self._eval_node.restype = c_void_p
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
    node = c_void_p()
    err: int = python0.parse_string(source.encode("utf-8"), 256, ctypes.byref(node))

    if err != python0.E_DONE:
        python0.print_error()
        return

    result = python0.eval_node(
        node, filename.encode("utf-8"), python0.dict, python0.dict
    )

    if not result:
        python0.print_error()
        decref(ctypes.cast(result, POINTER(PyObject)))
        return
