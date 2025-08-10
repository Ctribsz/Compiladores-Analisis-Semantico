from dataclasses import dataclass
from typing import List, Optional

class Type:
    name: str
    def __str__(self): return self.name
    def __repr__(self): return self.name
    def is_same(self, other: "Type") -> bool: return self.name == other.name

class IntegerType(Type): name = "integer"
class StringType(Type):  name = "string"
class BooleanType(Type): name = "boolean"
class NullType(Type):    name = "null"

@dataclass(frozen=True)
class ArrayType(Type):
    elem: Type
    @property
    def name(self): return f"{self.elem.name}[]"

@dataclass(frozen=True)
class ClassType(Type):
    class_name: str
    @property
    def name(self): return self.class_name

@dataclass(frozen=True)
class FunctionType(Type):
    params: List[Type]
    ret: Type
    @property
    def name(self): 
        p = ", ".join(t.name for t in self.params)
        return f"({p}) -> {self.ret.name}"

# singletons
INTEGER = IntegerType()
STRING  = StringType()
BOOLEAN = BooleanType()
NULL    = NullType()
