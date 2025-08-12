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
    if t in ("null", "void"): return NULL
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
        decl_type = self.visit(ctx.typeAnnotation()) if ctx.typeAnnotation() else NULL
        sym = VariableSymbol(name=name, typ=decl_type, is_const=False, initialized=False)
        if not self.current.define(sym):
            self.errors.report(ctx.start.line, ctx.start.column, "E001", f"Redeclaración de '{name}'.")
        return None

    # constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';'
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = _first_identifier_text(ctx)
        decl_type = self.visit(ctx.typeAnnotation()) if ctx.typeAnnotation() else NULL
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

        # scope de clase
        self._enter_child_scope(ctx)

        # Recorremos miembros explícitamente para poblar fields/methods en ClassSymbol
        for cm in ctx.classMember():
            if cm.variableDeclaration() is not None:
                vctx = cm.variableDeclaration()
                vname = _first_identifier_text(vctx)
                vtype = self.visit(vctx.typeAnnotation()) if vctx.typeAnnotation() else NULL
                # Declarar símbolo de campo en scope de clase (opcional, útil para 'this' más adelante)
                vsym = VariableSymbol(name=vname, typ=vtype, is_const=False, initialized=False)
                if not self.current.define(vsym):
                    self.errors.report(vctx.start.line, vctx.start.column, "E001", f"Redeclaración de '{vname}'.")
                # Registrar en la clase
                csym.fields[vname] = vtype

            elif cm.constantDeclaration() is not None:
                cctx = cm.constantDeclaration()
                vname = _first_identifier_text(cctx)
                vtype = self.visit(cctx.typeAnnotation()) if cctx.typeAnnotation() else NULL
                vsym = VariableSymbol(name=vname, typ=vtype, is_const=True, initialized=False)
                if not self.current.define(vsym):
                    self.errors.report(cctx.start.line, cctx.start.column, "E001", f"Redeclaración de '{vname}'.")
                csym.fields[vname] = vtype  # (si luego quieres distinguir const, puedes guardar flags aparte)

            elif cm.functionDeclaration() is not None:
                fctx = cm.functionDeclaration()
                fname = _first_identifier_text(fctx)
                # Armar FunctionType para el método
                params_syms = self.visit(fctx.parameters()) if fctx.parameters() else []
                ret_type = self.visit(fctx.type_()) if fctx.type_() else NULL
                ftype = FunctionType(params=[p.typ for p in params_syms], ret=ret_type)
                
                # marca el contexto del método con su clase
                setattr(fctx, "_enclosing_class", cname)
                fsym = FunctionSymbol(name=fname, typ=ftype, params=params_syms)
                if not self.current.define(fsym):
                    self.errors.report(fctx.start.line, fctx.start.column, "E001", f"Redeclaración de función '{fname}'.")
                # Definir parámetros en scope del método y visitar el cuerpo
                self._enter_child_scope(fctx)
                for p in params_syms:
                    if not self.current.define(p):
                        self.errors.report(fctx.start.line, fctx.start.column, "E001", f"Parámetro duplicado '{p.name}'.")
                self.visit(fctx.block())
                self._exit_scope()

                # Registrar en la clase
                csym.methods[fname] = ftype

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
        self.func_ret_stack = []
        self.loop_depth = 0
        self.current_class_stack = []  # nombre de clase actual si estamos dentro de un método

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
        # Entrar al scope de la función (creado en Pass1)
        self._enter_by_ctx(ctx)

        # Resolver el símbolo de la función en el scope padre para obtener el tipo de retorno
        fname = ctx.Identifier().getText()
        parent_scope = self.current.parent if self.current else None
        fsym = parent_scope.resolve(fname) if parent_scope else None
        expected_ret = fsym.typ.ret if fsym and hasattr(fsym, "typ") else NULL

        # --- detectar si estamos dentro de una clase ---
        enclosing_class_name = getattr(ctx, "_enclosing_class", None)
        if enclosing_class_name:
            # estamos en un método: habilitar 'this'
            self.current_class_stack.append(enclosing_class_name)
            # define 'this' en el scope del método (si no existe)
            try:
                self.current.define(VariableSymbol(
                    name="this",
                    typ=ClassType(enclosing_class_name),
                    is_const=False,
                    initialized=True
                ))
            except Exception:
                pass

        self.func_ret_stack.append(expected_ret)
        # Visitar cuerpo
        self.visit(ctx.block())
        self.func_ret_stack.pop()

        # todas las rutas retornan (solo si se espera valor)
        if expected_ret != NULL and not self._returns_all_block(ctx.block()):
            self.errors.report(ctx.start.line, ctx.start.column, "E015",
                            f"La función '{fname}' no retorna en todas las rutas.")

        if enclosing_class_name:
            self.current_class_stack.pop()

        self._exit()
        return None


    # prohibir return fuera de función
    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        if not self.func_ret_stack:
            self.errors.report(ctx.start.line, ctx.start.column, "E014", "return fuera de función.")
            return None
        expected = self.func_ret_stack[-1]
        if ctx.expression():  # return expr;
            actual = self.visit(ctx.expression())
            if not self._is_assignable(actual, expected):
                self.errors.report(ctx.start.line, ctx.start.column, "E012",
                                f"Tipo de return '{actual}' no es asignable a '{expected}'.")
        else:  # return;
            if expected != NULL:
                self.errors.report(ctx.start.line, ctx.start.column, "E013",
                                f"Se esperaba 'return' con valor de tipo '{expected}'.")
        return None


    # variableDeclaration: ('let'|'var') Identifier typeAnnotation? initializer? ';'
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        name = _first_identifier_text(ctx)
        sym = self.current.resolve(name)
        if ctx.initializer():
            itype = self.visit(ctx.initializer())
            if sym:
                if sym.typ == NULL:  # sin anotación → inferimos
                    sym.typ = itype
                    sym.initialized = True
                else:
                    if not self._is_assignable(itype, sym.typ):
                        self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                        f"No se puede asignar '{itype}' a '{sym.typ}' en inicialización de '{name}'.")
                    else:
                        sym.initialized = True
        return None

    # constantDeclaration: const debe inicializarse y ser asignable
    # constantDeclaration: 'const' Identifier typeAnnotation? '=' expression ';'
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        name = _first_identifier_text(ctx)
        sym = self.current.resolve(name)
        itype = self.visit(ctx.expression())  # const SIEMPRE lleva init en tu gramática
        if sym:
            if sym.typ == NULL:
                sym.typ = itype  # inferimos si no hubo anotación
            elif not self._is_assignable(itype, sym.typ):
                self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                f"No se puede asignar '{itype}' a '{sym.typ}' en const '{name}'.")
            sym.initialized = True
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
            # assignment: expression '.' Identifier '=' expression ';'
            obj_t = self.visit(ctx.expression(0))           # tipo del objeto
            # nombre de la propiedad: el tercer hijo es el Identifier en esta regla
            prop_name = ctx.getChild(2).getText()
            prop_t = self._resolve_property_type(obj_t, prop_name, ctx)
            rhs_t = self.visit(ctx.expression(1))
            if not self._is_assignable(rhs_t, prop_t):
                self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                f"No se puede asignar '{rhs_t}' a '{prop_t}'.")
            return prop_t


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
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        t = self.visit(ctx.primaryAtom())
        for s in ctx.suffixOp():
            t = self._suffix_apply_by_token(s, t)
        return t




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
        csym = self._resolve_class_symbol(cname)
        args = ctx.arguments().expression() if ctx.arguments() else []

        if not csym:
            # clase no declarada
            for e in args: self.visit(e)  # igual tipamos args para propagar
            self.errors.report(ctx.start.line, ctx.start.column, "E037", f"Clase '{cname}' no declarada.")
            return ClassType(cname)  # devolvemos el tipo para no cascada de errores

        ctor = csym.methods.get("constructor")
        if not ctor:
            # sin constructor declarado: solo 0 argumentos
            if len(args) != 0:
                self.errors.report(ctx.start.line, ctx.start.column, "E021",
                                f"Aridad inválida en constructor de '{cname}': se esperaban 0 argumentos.")
            else:
                # nada que validar
                pass
            return ClassType(cname)

        # validar aridad
        if len(args) != len(ctor.params):
            self.errors.report(ctx.start.line, ctx.start.column, "E021",
                            f"Aridad inválida en constructor de '{cname}': se esperaban {len(ctor.params)} argumentos.")
        else:
            for i, e in enumerate(args):
                actual = self.visit(e)
                expected = ctor.params[i]
                if not self._is_assignable(actual, expected):
                    self.errors.report(e.start.line, e.start.column, "E022",
                                    f"Arg {i+1} en constructor de '{cname}': '{actual}' no asignable a '{expected}'.")
        return ClassType(cname)


    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        if not self.current_class_stack:
            self.errors.report(ctx.start.line, ctx.start.column, "E043", "this no puede usarse fuera de un método de clase.")
            return NULL
        return ClassType(self.current_class_stack[-1])


    # foreach (...) { ... }  
    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        et = self.visit(ctx.expression())
        if not isinstance(et, ArrayType):
            self.errors.report(ctx.start.line, ctx.start.column, "E032",
                            "foreach espera un arreglo en 'in'.")
            elem_t = NULL
        else:
            elem_t = et.elem
        # Entrar al scope del bloque (creado en Pass1) y declarar el iterador
        block = ctx.block()
        self._enter_by_ctx(block)
        name = ctx.Identifier().getText()
        self.current.define(VariableSymbol(name=name, typ=elem_t, is_const=False, initialized=True))
        self.loop_depth += 1
        self.visit(block)
        self.loop_depth -= 1
        self._exit()
        return None


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

    def _suffix_apply_by_token(self, sctx, base_type: Type) -> Type:
        first = sctx.getChild(0).getText()  # '(', '[' o '.'
        if first == '(':
            return self._apply_call(sctx, base_type)
        if first == '[':
            return self._apply_index(sctx, base_type)
        if first == '.':
            return self._apply_prop(sctx, base_type)
        return base_type
    
    def _is_assignable(self, src: Type, dst: Type) -> bool:
        if src.name == dst.name: return True
        if src == NULL and (isinstance(dst, ArrayType) or isinstance(dst, ClassType)):
            return True
        return False

    def _op_err(self, ctx: ParserRuleContext, op: str, got, expected: str=None):
        msg = f"Tipos incompatibles para '{op}': {got}"
        if expected: msg += f" (se esperaba {expected})"
        self.errors.report(ctx.start.line, ctx.start.column, "E010", msg)

    def _apply_suffix(self, sctx, base_type: Type) -> Type:
        # Detecta por el primer token del sufijo: "(", "[" o "."
        first = sctx.getChild(0).getText()
        if first == '(':
            # buscar ArgumentsContext si existe
            args_ctx = None
            for ch in sctx.getChildren():
                if isinstance(ch, CompiscriptParser.ArgumentsContext):
                    args_ctx = ch
                    break
            return self._apply_call(args_ctx, base_type)
        if first == '[':
            # estructura: '[' expression ']'
            idx_expr_ctx = sctx.expression()
            return self._apply_index(sctx, base_type, idx_expr_ctx)
        if first == '.':
            # estructura: '.' Identifier
            # (stub por ahora; más adelante resolvemos campos/métodos de clases)
            return self._apply_prop(sctx, base_type)
        return base_type

    def _apply_call(self, sctx: CompiscriptParser.CallExprContext, callee_type: Type) -> Type:
        if not isinstance(callee_type, FunctionType):
            if sctx.arguments():
                for e in sctx.arguments().expression():
                    self.visit(e)
            self.errors.report(sctx.start.line, sctx.start.column, "E020",
                            f"Llamada sobre no-función '{callee_type}'.")
            return NULL

        args = sctx.arguments().expression() if sctx.arguments() else []
        if len(args) != len(callee_type.params):
            self.errors.report(sctx.start.line, sctx.start.column, "E021",
                            f"Aridad inválida: se esperaban {len(callee_type.params)} argumentos.")
        else:
            for i, e in enumerate(args):
                actual = self.visit(e)
                expected = callee_type.params[i]
                if not self._is_assignable(actual, expected):
                    self.errors.report(e.start.line, e.start.column, "E022",
                                    f"Arg {i+1}: '{actual}' no asignable a '{expected}'.")
        return callee_type.ret


    def _apply_index(self, sctx: CompiscriptParser.IndexExprContext, base_type: Type) -> Type:
        idx_t = self.visit(sctx.expression())
        if idx_t != INTEGER:
            self.errors.report(sctx.start.line, sctx.start.column, "E030", "Índice debe ser integer.")
        if not isinstance(base_type, ArrayType):
            self.errors.report(sctx.start.line, sctx.start.column, "E031",
                            f"Indexación solo en arreglos, no en '{base_type}'.")
            return NULL
        return base_type.elem

    def _apply_prop(self, sctx: CompiscriptParser.PropertyAccessExprContext, base_type: Type) -> Type:
        prop = sctx.Identifier().getText()
        return self._resolve_property_type(base_type, prop, sctx)

    
    # helper interno (añádelo en TypeCheckerVisitor)
    def _expect_boolean(self, expr_ctx):
        t = self.visit(expr_ctx)
        if t != BOOLEAN:
            self.errors.report(expr_ctx.start.line, expr_ctx.start.column, "E040",
                            f"Condición debe ser boolean, no '{t}'.")

    # if (bool) { ... } else { ... }
    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        self._expect_boolean(ctx.expression())
        self.visit(ctx.block(0))
        if ctx.block(1):
            self.visit(ctx.block(1))
        return None

    # while (bool) { ... }
    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        self._expect_boolean(ctx.expression())
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return None
    
    # do { ... } while (bool);
    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        self._expect_boolean(ctx.expression())
        return None

    # for (init; cond?; update?) { ... }
    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())

        exprs = ctx.expression()
        if len(exprs) >= 1:
            self._expect_boolean(exprs[0])   # la condición si existe
        if len(exprs) == 2:
            self.visit(exprs[1])             # update (solo visitarlo)

        self.loop_depth += 1
        self.visit(ctx.block())
        self.loop_depth -= 1
        return None
    # break; y continue; solo dentro de loops
    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        if self.loop_depth == 0:
            self.errors.report(ctx.start.line, ctx.start.column, "E041", "break fuera de bucle.")
        return None

    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        if self.loop_depth == 0:
            self.errors.report(ctx.start.line, ctx.start.column, "E042", "continue fuera de bucle.")
        return None
    
    # ---- Returns en todas las rutas (análisis simple) ----
    def _returns_all_block(self, bctx: CompiscriptParser.BlockContext) -> bool:
        # Si algún statement del bloque garantiza return, el bloque garantiza return.
        # Nota: Esto es conservador y suficiente para la rúbrica (no analiza loops/switch).
        for st in bctx.statement():
            if self._returns_all_stmt(st):
                return True
        return False
    
    def _returns_all_stmt(self, sctx: CompiscriptParser.StatementContext) -> bool:
        # return;
        if sctx.returnStatement() is not None:
            return True
        # { ... }
        if sctx.block() is not None:
            return self._returns_all_block(sctx.block())
        # if (..) { ... } else { ... }
        if sctx.ifStatement() is not None:
            ifc = sctx.ifStatement()
            # Requiere else y que ambas ramas garanticen return
            if ifc.block(1) is None:
                return False
            return self._returns_all_block(ifc.block(0)) and self._returns_all_block(ifc.block(1))
        # (Opcional a futuro) try/catch, switch, etc.
        return False

    def _resolve_class_symbol(self, cname: str) -> Optional[ClassSymbol]:
        # Desde el scope actual, resolve hasta encontrar la clase en scopes superiores
        sym = self.current.resolve(cname)
        return sym if isinstance(sym, ClassSymbol) else None

    def _resolve_property_type(self, obj_type: Type, prop: str, err_ctx) -> Type:
        if not isinstance(obj_type, ClassType):
            self.errors.report(err_ctx.start.line, err_ctx.start.column, "E033",
                            f"Acceso a propiedad sobre no-objeto '{obj_type}'.")
            return NULL
        csym = self._resolve_class_symbol(obj_type.name)
        if not csym:
            self.errors.report(err_ctx.start.line, err_ctx.start.column, "E033",
                            f"Clase '{obj_type.name}' no encontrada para acceso a propiedad.")
            return NULL
        if prop in csym.fields:
            return csym.fields[prop]
        if prop in csym.methods:
            return csym.methods[prop]  # FunctionType
        self.errors.report(err_ctx.start.line, err_ctx.start.column, "E034",
                        f"Propiedad o método '{prop}' no existe en '{obj_type.name}'.")
        return NULL


# -----------------------------
# Orquestador
# -----------------------------
def run_semantic(tree) -> ErrorCollector:
    errors = ErrorCollector()
    p1 = SymbolCollector(errors); p1.visit(tree)
    p2 = TypeCheckerVisitor(errors, p1.global_scope, p1.scopes_by_ctx); p2.visit(tree)
    return errors
