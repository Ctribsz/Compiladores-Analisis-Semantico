# semantic/scope.py
from typing import Optional, Dict, Any, List
from .symbols import Symbol

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


# -------- NUEVO: serialización simple (global + símbolos) --------
def serialize_symbol(sym: Symbol) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "name": getattr(sym, "name", None),
        "kind": sym.__class__.__name__,
    }
    # intenta obtener tipo como string
    t = getattr(sym, "type", None) or getattr(sym, "symbol_type", None)
    d["type"] = str(t) if t is not None else None

    # funciones: params/return si están disponibles
    params = getattr(sym, "params", None) or getattr(getattr(sym, "type", None), "params", None)
    if params:
        d["params"] = [
            {
                "name": getattr(p, "name", None),
                "type": str(getattr(p, "type", None) or getattr(p, "symbol_type", None)),
            }
            for p in params
        ]
    ret_t = getattr(sym, "return_type", None) or getattr(getattr(sym, "type", None), "return_type", None)
    if ret_t is not None:
        d["return_type"] = str(ret_t)

    # clases: fields/methods si existen
    fields = getattr(sym, "fields", None)
    if isinstance(fields, dict) and fields:
        d["fields"] = [serialize_symbol(s) for s in fields.values()]
    methods = getattr(sym, "methods", None)
    if isinstance(methods, dict) and methods:
        d["methods"] = [serialize_symbol(s) for s in methods.values()]

    return d


def serialize_scope(scope: "Scope") -> Dict[str, Any]:
    data = {
        "scope_name": getattr(scope, "name", "global"),
        "symbols": [serialize_symbol(s) for s in scope.symbols.values()],
        # placeholder por si luego agregamos hijos
        "children": [],
    }
    return data
