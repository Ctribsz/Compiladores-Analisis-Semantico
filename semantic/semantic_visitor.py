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
        self.classes = {}  # nombre -> ClassSymbol

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
    def visitProgram(self, ctx):
        self._bind_scope(ctx, self.global_scope)
        r = self.visitChildren(ctx)
        self._finalize_inheritance()
        
        # NUEVO: Calcular offsets después de recolectar todos los símbolos
        self._calculate_offsets()
        
        return r

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
        # guarda para herencia
        self.classes[cname] = csym
        setattr(csym, "_ctx", ctx)  # para line/col en errores

        # base (opcional): grammar: class Identifier (':' Identifier)?
        if ctx.Identifier(1):
            csym.base_name = ctx.Identifier(1).getText()
        else:
            csym.base_name = None
        csym.base = None  # se vincula en la fase de resolución
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

    def _finalize_inheritance(self):
        # dfs para resolver base, detectar ciclos y fusionar miembros
        VIS_NEW, VIS_RUN, VIS_DONE = 0, 1, 2
        for cs in self.classes.values():
            setattr(cs, "_vis", VIS_NEW)

        def same_sig(a, b):
            from .types import FunctionType
            if not isinstance(a, FunctionType) or not isinstance(b, FunctionType):
                return False
            if len(a.params) != len(b.params): return False
            for i in range(len(a.params)):
                if a.params[i].name != b.params[i].name:
                    return False
            return a.ret.name == b.ret.name

        def merge(derived, base):
            # Métodos: heredar; permitir override compatible; NO heredar 'constructor'
            for mname, mt in base.methods.items():
                if mname == "constructor":
                    continue
                if mname in derived.methods:
                    dt = derived.methods[mname]
                    if not same_sig(dt, mt):
                        ctx = getattr(derived, "_ctx", None)
                        line = ctx.start.line if ctx else 0
                        col  = ctx.start.column if ctx else 0
                        self.errors.report(line, col, "E053",
                            f"Override incompatible de método '{mname}' en '{derived.name}'.")
                    # si es compatible, se queda el de la derivada
                else:
                    derived.methods[mname] = mt
            # Campos: conflicto si el derivado redeclara un campo de la base
            for fname, ft in base.fields.items():
                if fname in derived.fields:
                    ctx = getattr(derived, "_ctx", None)
                    line = ctx.start.line if ctx else 0
                    col  = ctx.start.column if ctx else 0
                    self.errors.report(line, col, "E054",
                        f"Campo '{fname}' en '{derived.name}' ya existe en la base '{base.name}'.")
                    # se mantiene el del derivado
                else:
                    derived.fields[fname] = ft

        def dfs(csym):
            vis = getattr(csym, "_vis", 0)
            if vis == VIS_RUN:
                ctx = getattr(csym, "_ctx", None)
                line = ctx.start.line if ctx else 0
                col  = ctx.start.column if ctx else 0
                self.errors.report(line, col, "E052",
                    f"Herencia cíclica detectada en '{csym.name}'.")
                csym.base = None
                csym.base_name = None
                setattr(csym, "_vis", VIS_DONE)
                return
            if vis == VIS_DONE:
                return

            setattr(csym, "_vis", VIS_RUN)

            if getattr(csym, "base_name", None):
                bname = csym.base_name
                base = self.classes.get(bname)
                if not base:
                    ctx = getattr(csym, "_ctx", None)
                    line = ctx.start.line if ctx else 0
                    col  = ctx.start.column if ctx else 0
                    self.errors.report(line, col, "E051",
                        f"Clase base '{bname}' no encontrada para '{csym.name}'.")
                    csym.base = None
                    csym.base_name = None
                else:
                    dfs(base)
                    csym.base = base
                    merge(csym, base)

            setattr(csym, "_vis", VIS_DONE)

        for cs in self.classes.values():
            if getattr(cs, "_vis", 0) == VIS_NEW:
                dfs(cs)

        # cleanup flags
        for cs in self.classes.values():
            if hasattr(cs, "_vis"): delattr(cs, "_vis")

    # ============================================
    # NUEVO: Métodos para calcular offsets y registros de activación
    # ============================================
    
    def _calculate_offsets(self):
        """Calcula offsets y tamaños para todos los símbolos"""
        print("=== CALCULANDO OFFSETS ===")  # DEBUG
        self._process_global_scope(self.global_scope)
        
        # DEBUG: Imprimir lo que calculamos
        for name, sym in self.global_scope.symbols.items():
            print(f"Símbolo: {name}")
            print(f"  - offset: {getattr(sym, 'offset', 'NO TIENE')}")
            if isinstance(sym, FunctionSymbol):
                print(f"  - label: {getattr(sym, 'label', 'NO TIENE')}")
                print(f"  - params_size: {getattr(sym, 'params_size', 0)}")
                print(f"  - locals_size: {getattr(sym, 'locals_size', 0)}")
                print(f"  - frame_size: {getattr(sym, 'frame_size', 0)}")
                for p in (sym.params or []):
                    print(f"    - param {p.name}: offset={getattr(p, 'offset', 'NO TIENE')}")
        print("=== FIN CÁLCULO ===")
        
    def _process_global_scope(self, scope: Scope):
        """Procesa el scope global asignando offsets a variables y procesando funciones"""
        global_offset = 0
        
        for name, symbol in scope.symbols.items():
            if isinstance(symbol, VariableSymbol):
                # Variables globales: offsets positivos desde 0
                symbol.offset = global_offset
                global_offset += self._get_size(symbol.typ)
            
            elif isinstance(symbol, FunctionSymbol):
                # Procesar función
                self._process_function(symbol)
            
            elif isinstance(symbol, ClassSymbol):
                # Procesar clase
                self._process_class(symbol)
                
                # NUEVO: También procesar métodos de la clase
                # Buscar el scope de la clase para procesar sus métodos
                for ctx, scope_inner in self.scopes_by_ctx.items():
                    if ctx in self.scopes_by_ctx and hasattr(ctx, 'Identifier'):
                        try:
                            if hasattr(ctx, 'classMember') and ctx.Identifier().getText() == name:
                                # Procesar funciones en el scope de la clase
                                for method_name, method_sym in scope_inner.symbols.items():
                                    if isinstance(method_sym, FunctionSymbol):
                                        self._process_function(method_sym)
                        except:
                            pass
    
    def _process_function(self, fsym: FunctionSymbol):
        """Calcula offsets y tamaños para una función"""
        # Asignar label a la función
        fsym.label = f"L_{fsym.name}"
        
        # Calcular offsets para parámetros (negativos, antes del frame)
        param_offset = -4  # Empezar en -4 (después del return address)
        for param in (fsym.params or []):
            param.offset = param_offset
            param_offset -= self._get_size(param.typ)
        
        # Tamaño total de parámetros
        fsym.params_size = abs(param_offset) - 4
        
        # Buscar el scope de la función para calcular locals
        func_scope = self._find_function_scope(fsym.name)
        if func_scope:
            fsym.locals_size = self._calculate_locals_in_scope(func_scope)
        else:
            fsym.locals_size = 0
        
        # Frame size = params + locals + overhead (12 bytes: return, old FP, static link)
        fsym.frame_size = fsym.params_size + fsym.locals_size + 12
        
        # DEBUG: Imprimir para verificar
        print(f"  Función {fsym.name}: params_size={fsym.params_size}, locals_size={fsym.locals_size}, frame_size={fsym.frame_size}")
    
    def _process_class(self, csym: ClassSymbol):
        """Calcula tamaño de instancia para una clase y procesa sus métodos"""
        field_offset = 0
        
        # Calcular tamaño sumando todos los campos
        for field_name, field_type in (csym.fields or {}).items():
            field_offset += self._get_size(field_type)
        
        csym.instance_size = field_offset
        
        # Los métodos están como FunctionSymbol en el scope de la clase
        # Necesitamos encontrar ese scope
        class_ctx = getattr(csym, "_ctx", None)
        if class_ctx and class_ctx in self.scopes_by_ctx:
            class_scope = self.scopes_by_ctx[class_ctx]
            
            # Buscar FunctionSymbols en el scope de la clase
            for name, symbol in class_scope.symbols.items():
                if isinstance(symbol, FunctionSymbol):
                    # Procesar cada método como una función
                    self._process_function(symbol)
    
    def _calculate_locals_in_scope(self, scope: Scope, base_offset: int = 0) -> int:
        """
        Calcula el tamaño total de variables locales en un scope
        y asigna offsets a cada variable local
        """
        local_offset = base_offset
        
        for name, symbol in scope.symbols.items():
            if isinstance(symbol, VariableSymbol):
                # Asignar offset a la variable local
                symbol.offset = local_offset
                local_offset += self._get_size(symbol.typ)
        
        return local_offset - base_offset
    
    def _find_function_scope(self, func_name: str) -> Optional[Scope]:
        """Busca el scope interno de una función por su nombre"""
        for ctx, scope in self.scopes_by_ctx.items():
            # Verificar si es un contexto de función
            if hasattr(ctx, 'Identifier'):
                try:
                    ctx_id = ctx.Identifier()
                    if ctx_id and ctx_id.getText() == func_name:
                        # Este es el contexto de la función, buscar su scope interno (el bloque)
                        if hasattr(ctx, 'block'):
                            block_ctx = ctx.block()
                            if block_ctx in self.scopes_by_ctx:
                                return self.scopes_by_ctx[block_ctx]
                except:
                    pass
        return None
    
    def _get_size(self, typ: Type) -> int:
        """
        Retorna el tamaño en bytes de un tipo
        Convención: 4 bytes para primitivos, 8 para referencias
        """
        if typ == INTEGER or typ == BOOLEAN:
            return 4
        elif typ == STRING:
            return 8  # Puntero a string
        elif isinstance(typ, ArrayType):
            return 8  # Puntero a array
        elif isinstance(typ, ClassType):
            return 8  # Puntero a instancia
        elif isinstance(typ, FunctionType):
            return 8  # Puntero a función
        else:
            return 4  # Default
        
