from dataclasses import dataclass
from typing import Optional, List
from .types import Type

@dataclass
class Symbol:
    name: str
    typ: Type
    offset: Optional[int] = None  # ← NUEVO

@dataclass
class VariableSymbol(Symbol):
    is_const: bool = False
    initialized: bool = False

@dataclass
class FunctionSymbol(Symbol):
    params: List[Symbol] = None
    label: Optional[str] = None      # ← NUEVO
    params_size: int = 0             # ← NUEVO
    locals_size: int = 0             # ← NUEVO
    frame_size: int = 0              # ← NUEVO

@dataclass
class ClassSymbol(Symbol):
    base: Optional["ClassSymbol"] = None
    fields: dict = None
    methods: dict = None
    instance_size: int = 0           