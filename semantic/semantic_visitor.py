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


# =============================
# PASS 2: Chequeo de tipos/uso
# =============================
class TypeCheckerVisitor(CompiscriptVisitor):
    def __init__(self, errors: ErrorCollector, root_scope: Scope, scopes_by_ctx: dict):
        self.errors = errors
        self.current = root_scope
        self.scopes_by_ctx = scopes_by_ctx

    def _enter_by_ctx(self, ctx: ParserRuleContext):
        s = self.scopes_by_ctx.get(ctx)
        if s: self.current = s

    def _exit(self):
        if self.current.parent: self.current = self.current.parent

    # program / block / function: moverse por scopes ya construidos
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        self._enter_by_ctx(ctx); r = self.visitChildren(ctx); return r

    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        self._enter_by_ctx(ctx); r = self.visitChildren(ctx); self._exit(); return r

    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        self._enter_by_ctx(ctx)
        self.visit(ctx.block())
        self._exit()
        return None

    # variableDeclaration: validar initializer si existe
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = _first_identifier_text(ctx)
        sym = self.current.resolve(name)
        if ctx.initializer():
            itype = self.visit(ctx.initializer())  # -> Type
            if sym and not self._is_assignable(itype, sym.typ):
                self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                   f"No se puede asignar '{itype}' a '{sym.typ}' en inicialización de '{name}'.")
            if sym: sym.initialized = True
        return None

    # constantDeclaration: const debe inicializarse y ser asignable
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = _first_identifier_text(ctx)
        sym = self.current.resolve(name)
        if not ctx.expression():
            self.errors.report(ctx.start.line, ctx.start.column, "E003", f"Constante '{name}' debe inicializarse.")
            return None
        itype = self.visit(ctx.expression())
        if sym and not self._is_assignable(itype, sym.typ):
            self.errors.report(ctx.start.line, ctx.start.column, "E004",
                               f"No se puede asignar '{itype}' a '{sym.typ}' en const '{name}'.")
        if sym: sym.initialized = True
        return None

    # initializer: '=' expression
    def visitInitializer(self, ctx: CompiscriptParser.InitializerContext):
        return self.visit(ctx.expression())

    # assignment (statement):
    #   Identifier '=' expression ';'
    # | expression '.' Identifier '=' expression ';'   (no soportado aún)
    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        # distinguir por número de expressions: 1 = simple, 2 = property
        if len(ctx.expression()) == 1:
            # simple: Identifier '=' expr
            name = _first_identifier_text(ctx)
            rtype = self.visit(ctx.expression(0))
            if name is None:
                self.errors.report(ctx.start.line, ctx.start.column, "E006",
                                   "Asignación inválida (identificador esperado).")
                return NULL
            sym = self.current.resolve(name)
            if not sym:
                self.errors.report(ctx.start.line, ctx.start.column, "E002", f"Identificador no declarado '{name}'.")
                return NULL
            if sym.is_const:
                self.errors.report(ctx.start.line, ctx.start.column, "E005", f"No se puede reasignar const '{name}'.")
                return sym.typ
            if not self._is_assignable(rtype, sym.typ):
                self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                   f"No se puede asignar '{rtype}' a '{sym.typ}'.")
            else:
                sym.initialized = True
            return sym.typ
        else:
            # property assignment aún no implementado
            self.errors.report(ctx.start.line, ctx.start.column, "E006",
                               "Asignación a propiedad no soportada aún.")
            # visitar RHS para seguir tipeando
            self.visit(ctx.expression(1))
            return NULL

    # expressionStatement: expression ';'
    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        self.visit(ctx.expression()); return None

    # ---- Expresiones ----
    def visitExpression(self, ctx: CompiscriptParser.ExpressionContext):
        return self.visitChildren(ctx)

    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        txt = ctx.getText()
        if txt == "true" or txt == "false": return BOOLEAN
        if txt == "null": return NULL
        if len(txt) >= 2 and ((txt[0] == '"' and txt[-1] == '"') or (txt[0] == "'" and txt[-1] == "'")):
            return STRING
        if txt.lstrip("-").isdigit(): return INTEGER
        return NULL

    # primaryExpr: literalExpr | leftHandSide | '(' expression ')'
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        for ch in ctx.getChildren():
            return ch.accept(self)
        return NULL

    # leftHandSide: primaryAtom (suffixOp)* ;
    # Por ahora solo soportamos primaryAtom sin sufijos
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        return self.visit(ctx.primaryAtom())

    # primaryAtom:
    #   Identifier           # IdentifierExpr
    # | 'new' Identifier...  # NewExpr
    # | 'this'               # ThisExpr
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        name = ctx.Identifier().getText()
        sym = self.current.resolve(name)
        if not sym:
            self.errors.report(ctx.start.line, ctx.start.column, "E002", f"Identificador no declarado '{name}'.")
            return NULL
        return sym.typ

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        cname = ctx.Identifier().getText()
        # En el futuro: validar existencia de la clase y constructor
        return ClassType(cname)

    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        # Para ahora devolvemos NULL; luego lo ligamos al tipo de clase actual
        return NULL

    # arrayLiteral: '[' (expression (',' expression)*)? ']'
    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        exprs = ctx.expression()
        if not exprs:
            return ArrayType(NULL)
        t0 = self.visit(exprs[0])
        for e in exprs[1:]:
            ti = self.visit(e)
            if t0.name != ti.name:
                self.errors.report(ctx.start.line, ctx.start.column, "E011",
                                   f"Elementos de arreglo deben tener mismo tipo: {t0} vs {ti}.")
        return ArrayType(t0)

    # logical OR/AND
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        n = len(ctx.logicalAndExpr())
        if n == 1:
            return ctx.logicalAndExpr(0).accept(self)
        for i in range(n):
            t = ctx.logicalAndExpr(i).accept(self)
            if t != BOOLEAN:
                self._op_err(ctx, "||", t, "boolean")
        return BOOLEAN


    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        n = len(ctx.equalityExpr())
        if n == 1:
            return ctx.equalityExpr(0).accept(self)
        for i in range(n):
            t = ctx.equalityExpr(i).accept(self)
            if t != BOOLEAN:
                self._op_err(ctx, "&&", t, "boolean")
        return BOOLEAN


    # ==, !=
    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        n = len(ctx.relationalExpr())
        if n == 1:
            return ctx.relationalExpr(0).accept(self)
        left = ctx.relationalExpr(0).accept(self)
        for i in range(1, n):
            right = ctx.relationalExpr(i).accept(self)
            if not self._eq_compatible(left, right):
                self._op_err(ctx, "==/!=", f"{left} vs {right}")
        return BOOLEAN


    # <,<=,>,>=  (integer)
    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        n = len(ctx.additiveExpr())
        if n == 1:
            return ctx.additiveExpr(0).accept(self)
        t0 = ctx.additiveExpr(0).accept(self)
        for i in range(1, n):
            ti = ctx.additiveExpr(i).accept(self)
            if t0 != INTEGER or ti != INTEGER:
                self._op_err(ctx, "relacional", f"{t0} y {ti}", "integer")
        return BOOLEAN


    # +, -
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        n = len(ctx.multiplicativeExpr())
        if n == 1:
            return ctx.multiplicativeExpr(0).accept(self)

        res = ctx.multiplicativeExpr(0).accept(self)
        for i in range(1, n):
            t = ctx.multiplicativeExpr(i).accept(self)
            # Si aparece string en una suma/resta:
            if res == STRING or t == STRING:
                # Permitimos concatenación si todos son string; si hay mezcla, error
                if res != STRING or t != STRING:
                    self._op_err(ctx, "+/-", f"{res} y {t}", "string o integer (coincidentes)")
                res = STRING
            else:
                # aritmética entera
                if res != INTEGER or t != INTEGER:
                    self._op_err(ctx, "+/-", f"{res} y {t}", "integer")
                res = INTEGER
        return res


    # *, /, %
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        n = len(ctx.unaryExpr())
        if n == 1:
            return ctx.unaryExpr(0).accept(self)
        for i in range(n):
            t = ctx.unaryExpr(i).accept(self)
            if t != INTEGER:
                self._op_err(ctx, "*,/,%", t, "integer")
        return INTEGER
    


        # !  y  - (unario)
    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t  = ctx.getChild(1).accept(self)
            if op == '!':
                if t != BOOLEAN: self._op_err(ctx, "!", t, "boolean")
                return BOOLEAN
            if op == '-':
                if t != INTEGER: self._op_err(ctx, "neg", t, "integer")
                return INTEGER
        return self.visitChildren(ctx)


    # helpers
    def _eq_compatible(self, a: Type, b: Type) -> bool:
        if a.name == b.name: return True
        if a == NULL or b == NULL:
            return True  # permitimos comparar con null
        return False

    def _is_assignable(self, src: Type, dst: Type) -> bool:
        if src.name == dst.name: return True
        if src == NULL and (isinstance(dst, ArrayType) or isinstance(dst, ClassType)):
            return True
        return False

    def _op_err(self, ctx: ParserRuleContext, op: str, got, expected: str=None):
        msg = f"Tipos incompatibles para '{op}': {got}"
        if expected: msg += f" (se esperaba {expected})"
        self.errors.report(ctx.start.line, ctx.start.column, "E010", msg)

def run_semantic(tree) -> ErrorCollect	or:
    errors = ErrorCollector()
    p1 = SymbolCollector(errors); p1.visit(tree)
    p2 = TypeCheckerVisitor(errors, p1.global_scope, p1.scopes_by_ctx); p2.visit(tree)
    return errors
