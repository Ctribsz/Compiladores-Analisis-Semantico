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

# =============================
# PASS 1: Recolector de símbolos
# =============================
class SymbolCollector(CompiscriptVisitor):
    def __init__(self, errors: ErrorCollector):
        self.errors = errors
        self.global_scope = Scope(None)
        self.current = self.global_scope
        self.scopes_by_ctx = {}

    def _bind_scope(self, ctx: ParserRuleContext, scope: Scope):
        self.scopes_by_ctx[ctx] = scope
        setattr(ctx, "scope", scope)

    def _enter_child_scope(self, ctx: ParserRuleContext):
        child = Scope(self.current)
        self._bind_scope(ctx, child)
        self.current = child

    def _exit_scope(self):
        if self.current.parent:
            self.current = self.current.parent

    # program: statement* EOF;
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        # enlazamos el scope global al program para que Pass2 pueda entrar
        self._bind_scope(ctx, self.global_scope)
        return self.visitChildren(ctx)

    # block: '{' statement* '}';
    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self._enter_child_scope(ctx)
        r = self.visitChildren(ctx)
        self._exit_scope()
        return r

    # variableDeclaration: ('let'|'var') Identifier typeAnnotation? initializer? ';'
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = _first_identifier_text(ctx)
        decl_type = NULL
        if ctx.typeAnnotation():
            decl_type = self.visit(ctx.typeAnnotation())  # -> Type
        sym = VariableSymbol(name=name, typ=decl_type, is_const=False, initialized=False)
        if not self.current.define(sym):
            self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Redeclaración de '{name}'.")
        return None

    # constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';'
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = _first_identifier_text(ctx)
        decl_type = NULL
        if ctx.typeAnnotation():
            decl_type = self.visit(ctx.typeAnnotation())
        sym = VariableSymbol(name=name, typ=decl_type, is_const=True, initialized=False)
        if not self.current.define(sym):
            self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Redeclaración de '{name}'.")
        return None

    # typeAnnotation: ':' type;
    def visitTypeAnnotation(self, ctx: CompiscriptParser.TypeAnnotationContext):
        tctx = ctx.type_()   # ¡ojo!: type_() en Python
        return self.visit(tctx) if tctx else NULL

    # type: baseType ('[' ']')*;
    def visitType(self, ctx: CompiscriptParser.TypeContext):
        return _type_from_rule_text(ctx.getText())

    # baseType: 'boolean' | 'integer' | 'string' | Identifier;
    def visitBaseType(self, ctx: CompiscriptParser.BaseTypeContext):
        return _base_type_from_text(ctx.getText())

    # functionDeclaration: 'function' Identifier '(' parameters? ')' (':' type)? block;
    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        fname = _first_identifier_text(ctx)
        params_syms: List[VariableSymbol] = []
        if ctx.parameters():
            params_syms = self.visit(ctx.parameters())  # -> List[VariableSymbol]
        ret_type = self.visit(ctx.type_()) if ctx.type_() else NULL

        ftype = FunctionType(params=[p.typ for p in params_syms], ret=ret_type)
        fsym = FunctionSymbol(name=fname, typ=ftype, params=params_syms)
        if not self.current.define(fsym):
            self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Redeclaración de función '{fname}'.")

        # scope de función
        self._enter_child_scope(ctx)
        for p in params_syms:
            if not self.current.define(p):
                self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Parámetro duplicado '{p.name}'.")
        # visitar cuerpo
        self.visit(ctx.block())
        self._exit_scope()
        return None

    # parameters: parameter (',' parameter)* ;
    def visitParameters(self, ctx: CompiscriptParser.ParametersContext):
        return [self.visit(p) for p in ctx.parameter()]

    # parameter: Identifier (':' type)?;
    def visitParameter(self, ctx: CompiscriptParser.ParameterContext):
        pname = _first_identifier_text(ctx)
        ptype = self.visit(ctx.type_()) if ctx.type_() else NULL
        return VariableSymbol(name=pname, typ=ptype, is_const=False, initialized=True)

    # classDeclaration: 'class' Identifier (':' Identifier)? '{' classMember* '}'
    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        cname = _first_identifier_text(ctx)
        csym = ClassSymbol(name=cname, typ=ClassType(cname), fields={}, methods={})
        if not self.current.define(csym):
            self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Redeclaración de clase '{cname}'.")
        # (Opcional) scope de clase; por ahora solo recorremos miembros
        self._enter_child_scope(ctx)
        self.visitChildren(ctx)
        self._exit_scope()
        return None


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
