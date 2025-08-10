from dataclasses import dataclass
from typing import Optional, List
from .types import Type

@dataclass
class Symbol:
    name: str
    typ: Type

@dataclass
class VariableSymbol(Symbol):
    is_const: bool = False
    initialized: bool = False

@dataclass
class FunctionSymbol(Symbol):
    params: List[Symbol] = None  # symbols de parámetros

@dataclass
class ClassSymbol(Symbol):
    base: Optional["ClassSymbol"] = None
    fields: dict = None
    methods: dict = None
