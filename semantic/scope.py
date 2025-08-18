from typing import Dict, Any, Optional
from .symbols import Symbol, VariableSymbol, FunctionSymbol, ClassSymbol
from .types import Type, FunctionType

class Scope:
    def __init__(self, parent: Optional["Scope"]=None, name: str = "global"):
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        # opcional: nombre visible del scope
        self.name = name

    def define(self, sym: Symbol) -> bool:
        if sym.name in self.symbols:
            return False
        self.symbols[sym.name] = sym
        return True

    def resolve(self, name: str) -> Optional[Symbol]:
        cur = self
        while cur:
            if name in cur.symbols:
                return cur.symbols[name]
            cur = cur.parent
        return None


def _type_str(t: Optional[Type]) -> Optional[str]:
    return str(t) if t is not None else None

def serialize_symbol(sym: Symbol) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "name": getattr(sym, "name", None),
        "kind": sym.__class__.__name__,
        "type": _type_str(getattr(sym, "typ", None)),  # <-- usa .typ
    }

    if isinstance(sym, VariableSymbol):
        d["is_const"] = getattr(sym, "is_const", False)
        d["initialized"] = getattr(sym, "initialized", False)

    if isinstance(sym, FunctionSymbol):
        d["params"] = [
            {"name": getattr(p, "name", None), "type": _type_str(getattr(p, "typ", None))}
            for p in (getattr(sym, "params", []) or [])
        ]
        ftype = getattr(sym, "typ", None)
        if isinstance(ftype, FunctionType):
            d["return_type"] = _type_str(ftype.ret)

    if isinstance(sym, ClassSymbol):
        fields = getattr(sym, "fields", {}) or {}
        d["fields"] = [
            {"name": fname, "kind": "Field", "type": _type_str(ftype)}
            for fname, ftype in fields.items()
        ]
        methods = getattr(sym, "methods", {}) or {}
        d["methods"] = []
        for mname, mtype in methods.items():
            item = {"name": mname, "kind": "Method", "type": _type_str(mtype)}
            if isinstance(mtype, FunctionType):
                item["params"] = [_type_str(t) for t in (mtype.params or [])]
                item["return_type"] = _type_str(mtype.ret)
            d["methods"].append(item)
    return d

def serialize_scope(scope: "Scope") -> Dict[str, Any]:
    return {
        "scope_name": getattr(scope, "name", "global"),
        "symbols": [serialize_symbol(s) for s in scope.symbols.values()],
        "children": [],  # si luego agregas sub-scopes, rellénalos aquí
    }
