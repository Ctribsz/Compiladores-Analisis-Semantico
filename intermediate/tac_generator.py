"""
Generador de código intermedio (Three-Address Code)
Visitor que recorre el AST y genera TAC
"""
from typing import Optional, Dict, List, Any
from antlr4 import ParserRuleContext

from program.gen.CompiscriptVisitor import CompiscriptVisitor
from program.gen.CompiscriptParser import CompiscriptParser
from semantic.scope import Scope
from semantic.symbols import VariableSymbol, FunctionSymbol, ClassSymbol
from semantic.types import Type, INTEGER, STRING, BOOLEAN, NULL, ArrayType, ClassType, FunctionType

from .tac import TACOp, TACOperand, TACInstruction, TACProgram

class TACGenerator(CompiscriptVisitor):
    """Generador de código TAC desde el AST de Compiscript"""
    
    def __init__(self, global_scope: Scope, scopes_by_ctx: dict):
        self.program = TACProgram()
        self.global_scope = global_scope
        self.current_scope = global_scope
        self.scopes_by_ctx = scopes_by_ctx
        
        # Stack para manejar break/continue
        self.loop_stack = []
        self.current_function = None
        self.switch_stack = []
        self.current_class = None
        self.class_symbols = {}
        
        # NUEVO: Gestión de memoria y funciones
        self.next_global_addr = 0x1000  # ← FALTA ESTO
        self.global_addrs = {}           # ← FALTA ESTO
        self.in_function = False         # ← FALTA ESTO
        
        self._collect_classes()
    
    def _collect_classes(self):
        """Recopila todas las clases definidas en el programa"""
        for name, symbol in self.global_scope.symbols.items():
            if isinstance(symbol, ClassSymbol):
                self.class_symbols[name] = symbol
    def _id(self, ctx, i: int = 0) -> str:
        """Texto del i-ésimo token Identifier en 'ctx' (o '' si no hay)."""
        tok = ctx.getToken(CompiscriptParser.Identifier, i)
        return tok.getText() if tok is not None else ""
    
    def _enter_scope(self, ctx: ParserRuleContext):
        """Entra a un scope basado en el contexto"""
        if ctx in self.scopes_by_ctx:
            self.current_scope = self.scopes_by_ctx[ctx]
    
    def _exit_scope(self):
        """Sale del scope actual"""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    
    def _make_operand(self, value: Any, is_constant: bool = False, typ: str = None) -> TACOperand:
        """Crea un operando TAC"""
        if isinstance(value, TACOperand):
            return value
        return TACOperand(value, is_constant=is_constant, typ=typ)
    
    def _make_constant(self, value: Any, typ: str = None) -> TACOperand:
        """Crea un operando constante"""
        return TACOperand(value, is_constant=True, typ=typ)
    
    def _make_variable(self, name: str, typ: str = None) -> TACOperand:
        """Crea un operando variable"""
        return TACOperand(name, typ=typ)

    # ---------- helpers para reciclaje de temporales ----------
    def _is_temp(self, name) -> bool:
        return isinstance(name, (str, TACOperand)) and str(name).startswith("t")

    def _free_if_temp(self, *names: Any):
        for n in names:
            # Si es TACOperand, su valor string está en n.value
            s = str(n.value) if isinstance(n, TACOperand) else str(n)
            if s and s.startswith("t"):
                self.program.free_temp(s)
    # ----------------------------------------------------------
    
    # ========== PROGRAM ==========
    def visitProgram(self, ctx: CompiscriptParser.ProgramContext):
        """Visita el programa completo"""
        self._enter_scope(ctx)
        
        # Generar código para todas las declaraciones
        for stmt in ctx.statement():
            self.visit(stmt)
        
        self._exit_scope()
        return self.program
    
    # ========== DECLARATIONS ==========
    def visitVariableDeclaration(self, ctx: CompiscriptParser.VariableDeclarationContext):
        """Declara una variable usando direcciones de memoria o FP+offset"""
        var_name = self._id(ctx)
        sym = self.current_scope.resolve(var_name)
        
        if ctx.initializer():
            init_value = self.visit(ctx.initializer())
            
            # Determinar si es global o local
            if self.in_function and sym and hasattr(sym, 'offset') and sym.offset is not None:
                # Variable local: usar FP[offset]
                fp_ref = TACOperand(f"FP[{sym.offset}]")
                # CORRECTO: result, arg1, arg2
                self.program.emit(TACOp.ASSIGN, result=fp_ref, arg1=init_value)
            else:
                # Variable global: asignar dirección de memoria
                if var_name not in self.global_addrs:
                    self.global_addrs[var_name] = hex(self.next_global_addr)
                    self.next_global_addr += 4
                
                addr_op = TACOperand(self.global_addrs[var_name])
                # CORRECTO: result, arg1, arg2
                self.program.emit(TACOp.ASSIGN, result=addr_op, arg1=init_value)
            
            self._free_if_temp(init_value)
        
        return None
    
    def visitConstantDeclaration(self, ctx: CompiscriptParser.ConstantDeclarationContext):
        """Declara una constante"""
        const_name = self._id(ctx)
        init_value = self.visit(ctx.expression())
        const_op = self._make_variable(const_name)
        self.program.emit(TACOp.ASSIGN, const_op, init_value)
        self._free_if_temp(init_value)
        return None
    
    def visitInitializer(self, ctx: CompiscriptParser.InitializerContext):
        """Visita un inicializador"""
        return self.visit(ctx.expression())
    
    # ========== STATEMENTS ==========
    def visitBlock(self, ctx: CompiscriptParser.BlockContext):
        """Visita un bloque de código"""
        self._enter_scope(ctx)
        for stmt in ctx.statement():
            self.visit(stmt)
        self._exit_scope()
        return None
    
    def visitAssignment(self, ctx: CompiscriptParser.AssignmentContext):
        """Maneja asignaciones"""
        if len(ctx.expression()) == 1:
            # Asignación simple: id = expr
            # Regla esperada: Identifier '=' expression
            var_name = self._id(ctx)
            value    = self.visit(ctx.expression(0))
            var_op   = self._make_variable(var_name)
            self.program.emit(TACOp.ASSIGN, var_op, value)
            # RHS consumido
            self._free_if_temp(value)
        else:
            # Asignación a propiedad: expr '.' Identifier '=' expression
            obj       = self.visit(ctx.expression(0))
            prop_name = self._id(ctx)
            value     = self.visit(ctx.expression(1))
            prop_op   = self._make_constant(prop_name)
            self.program.emit(TACOp.FIELD_ASSIGN, obj, prop_op, value)
            # RHS consumido
            self._free_if_temp(value)
        return None
    
    def visitExpressionStatement(self, ctx: CompiscriptParser.ExpressionStatementContext):
        """Visita una expresión como statement"""
        self.visit(ctx.expression())
        return None
    
    def visitPrintStatement(self, ctx: CompiscriptParser.PrintStatementContext):
        """Genera código para print"""
        value = self.visit(ctx.expression())
        self.program.emit(TACOp.PRINT, arg1=value)
        self._free_if_temp(value)
        return None
    
    # ========== CONTROL FLOW ==========
    def visitIfStatement(self, ctx: CompiscriptParser.IfStatementContext):
        """Genera código para if-else"""
        cond = self.visit(ctx.expression())
        
        else_label = self.program.new_label()
        end_label = self.program.new_label()
        
        # Si la condición es falsa, saltar al else (o al final si no hay else)
        if ctx.block(1):  # Hay else
            self.program.emit(TACOp.IF_FALSE, arg1=cond, arg2=else_label)
            self.visit(ctx.block(0))  # Then block
            self.program.emit(TACOp.GOTO, arg1=end_label)
            self.program.emit_label(else_label)
            self.visit(ctx.block(1))  # Else block
            self.program.emit_label(end_label)
        else:  # No hay else
            self.program.emit(TACOp.IF_FALSE, arg1=cond, arg2=end_label)
            self.visit(ctx.block(0))  # Then block
            self.program.emit_label(end_label)
        
        self._free_if_temp(cond)
        return None
    
    def visitWhileStatement(self, ctx: CompiscriptParser.WhileStatementContext):
        """Genera código para while"""
        start_label = self.program.new_label()
        continue_label = start_label  # continue va al inicio del loop
        end_label = self.program.new_label()
        
        self.loop_stack.append((continue_label, end_label))
        
        self.program.emit_label(start_label)
        cond = self.visit(ctx.expression())
        self.program.emit(TACOp.IF_FALSE, arg1=cond, arg2=end_label)
        self.visit(ctx.block())
        self.program.emit(TACOp.GOTO, arg1=start_label)
        self.program.emit_label(end_label)
        
        self.loop_stack.pop()
        self._free_if_temp(cond)
        return None
    
    def visitDoWhileStatement(self, ctx: CompiscriptParser.DoWhileStatementContext):
        """Genera código para do-while"""
        start_label = self.program.new_label()
        continue_label = self.program.new_label()
        end_label = self.program.new_label()
        
        self.loop_stack.append((continue_label, end_label))
        
        self.program.emit_label(start_label)
        self.visit(ctx.block())
        self.program.emit_label(continue_label)
        cond = self.visit(ctx.expression())
        self.program.emit(TACOp.IF_TRUE, arg1=cond, arg2=start_label)
        self.program.emit_label(end_label)
        
        self.loop_stack.pop()
        self._free_if_temp(cond)
        return None
    
    def visitForStatement(self, ctx: CompiscriptParser.ForStatementContext):
        """Genera código para for"""
        # Inicialización
        if ctx.variableDeclaration():
            self.visit(ctx.variableDeclaration())
        elif ctx.assignment():
            self.visit(ctx.assignment())
        
        start_label = self.program.new_label()
        continue_label = self.program.new_label()
        end_label = self.program.new_label()
        
        self.loop_stack.append((continue_label, end_label))
        
        self.program.emit_label(start_label)
        
        # Condición
        exprs = ctx.expression()
        cond = None
        if len(exprs) >= 1:
            cond = self.visit(exprs[0])
            self.program.emit(TACOp.IF_FALSE, arg1=cond, arg2=end_label)
        
        # Cuerpo
        self.visit(ctx.block())
        
        # Continue label (antes del update)
        self.program.emit_label(continue_label)
        
        # Update
        if len(exprs) >= 2:
            self.visit(exprs[1])
        
        self.program.emit(TACOp.GOTO, arg1=start_label)
        self.program.emit_label(end_label)
        
        self.loop_stack.pop()
        if cond is not None:
            self._free_if_temp(cond)
        return None
    
    def visitForeachStatement(self, ctx: CompiscriptParser.ForeachStatementContext):
        """Genera código para foreach (desazucarado a for con índice)"""
        iter_var = self._id(ctx)
        array = self.visit(ctx.expression())       # array sobre el que se itera

        # Temporales para manejo de índice y longitud
        index_temp  = self.program.new_temp()
        length_temp = self.program.new_temp()

        # index = 0
        self.program.emit(TACOp.ASSIGN, index_temp, self._make_constant(0))

        # length = array.length
        # Suponemos que FIELD_ACCESS escribe en length_temp el campo pedido.
        self.program.emit(TACOp.FIELD_ACCESS, length_temp, array, self._make_constant("length"))

        # Labels del ciclo
        start_label    = self.program.new_label()   # verifica condición y/o inicio de iteración
        continue_label = self.program.new_label()   # punto de 'continue'
        end_label      = self.program.new_label()   # salida del foreach

        # Registrar para 'break' y 'continue'
        self.loop_stack.append((continue_label, end_label))

        # Inicio del ciclo
        self.program.emit_label(start_label)

        # if (index >= length) goto end_label
        cmp_exit = self.program.new_temp()
        self.program.emit(TACOp.GE, cmp_exit, index_temp, length_temp)
        self.program.emit(TACOp.IF_TRUE, arg1=cmp_exit, arg2=end_label)
        self._free_if_temp(cmp_exit)

        # iter_var = array[index]
        iter_op = self._make_variable(iter_var)
        self.program.emit(TACOp.ARRAY_ACCESS, iter_op, array, index_temp)

        # Cuerpo del foreach
        self._enter_scope(ctx.block())
        self.visit(ctx.block())
        self._exit_scope()

        # Punto de continue: index++ y volver a chequear la condición
        self.program.emit_label(continue_label)
        self.program.emit(TACOp.ADD, index_temp, index_temp, self._make_constant(1))
        self.program.emit(TACOp.GOTO, arg1=start_label)

        # Salida del foreach
        self.program.emit_label(end_label)
        self.loop_stack.pop()
        return None

    
    def visitBreakStatement(self, ctx: CompiscriptParser.BreakStatementContext):
        # Prioridad: si estamos en un switch, saltar al end_label del switch
        if self.switch_stack:
            self.program.emit(TACOp.GOTO, arg1=self.switch_stack[-1])
            return None

        # Si no, usar el de bucle (while/for/do)
        if self.loop_stack:
            _, break_label = self.loop_stack[-1]
            self.program.emit(TACOp.GOTO, arg1=break_label)
        return None

    
    def visitContinueStatement(self, ctx: CompiscriptParser.ContinueStatementContext):
        """Genera código para continue"""
        if self.loop_stack:
            continue_label, _ = self.loop_stack[-1]
            self.program.emit(TACOp.GOTO, arg1=continue_label)
        return None
    
    def visitReturnStatement(self, ctx: CompiscriptParser.ReturnStatementContext):
        """Genera código para return"""
        if ctx.expression():
            value = self.visit(ctx.expression())
            self.program.emit(TACOp.RETURN, arg1=value)
            self._free_if_temp(value)
        else:
            self.program.emit(TACOp.RETURN)
        return None
    
    # ========== SWITCH STATEMENT ==========
    def visitSwitchStatement(self, ctx: CompiscriptParser.SwitchStatementContext):
        """Genera código para switch con soporte de break"""
        switch_expr = self.visit(ctx.expression())

        end_label = self.program.new_label()
        self.switch_stack.append(end_label)   # para que 'break' lo use

        # Preparamos label para cada case
        case_labels = [self.program.new_label() for _ in ctx.switchCase()]

        has_default   = ctx.defaultCase() is not None
        default_label = self.program.new_label() if has_default else end_label

        # Comparaciones: if (switch_expr == case_value) goto L_case_i
        for i, case in enumerate(ctx.switchCase()):
            case_value = self.visit(case.expression())
            cmp_temp   = self.program.new_temp()
            self.program.emit(TACOp.EQ, cmp_temp, switch_expr, case_value)
            self.program.emit(TACOp.IF_TRUE, arg1=cmp_temp, arg2=case_labels[i])
            self._free_if_temp(cmp_temp)

        # Si no coincide ningún case, ir al default (si existe) o al final
        self.program.emit(TACOp.GOTO, arg1=default_label)

        # Bloques de cada case (fall-through permitido si no hay 'break')
        for i, case in enumerate(ctx.switchCase()):
            self.program.emit_label(case_labels[i])
            for stmt in case.statement():
                self.visit(stmt)

        # Default (opcional)
        if has_default:
            self.program.emit_label(default_label)
            for stmt in ctx.defaultCase().statement():
                self.visit(stmt)

        # Etiqueta de salida (donde saltan los 'break')
        self.program.emit_label(end_label)
        self.switch_stack.pop()
        return None

    
    # ========== FUNCTIONS ==========
    def visitFunctionDeclaration(self, ctx: CompiscriptParser.FunctionDeclarationContext):
        fname = self._id(ctx)
        self.current_function = fname
        self.in_function = True
        
        # CAMBIO: Buscar el símbolo en el scope ACTUAL (puede ser clase o global)
        # Primero intentar en el scope padre actual
        fsym = None
        if self.current_scope.parent:
            fsym = self.current_scope.parent.resolve(fname)
        
        # Si no se encuentra y estamos en una clase, buscar en el scope de la clase
        if not fsym and self.current_class:
            # Buscar el ClassSymbol
            class_sym = self.global_scope.resolve(self.current_class)
            if class_sym and hasattr(class_sym, "_ctx"):
                class_ctx = class_sym._ctx
                if class_ctx in self.scopes_by_ctx:
                    class_scope = self.scopes_by_ctx[class_ctx]
                    fsym = class_scope.resolve(fname)
        
        # Si aún no se encuentra, buscar en global
        if not fsym:
            fsym = self.global_scope.resolve(fname)
        
        frame_size = getattr(fsym, 'frame_size', 0) if fsym else 0
        
        print(f"DEBUG: Función {fname}, fsym={fsym}, frame_size={frame_size}")
        if fsym:
            print(f"  params_size={getattr(fsym, 'params_size', 'NO TIENE')}")
            print(f"  locals_size={getattr(fsym, 'locals_size', 'NO TIENE')}")
            print(f"  frame_size={getattr(fsym, 'frame_size', 'NO TIENE')}")
        
        # Emitir inicio de función
        func_op = self._make_variable(fname)
        self.program.emit(TACOp.FUNC_START, arg1=func_op)
        
        # Emitir ENTER con tamaño del frame
        self.program.emit(TACOp.ENTER, arg1=self._make_constant(frame_size))
        
        # Entrar al scope de la función
        self._enter_scope(ctx)
        
        # Cuerpo de la función
        self.visit(ctx.block())
        
        # Emitir LEAVE antes de finalizar
        self.program.emit(TACOp.LEAVE)
        
        # Emitir fin de función
        self.program.emit(TACOp.FUNC_END, arg1=func_op)
        
        self._exit_scope()
        self.current_function = None
        self.in_function = False
        return None
    
    # ========== CLASSES ==========
    def visitClassDeclaration(self, ctx: CompiscriptParser.ClassDeclarationContext):
        """Genera código para declaración de clase"""
        class_name = self._id(ctx)
        self.current_class = class_name
        
        # Por ahora, las clases se manejan como estructuras
        # Los métodos se generan como funciones con prefijo
        
        self._enter_scope(ctx)
        
        # Visitar miembros de la clase
        for member in ctx.classMember():
            if member.functionDeclaration():
                # Los métodos se generan con prefijo de clase
                self.visit(member.functionDeclaration())
            # Los campos se manejan dinámicamente
        
        self._exit_scope()
        self.current_class = None
        return None
    
    # ========== EXPRESSIONS ==========
    def visitExpression(self, ctx: CompiscriptParser.ExpressionContext):
        """Visita una expresión genérica"""
        return self.visit(ctx.assignmentExpr())
    
    def visitAssignExpr(self, ctx: CompiscriptParser.AssignExprContext):
        rhs = self.visit(ctx.assignmentExpr())

        # Analizamos el LHS (leftHandSide = primaryAtom + suffixOp*)
        lhs_ctx = ctx.lhs
        suffixes = list(lhs_ctx.suffixOp())
        base_atom = lhs_ctx.primaryAtom()

        # Caso A: asignación a índice de arreglo:  <id> '[' expr ']'
        if suffixes and suffixes[-1].getChild(0).getText() == '[':
            array_name = self._id(base_atom)  # nombre del arreglo
            array_op = self._make_variable(array_name)
            index = self.visit(suffixes[-1].expression())
            self.program.emit(TACOp.ARRAY_ASSIGN, array_op, index, rhs)
            self._free_if_temp(index, rhs)
            return array_op  # valor de la expr es el lvalue (no se usa en stmt, pero ok)

        # Caso B: identificador simple
        if not suffixes and hasattr(base_atom, "Identifier"):
            var_name = self._id(base_atom)
            var_op = self._make_variable(var_name)
            self.program.emit(TACOp.ASSIGN, var_op, rhs)
            self._free_if_temp(rhs)
            return var_op

        # Otros lvalues (propiedades) los cubre PropertyAssignExpr por gramática;
        # aquí devolvemos rhs tal cual para no duplicar efectos.
        return rhs

    
    def visitExprNoAssign(self, ctx: CompiscriptParser.ExprNoAssignContext):
        """Visita expresión sin asignación"""
        return self.visit(ctx.conditionalExpr())
    
    def visitTernaryExpr(self, ctx: CompiscriptParser.TernaryExprContext):
        """Genera código para operador ternario"""
        if len(ctx.expression()) == 0:
            # No hay ternario, solo logical or
            return self.visit(ctx.logicalOrExpr())
        
        # cond ? expr1 : expr2
        cond = self.visit(ctx.logicalOrExpr())
        
        result = self.program.new_temp()
        else_label = self.program.new_label()
        end_label = self.program.new_label()
        
        self.program.emit(TACOp.IF_FALSE, arg1=cond, arg2=else_label)
        
        # Rama then
        then_value = self.visit(ctx.expression(0))
        self.program.emit(TACOp.ASSIGN, result, then_value)
        self.program.emit(TACOp.GOTO, arg1=end_label)
        
        # Rama else
        self.program.emit_label(else_label)
        else_value = self.visit(ctx.expression(1))
        self.program.emit(TACOp.ASSIGN, result, else_value)
        
        self.program.emit_label(end_label)
        self._free_if_temp(cond, then_value, else_value)
        return result
    
    # ========== BINARY OPERATIONS ==========
    def visitLogicalOrExpr(self, ctx: CompiscriptParser.LogicalOrExprContext):
        """Genera código para OR lógico con cortocircuito"""
        operands = ctx.logicalAndExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        result = self.program.new_temp()
        true_label = self.program.new_label()
        end_label = self.program.new_label()
        
        last_val = None
        for i, operand in enumerate(operands):
            op_result = self.visit(operand)
            if i < len(operands) - 1:
                # Si es true, cortocircuito
                self.program.emit(TACOp.IF_TRUE, arg1=op_result, arg2=true_label)
                self._free_if_temp(op_result)
            else:
                # Último operando
                self.program.emit(TACOp.ASSIGN, result, op_result)
                last_val = op_result
        
        self.program.emit(TACOp.GOTO, arg1=end_label)
        
        self.program.emit_label(true_label)
        self.program.emit(TACOp.ASSIGN, result, self._make_constant(True))
        
        self.program.emit_label(end_label)
        self._free_if_temp(last_val)
        return result
    
    def visitLogicalAndExpr(self, ctx: CompiscriptParser.LogicalAndExprContext):
        """Genera código para AND lógico con cortocircuito"""
        operands = ctx.equalityExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        result = self.program.new_temp()
        false_label = self.program.new_label()
        end_label = self.program.new_label()
        
        last_val = None
        for i, operand in enumerate(operands):
            op_result = self.visit(operand)
            if i < len(operands) - 1:
                # Si es false, cortocircuito
                self.program.emit(TACOp.IF_FALSE, arg1=op_result, arg2=false_label)
                self._free_if_temp(op_result)
            else:
                # Último operando
                self.program.emit(TACOp.ASSIGN, result, op_result)
                last_val = op_result
        
        self.program.emit(TACOp.GOTO, arg1=end_label)
        
        self.program.emit_label(false_label)
        self.program.emit(TACOp.ASSIGN, result, self._make_constant(False))
        
        self.program.emit_label(end_label)
        self._free_if_temp(last_val)
        return result
    
    def visitEqualityExpr(self, ctx: CompiscriptParser.EqualityExprContext):
        """Genera código para operaciones de igualdad"""
        operands = ctx.relationalExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        left = self.visit(operands[0])
        for i in range(1, len(operands)):
            right = self.visit(operands[i])
            result = self.program.new_temp()
            
            # Determinar operador
            op_text = ctx.getChild(2*i-1).getText()
            if op_text == '==':
                self.program.emit(TACOp.EQ, result, left, right)
            else:  # !=
                self.program.emit(TACOp.NE, result, left, right)
            
            self._free_if_temp(left, right)
            left = result
        
        return left
    
    def visitRelationalExpr(self, ctx: CompiscriptParser.RelationalExprContext):
        """Genera código para operaciones relacionales"""
        operands = ctx.additiveExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        left = self.visit(operands[0])
        for i in range(1, len(operands)):
            right = self.visit(operands[i])
            result = self.program.new_temp()
            
            # Determinar operador
            op_text = ctx.getChild(2*i-1).getText()
            op_map = {
                '<': TACOp.LT,
                '<=': TACOp.LE,
                '>': TACOp.GT,
                '>=': TACOp.GE
            }
            self.program.emit(op_map[op_text], result, left, right)
            self._free_if_temp(left, right)
            left = result
        
        return left
    
    def visitAdditiveExpr(self, ctx: CompiscriptParser.AdditiveExprContext):
        """Genera código para suma y resta"""
        operands = ctx.multiplicativeExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        result = self.visit(operands[0])
        for i in range(1, len(operands)):
            right = self.visit(operands[i])
            temp = self.program.new_temp()
            
            # Determinar operador
            op_text = ctx.getChild(2*i-1).getText()
            if op_text == '+':
                self.program.emit(TACOp.ADD, temp, result, right)
            else:  # -
                self.program.emit(TACOp.SUB, temp, result, right)
            
            self._free_if_temp(result, right)
            result = temp
        
        return result
    
    def visitMultiplicativeExpr(self, ctx: CompiscriptParser.MultiplicativeExprContext):
        """Genera código para multiplicación, división y módulo"""
        operands = ctx.unaryExpr()
        if len(operands) == 1:
            return self.visit(operands[0])
        
        result = self.visit(operands[0])
        for i in range(1, len(operands)):
            right = self.visit(operands[i])
            temp = self.program.new_temp()
            
            # Determinar operador
            op_text = ctx.getChild(2*i-1).getText()
            op_map = {
                '*': TACOp.MUL,
                '/': TACOp.DIV,
                '%': TACOp.MOD
            }
            self.program.emit(op_map[op_text], temp, result, right)
            self._free_if_temp(result, right)
            result = temp
        
        return result
    
    def visitUnaryExpr(self, ctx: CompiscriptParser.UnaryExprContext):
        """Genera código para operaciones unarias"""
        if ctx.getChildCount() == 2:
            op = ctx.getChild(0).getText()
            operand = self.visit(ctx.getChild(1))
            result = self.program.new_temp()
            
            if op == '!':
                self.program.emit(TACOp.NOT, result, operand)
            elif op == '-':
                self.program.emit(TACOp.NEG, result, operand)
            
            self._free_if_temp(operand)
            return result
        
        return self.visit(ctx.primaryExpr())
    
    # ========== PRIMARY EXPRESSIONS ==========
    def visitPrimaryExpr(self, ctx: CompiscriptParser.PrimaryExprContext):
        """Visita expresión primaria"""
        if ctx.literalExpr():
            return self.visit(ctx.literalExpr())
        elif ctx.leftHandSide():
            return self.visit(ctx.leftHandSide())
        elif ctx.expression():
            # Paréntesis
            return self.visit(ctx.expression())
        return None
    
    def visitLiteralExpr(self, ctx: CompiscriptParser.LiteralExprContext):
        """Genera código para literales"""
        text = ctx.getText()
        
        if text == 'true':
            return self._make_constant(True, 'boolean')
        elif text == 'false':
            return self._make_constant(False, 'boolean')
        elif text == 'null':
            return self._make_constant(None, 'null')
        elif ctx.arrayLiteral():
            return self.visit(ctx.arrayLiteral())
        elif text[0] == '"' and text[-1] == '"':
            # String literal
            return self._make_constant(text[1:-1], 'string')
        else:
            # Integer literal
            try:
                value = int(text)
                return self._make_constant(value, 'integer')
            except:
                return self._make_constant(text, 'unknown')
    
    def visitArrayLiteral(self, ctx: CompiscriptParser.ArrayLiteralContext):
        """Genera código para literales de array"""
        temp = self.program.new_temp()
        
        # Crear nuevo array
        size = len(ctx.expression())
        size_op = self._make_constant(size)
        self.program.emit(TACOp.NEW, temp, size_op)
        
        # Inicializar elementos
        for i, expr in enumerate(ctx.expression()):
            value = self.visit(expr)
            index_op = self._make_constant(i)
            self.program.emit(TACOp.ARRAY_ASSIGN, temp, index_op, value)
            self._free_if_temp(value)
        
        return temp
    
    def visitLeftHandSide(self, ctx: CompiscriptParser.LeftHandSideContext):
        """Visita el lado izquierdo con sufijos"""
        base = self.visit(ctx.primaryAtom())
        
        # Aplicar sufijos
        for suffix in ctx.suffixOp():
            base = self._apply_suffix(base, suffix)
        
        return base
    
    def visitIdentifierExpr(self, ctx: CompiscriptParser.IdentifierExprContext):
        """Visita un identificador usando FP[offset] si está en función"""
        name = ctx.Identifier().getText()
        sym = self.current_scope.resolve(name)
        
        if not sym:
            return self._make_variable(name)
        
        # Si estamos en función y tiene offset: usar FP[offset]
        if self.in_function and hasattr(sym, 'offset') and sym.offset is not None:
            offset = sym.offset
            fp_ref = TACOperand(f"FP[{offset}]")
            
            # Cargar valor desde FP[offset]
            temp = self.program.new_temp()
            # CORRECTO: result, arg1
            self.program.emit(TACOp.DEREF, result=temp, arg1=fp_ref)
            return temp
        
        # Variable global: usar dirección de memoria si existe
        if name in self.global_addrs:
            addr_op = TACOperand(self.global_addrs[name])
            temp = self.program.new_temp()
            # CORRECTO: result, arg1
            self.program.emit(TACOp.DEREF, result=temp, arg1=addr_op)
            return temp
        
        # Fallback: referencia directa
        return self._make_variable(name)
    
    def visitNewExpr(self, ctx: CompiscriptParser.NewExprContext):
        """Genera código para new"""
        class_name = self._id(ctx)
        temp = self.program.new_temp()
        
        # Crear nueva instancia
        class_op = self._make_variable(class_name)
        self.program.emit(TACOp.NEW, temp, class_op)
        
        # Si hay argumentos, llamar al constructor
        if ctx.arguments():
            # Pasar argumentos (y registrar para liberar luego)
            arg_values: List[TACOperand] = []
            for expr in ctx.arguments().expression():
                arg = self.visit(expr)
                self.program.emit(TACOp.PARAM, arg1=arg)
                arg_values.append(arg)
            
            # Llamar constructor
            ctor_name = f"{class_name}.constructor"
            ctor_op = self._make_variable(ctor_name)
            num_args = len(arg_values)
            self.program.emit(TACOp.CALL, arg1=ctor_op, arg2=self._make_constant(num_args))
            
            # Liberar args temporales
            self._free_if_temp(*arg_values)
        
        return temp
    
    def visitThisExpr(self, ctx: CompiscriptParser.ThisExprContext):
        """Genera código para this"""
        return self._make_variable("this")
    
    def _apply_suffix(self, base: TACOperand, suffix_ctx) -> TACOperand:
        """Aplica un sufijo a una expresión base"""
        first_token = suffix_ctx.getChild(0).getText()
        
        if first_token == '(':
            # Llamada a función
            return self._apply_call(base, suffix_ctx)
        elif first_token == '[':
            # Acceso a array
            return self._apply_index(base, suffix_ctx)
        elif first_token == '.':
            # Acceso a propiedad
            return self._apply_property(base, suffix_ctx)
        
        return base
    
    def _apply_call(self, func: TACOperand, call_ctx) -> TACOperand:
        """Aplica una llamada de función con PUSH/POP"""
        # Evaluar y hacer PUSH de argumentos (en orden inverso)
        args_vals = []
        if call_ctx.arguments():
            args_vals = [self.visit(expr) for expr in call_ctx.arguments().expression()]
        
        # PUSH argumentos en orden inverso (convención de stack)
        for arg in reversed(args_vals):
            self.program.emit(TACOp.PUSH, arg1=arg)
        
        num_args = len(args_vals)
        
        # Llamar función - CORRECCIÓN AQUÍ
        num_args_op = self._make_constant(num_args)
        self.program.emit(TACOp.CALL, arg1=func, arg2=num_args_op)  # ← func primero, luego num_args
        
        # Ajustar stack pointer después de llamada
        if num_args > 0:
            bytes_to_pop = num_args * 4
            self.program.emit(TACOp.ADD_SP, arg1=self._make_constant(bytes_to_pop))
        
        # POP resultado
        result = self.program.new_temp()
        self.program.emit(TACOp.POP, result=result)
        
        # Liberar args temporales
        self._free_if_temp(*args_vals)
        return result
    
    def _apply_index(self, array: TACOperand, index_ctx) -> TACOperand:
        """Aplica acceso a índice de array"""
        index = self.visit(index_ctx.expression())
        result = self.program.new_temp()
        self.program.emit(TACOp.ARRAY_ACCESS, result, array, index)
        # index consumido
        self._free_if_temp(index)
        return result
    
    def _apply_property(self, obj: TACOperand, prop_ctx) -> TACOperand:
        """Aplica acceso a propiedad"""
        prop_name = self._id(prop_ctx)
        prop_op = self._make_constant(prop_name)
        result = self.program.new_temp()
        self.program.emit(TACOp.FIELD_ACCESS, result, obj, prop_op)
        return result
    
    # ========== TRY-CATCH ==========
    def visitTryCatchStatement(self, ctx: CompiscriptParser.TryCatchStatementContext):
        """Genera código para try-catch (simplificado)"""
        # Por simplicidad, generamos el try block normal
        # y saltamos el catch si no hay excepción
        
        catch_label = self.program.new_label()
        end_label = self.program.new_label()
        
        # Try block
        self.visit(ctx.block(0))
        self.program.emit(TACOp.GOTO, arg1=end_label)
        
        # Catch block
        self.program.emit_label(catch_label)
        error_var = self._id(ctx)
        # Asignar error a la variable (simplificado)
        error_op = self._make_variable(error_var)
        self.visit(ctx.block(1))
        
        self.program.emit_label(end_label)
        return None