# =============================
# PASS 2: Chequeo de tipos/uso
# =============================
class TypeCheckerVisitor(CompiscriptVisitor):
    def __init__(self, errors: ErrorCollector, root_scope: Scope, scopes_by_ctx: dict):
        self.errors = errors
        self.current = root_scope
        self.scopes_by_ctx = scopes_by_ctx
        self.types_by_ctx = {}
        self.func_ret_stack = []
        self.loop_depth = 0
        self.current_class_stack = []  # nombre de clase actual si estamos dentro de un método

    # printStatement: 'print' '(' expression ')' ';'
    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        # Solo necesitamos visitar la expresión para que se
        # calcule y guarde su tipo en self.types_by_ctx
        if ctx.expression():
            self.visit(ctx.expression())
        return None
    
    def _set_type(self, ctx: ParserRuleContext, typ: Type) -> Type:
        """Guarda el tipo para este nodo de contexto y lo retorna."""
        self.types_by_ctx[ctx] = typ
        return typ

    def _enter_by_ctx(self, ctx: ParserRuleContext):
        s = self.scopes_by_ctx.get(ctx)
        if s: self.current = s

    def _exit(self):
        if self.current.parent: self.current = self.current.parent

    # program / block / function: moverse por scopes ya construidos
    def visitProgram(self, ctx):
        self._enter_by_ctx(ctx)
        r = self.visitChildren(ctx)
        self._exit()
        return r

    # ****** INICIO DE CAMBIOS ******
    
    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        """
        conditionalExpr:
            logicalOrExpr ('?' expression ':' expression)?  # TernaryExpr
        """
        cond_t = self.visit(ctx.logicalOrExpr()) # <--- ARREGLADO (visit)

        # Si no hay '?', el valor es el de logicalOrExpr
        if len(ctx.expression()) == 0:
            return self._set_type(ctx, cond_t)

        # Con ternario: validar condición y calcular tipo común
        if cond_t != BOOLEAN:
            self.errors.report(ctx.start.line, ctx.start.column, "E040",
                            f"Condición debe ser boolean, no '{cond_t}'.")

        t_then = self.visit(ctx.expression(0))
        t_else = self.visit(ctx.expression(1))

        # Regla de "tipo común"
        if self._is_assignable(t_then, t_else):
            return self._set_type(ctx, t_else)
        if self._is_assignable(t_else, t_then):
            return self._set_type(ctx, t_then)
        if t_then == NULL and t_else != NULL:
            return self._set_type(ctx, t_else)
        if t_else == NULL and t_then != NULL:
            return self._set_type(ctx, t_then)

        # Incompatible
        self.errors.report(ctx.start.line, ctx.start.column, "E070",
                        f"Ramas incompatibles en ternario: '{t_then}' vs '{t_else}'.")
        return self._set_type(ctx, NULL) # <--- ARREGLADO (wrapper)

    # ****** FIN DE CAMBIOS ******


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
        return self._set_type(ctx, self.visit(ctx.expression()))

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
                return self._set_type(ctx, NULL)
            sym = self.current.resolve(name)
            if not sym:
                self.errors.report(ctx.start.line, ctx.start.column, "E002", f"Identificador no declarado '{name}'.")
                return self._set_type(ctx, NULL)
            if sym.is_const:
                self.errors.report(ctx.start.line, ctx.start.column, "E005", f"No se puede reasignar const '{name}'.")
                return self._set_type(ctx, sym.typ)
            if not self._is_assignable(rtype, sym.typ):
                self.errors.report(ctx.start.line, ctx.start.column, "E004",
                                   f"No se puede asignar '{rtype}' a '{sym.typ}'.")
            else:
                sym.initialized = True
            return self._set_type(ctx, sym.typ)
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
            return self._set_type(ctx, prop_t)

    # expressionStatement: expression ';'
    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        self.visit(ctx.expression()); return None

    # ---- Expresiones ----
    # expression: assignmentExpr;
    def visitExpression(self, ctx: CompiscriptParser.ExpressionContext):
        # Visita al hijo (assignmentExpr) y guarda su tipo
        # en el contexto de ESTA expresión
        child_type = self.visit(ctx.assignmentExpr())
        return self._set_type(ctx, child_type)

    # ****** INICIO DE CAMBIOS ******

    # (AÑADIR ESTE MÉTODO a TypeCheckerVisitor)
    # assignmentExpr: lhs=leftHandSide op='=' rhs=assignmentExpr | conditionalExpr;
    def visitAssignmentExpr(self, ctx: CompiscriptParser.AssignmentExprContext):
        if ctx.conditionalExpr():
            # Es un passthrough (no asignación), ej: 'i'
            # El 'conditionalExpr' es visitado por 'visitTernaryExpr'
            typ = self.visit(ctx.conditionalExpr())
        else:
            # Es una asignación, ej: 'a = 5'
            # (El chequeo de tipo para la asignación real se hace en 
            # 'visitAssignment' (statement) y 'visitAssignExpr' (TAC).
            # Aquí solo necesitamos propagar el tipo de la expresión.)
            typ = self.visit(ctx.assignmentExpr()) # Visita el RHS

        return self._set_type(ctx, typ)

    # (AÑADIR ESTE MÉTODO a TypeCheckerVisitor)
    def visitExprNoAssign(self, ctx: CompiscriptParser.ExprNoAssignContext):
        """Visita expresión sin asignación"""
        # (Esto asume que el hijo es conditionalExpr, como en tac_generator.py)
        typ = self.visit(ctx.conditionalExpr())
        return self._set_type(ctx, typ)

    # ****** FIN DE CAMBIOS ******


    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        txt = ctx.getText()
        if txt == "true" or txt == "false": return self._set_type(ctx, BOOLEAN)
        if txt == "null": return self._set_type(ctx, NULL)
        if len(txt) >= 2 and ((txt[0] == '"' and txt[-1] == '"') or (txt[0] == "'" and txt[-1] == "'")):
            return self._set_type(ctx, STRING)
        if txt.lstrip("-").isdigit(): return self._set_type(ctx, INTEGER)
        return NULL

    # primaryExpr: literalExpr | leftHandSide | '(' expression ')'
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        # primaryExpr: literalExpr | leftHandSide | '(' expression ')'
        if ctx.literalExpr() is not None:
            return self._set_type(ctx, self.visit(ctx.literalExpr()))
        if ctx.leftHandSide() is not None:
            return self._set_type(ctx, self.visit(ctx.leftHandSide()))
        if ctx.expression() is not None:
            # caso paréntesis: devolver el tipo de la expresión interna
            return self._set_type(ctx, self.visit(ctx.expression()))
        return self._set_type(ctx, NULL)

    # leftHandSide: primaryAtom (suffixOp)* ;
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        t = self.visit(ctx.primaryAtom())
        for s in ctx.suffixOp():
            t = self._suffix_apply_by_token(s, t)
        return self._set_type(ctx, t)

    # primaryAtom:
    #   Identifier           # IdentifierExpr
    # | 'new' Identifier...  # NewExpr
    # | 'this'               # ThisExpr
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        name = ctx.Identifier().getText()
        sym = self.current.resolve(name)
        if not sym:
            self.errors.report(ctx.start.line, ctx.start.column, "E002", f"Identificador no declarado '{name}'.")
            return self._set_type(ctx, NULL)
        return self._set_type(ctx, sym.typ)

    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        cname = ctx.Identifier().getText()
        csym = self._resolve_class_symbol(cname)
        args = ctx.arguments().expression() if ctx.arguments() else []

        if not csym:
            # clase no declarada
            for e in args: self.visit(e)  # igual tipamos args para propagar
            self.errors.report(ctx.start.line, ctx.start.column, "E037", f"Clase '{cname}' no declarada.")
            return self._set_type(ctx, ClassType(cname))  # devolvemos el tipo para no cascada de errores

        ctor = csym.methods.get("constructor")
        if not ctor:
            # sin constructor declarado: solo 0 argumentos
            if len(args) != 0:
                self.errors.report(ctx.start.line, ctx.start.column, "E021",
                                f"Aridad inválida en constructor de '{cname}': se esperaban 0 argumentos.")
            else:
                # nada que validar
                pass
            return self._set_type(ctx, ClassType(cname))

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
        return self._set_type(ctx, ClassType(cname))


    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        if not self.current_class_stack:
            self.errors.report(ctx.start.line, ctx.start.column, "E043", "this no puede usarse fuera de un método de clase.")
            return self._set_type(ctx, NULL)
        return self._set_type(ctx, ClassType(self.current_class_stack[-1]))

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
            return self._set_type(ctx, ArrayType(NULL))
        t0 = self.visit(exprs[0])
        for e in exprs[1:]:
            ti = self.visit(e)
            if t0.name != ti.name:
                self.errors.report(ctx.start.line, ctx.start.column, "E011",
                                   f"Elementos de arreglo deben tener mismo tipo: {t0} vs {ti}.")
        return self._set_type(ctx, ArrayType(t0))

    # ****** INICIO DE CAMBIOS ******

    # logical OR/AND
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        n = len(ctx.logicalAndExpr())
        if n == 1:
            child_t = self.visit(ctx.logicalAndExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo
        for i in range(n):
            t = self.visit(ctx.logicalAndExpr(i)) # Usar visit()
            if t != BOOLEAN:
                self._op_err(ctx, "||", t, "boolean")
        return self._set_type(ctx, BOOLEAN)

    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        n = len(ctx.equalityExpr())
        if n == 1:
            child_t = self.visit(ctx.equalityExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo
        for i in range(n):
            t = self.visit(ctx.equalityExpr(i)) # Usar visit()
            if t != BOOLEAN:
                self._op_err(ctx, "&&", t, "boolean")
        return self._set_type(ctx, BOOLEAN)

    # ==, !=
    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        n = len(ctx.relationalExpr())
        if n == 1:
            child_t = self.visit(ctx.relationalExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo
        left = self.visit(ctx.relationalExpr(0)) # Usar visit()
        for i in range(1, n):
            right = self.visit(ctx.relationalExpr(i)) # Usar visit()
            if not self._eq_compatible(left, right):
                self._op_err(ctx, "==/!=", f"{left} vs {right}")
        return self._set_type(ctx, BOOLEAN)

    # <,<=,>,>=  (integer)
    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        n = len(ctx.additiveExpr())
        if n == 1:
            child_t = self.visit(ctx.additiveExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo
        t0 = self.visit(ctx.additiveExpr(0)) # Usar visit()
        for i in range(1, n):
            ti = self.visit(ctx.additiveExpr(i)) # Usar visit()
            if t0 != INTEGER or ti != INTEGER:
                self._op_err(ctx, "relacional", f"{t0} y {ti}", "integer")
        return self._set_type(ctx, BOOLEAN)

    # +, -
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        n = len(ctx.multiplicativeExpr())
        if n == 1:
            child_t = self.visit(ctx.multiplicativeExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo

        res = self.visit(ctx.multiplicativeExpr(0)) # Usar visit()
        for i in range(1, n):
            t = self.visit(ctx.multiplicativeExpr(i)) # Usar visit()
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
        return self._set_type(ctx, res)

    # *, /, %
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        n = len(ctx.unaryExpr())
        if n == 1:
            child_t = self.visit(ctx.unaryExpr(0))
            return self._set_type(ctx, child_t) # Guardar el tipo del hijo
        for i in range(n):
            t = self.visit(ctx.unaryExpr(i)) # Usar visit()
            if t != INTEGER:
                self._op_err(ctx, "*,/,%", t, "integer")
        return self._set_type(ctx, INTEGER)

    # !  y  - (unario)
    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            t  = self.visit(ctx.getChild(1)) # Usar visit()
            if op == '!':
                if t != BOOLEAN: self._op_err(ctx, "!", t, "boolean")
                return self._set_type(ctx, BOOLEAN)
            if op == '-':
                if t != INTEGER: self._op_err(ctx, "neg", t, "integer")
                return self._set_type(ctx, INTEGER)
        
        # Passthrough (ej: primaryExpr)
        child_t = self.visit(ctx.primaryExpr())
        return self._set_type(ctx, child_t)

    # ****** FIN DE CAMBIOS ******

    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        # Tipo del switch(expr)
        switch_t = self.visit(ctx.expression())

        # Conjunto para detectar duplicados de 'case' literales
        seen = {}

        # Validar cada case: tipo compatible y duplicados, luego visitar statements
        for c in ctx.switchCase():
            ce_t = self.visit(c.expression())

            if not self._is_case_compatible(ce_t, switch_t):
                self.errors.report(c.start.line, c.start.column, "E060",
                                f"Case incompatible con switch: '{ce_t}' vs '{switch_t}'.")

            k = self._case_value_key(c.expression())
            if k is not None:
                if k in seen:
                    self.errors.report(c.start.line, c.start.column, "E061",
                                    f"Case duplicado: {c.expression().getText()}.")
                else:
                    seen[k] = (c.start.line, c.start.column)

            # Visitar statements del case
            for st in c.statement():
                self.visit(st)

        # default (si lo hay)
        if ctx.defaultCase():
            for st in ctx.defaultCase().statement():
                self.visit(st)

        return None

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
            return self._set_type(sctx, NULL)

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
        return self._set_type(sctx, callee_type.ret)


    def _apply_index(self, sctx: CompiscriptParser.IndexExprContext, base_type: Type) -> Type:
        idx_t = self.visit(sctx.expression())
        if idx_t != INTEGER:
            self.errors.report(sctx.start.line, sctx.start.column, "E030", "Índice debe ser integer.")
        if not isinstance(base_type, ArrayType):
            self.errors.report(sctx.start.line, sctx.start.column, "E031",
                            f"Indexación solo en arreglos, no en '{base_type}'.")
            return self._set_type(sctx, NULL)
        return self._set_type(sctx, base_type.elem)

    def _apply_prop(self, sctx: CompiscriptParser.PropertyAccessExprContext, base_type: Type) -> Type:
        prop = sctx.Identifier().getText()
        # _resolve_property_type ya retorna NULL en error, así que solo envolvemos la llamada
        prop_type = self._resolve_property_type(base_type, prop, sctx)
        return self._set_type(sctx, prop_type) # <--- CAMBIO

    
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
        
    def _is_case_compatible(self, case_t: Type, switch_t: Type) -> bool:
        # Compatible si hay asignabilidad en algún sentido (p.ej., mismos primitivos, o NULL ↔ clase/array)
        return self._is_assignable(case_t, switch_t) or self._is_assignable(switch_t, case_t)

    def _case_value_key(self, expr_ctx) -> Optional[tuple]:
        """
        Retorna una clave hashable para detectar 'case' duplicados
        SOLO si el case es un literal simple: int, string, boolean.
        Si no, retorna None (no intentamos evaluar expresiones).
        """
        txt = expr_ctx.getText()
        # boolean
        if txt == "true":  return ("bool", True)
        if txt == "false": return ("bool", False)
        # string
        if (len(txt) >= 2 and ((txt[0] == '"' and txt[-1] == '"') or (txt[0] == "'" and txt[-1] == "'"))):
            return ("str", txt[1:-1])
        # integer (permite signo)
        core = txt[1:] if txt.startswith("-") else txt
        if core.isdigit():
            try:
                return ("int", int(txt))
            except Exception:
                return None
        return None
# -----------------------------
# Orquestador
# -----------------------------
class SemResult:
    """Contenedor para lo que consume el IDE/web: lista de errores + scope global."""
    def __init__(self, errors_obj: ErrorCollector, global_scope: Scope):
        # normaliza a lista si hay método to_list(); si no, intenta .errors; sino vacío
        if hasattr(errors_obj, "to_list"):
            self.errors = errors_obj.to_list()
        elif hasattr(errors_obj, "errors"):
            self.errors = errors_obj.errors
        else:
            self.errors = []
        self._errors_obj = errors_obj
        self.global_scope = global_scope

    # para que el adaptador del server pueda usar pretty() si lo necesita
    def pretty(self) -> str:
        if hasattr(self._errors_obj, "pretty"):
            return self._errors_obj.pretty()
        return ""

def run_semantic(tree) -> SemResult:
    errors = ErrorCollector()
    p1 = SymbolCollector(errors); p1.visit(tree)
    p2 = TypeCheckerVisitor(errors, p1.global_scope, p1.scopes_by_ctx); p2.visit(tree)
    return SemResult(errors, p1.global_scope)