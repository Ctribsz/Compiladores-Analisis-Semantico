from antlr4 import ParseTreeVisitor
from typing import Optional
from .errors import ErrorCollector
from .scope import ScopeStack
from .symbols import *
from .types import *

# Importa el visitor generado por ANTLR
from program.gen.CompiscriptVisitor import CompiscriptVisitor

class SymbolCollector(CompiscriptVisitor):
    """
    Pass 1: declara símbolos (variables, funciones, clases) en el ScopeStack.
    Nota: aún sin overrides específicos porque dependen de nombres de reglas.
    """
    def __init__(self, scopes: ScopeStack, errors: ErrorCollector):
        self.scopes = scopes
        self.errors = errors

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
    def __init__(self, scopes: ScopeStack, errors: ErrorCollector):
        self.scopes = scopes
        self.errors = errors

    def visitChildren(self, node):
        result = None
        n = node.getChildCount()
        for i in range(n):
            c = node.getChild(i)
            result = c.accept(self)
        return result

def run_semantic(tree) -> ErrorCollector:
    errors = ErrorCollector()
    scopes = ScopeStack()

    # Pass 1: declarar símbolos
    SymbolCollector(scopes, errors).visit(tree)
    # Pass 2: chequear tipos/uso
    TypeCheckerVisitor(scopes, errors).visit(tree)
    return errors
