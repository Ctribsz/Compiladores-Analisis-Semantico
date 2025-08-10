from typing import List, Optional
from antlr4 import ParserRuleContext, TerminalNode

from .errors import ErrorCollector
from .symbols import VariableSymbol, FunctionSymbol, ClassSymbol
from .types import (
    Type, INTEGER, STRING, BOOLEAN, NULL,
    ArrayType, ClassType, FunctionType
)
from .scope import Scope

from program.gen.CompiscriptVisitor import CompiscriptVisitor
from program.gen.CompiscriptParser import CompiscriptParser

# -----------------------------
# Helpers de tipos
# -----------------------------
def _base_type_from_text(t: str) -> Type:
    t = t.strip()
    if t == "integer": return INTEGER
    if t == "string":  return STRING
    if t == "boolean": return BOOLEAN
    if t == "null":    return NULL
    return ClassType(t)

def _type_from_rule_text(text: str) -> Type:
    # Soporta T, T[], T[][], etc.
    base = text
    dims = 0
    while base.endswith("[]"):
        dims += 1
        base = base[:-2]
    typ: Type = _base_type_from_text(base)
    for _ in range(dims):
        typ = ArrayType(typ)
    return typ

def _first_identifier_text(ctx: ParserRuleContext) -> Optional[str]:
    """Devuelve el texto del primer token Identifier que encuentre en ctx."""
    try:
        tok = ctx.getToken(CompiscriptParser.Identifier, 0)
        return tok.getText() if tok else None
    except Exception:
        pass
    for ch in ctx.getChildren():
        if isinstance(ch, TerminalNode) and getattr(ch.symbol, "type", None) == CompiscriptParser.Identifier:
            return ch.getText()
    return None

class SymbolCollector(CompiscriptVisitor):
    """
    Pass 1: declara símbolos (variables, funciones, clases) en el ScopeStack.
    Nota: aún sin overrides específicos porque dependen de nombres de reglas.
    """
    def __init__(self, errors: ErrorCollector):
        self.errors = errors
        self.global_scope = Scope(None)
        self.current = self.global_scope
        self.scopes_by_ctx = {}

    # Por ahora, default: solo recorre
    def visitChildren(self, node):
        result = None
        n = node.getChildCount()
        for i in range(n):
            c = node.getChild(i)
            result = c.accept(self)
        return result

class TypeCheckerVisitor(CompiscriptVisitor):
    """
    Pass 2: verifica tipos/uso de identificadores.
    """
    def __init__(self, errors: ErrorCollector, root_scope: Scope, scopes_by_ctx: dict):
        self.errors = errors
        self.current = root_scope
        self.scopes_by_ctx = scopes_by_ctx

    def visitChildren(self, node):
        result = None
        n = node.getChildCount()
        for i in range(n):
            c = node.getChild(i)
            result = c.accept(self)
        return result

def run_semantic(tree) -> ErrorCollect	or:
    errors = ErrorCollector()
    p1 = SymbolCollector(errors); p1.visit(tree)
    p2 = TypeCheckerVisitor(errors, p1.global_scope, p1.scopes_by_ctx); p2.visit(tree)
    return errors
