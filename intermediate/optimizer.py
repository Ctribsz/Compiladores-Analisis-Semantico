"""
Optimizador de código intermedio TAC
Implementa optimizaciones locales básicas (robustas a strings/labels)
"""
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from .tac import TACOp, TACOperand, TACInstruction, TACProgram

# --------- helpers seguros ---------
def _is_const(x) -> bool:
    # True sólo si es TACOperand con bandera is_constant
    return getattr(x, "is_constant", False)

def _const_val(x):
    # Si es TACOperand, devuelve .value; si no, lo retorna tal cual (str/int/bool/None)
    return getattr(x, "value", x)

def _is_temp_name(x) -> bool:
    s = str(_const_val(x))
    return isinstance(s, str) and s.startswith("t")
# -----------------------------------


class TACOptimizer:
    """Optimizador de código TAC"""
    
    def __init__(self, program: TACProgram):
        self.program = program
        self.optimized_instructions: List[TACInstruction] = []
    
    def optimize(self) -> TACProgram:
        """Aplica todas las optimizaciones disponibles"""
        instructions = self.program.instructions.copy()
        
        instructions = self.constant_folding(instructions)
        instructions = self.constant_propagation(instructions)
        instructions = self.dead_code_elimination(instructions)
        instructions = self.algebraic_simplification(instructions)
        instructions = self.remove_redundant_jumps(instructions)
        
        # Crear nuevo programa optimizado
        optimized = TACProgram()
        optimized.instructions = instructions
        optimized.temp_counter = self.program.temp_counter
        optimized.label_counter = self.program.label_counter
        return optimized
    
    # ---------------- passes ----------------
    def constant_folding(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Evalúa expresiones con operandos constantes en tiempo de compilación"""
        result: List[TACInstruction] = []

        control_ops = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.FUNC_START, TACOp.FUNC_END, TACOp.RETURN, TACOp.PARAM,
            TACOp.PRINT, TACOp.CALL
        }
        
        for inst in instructions:
            if inst.op in control_ops:
                result.append(inst)
                continue

            # Aritméticas
            if inst.op in [TACOp.ADD, TACOp.SUB, TACOp.MUL, TACOp.DIV, TACOp.MOD]:
                if _is_const(inst.arg1) and _is_const(inst.arg2):
                    val1 = _const_val(inst.arg1)
                    val2 = _const_val(inst.arg2)
                    if isinstance(val1, int) and isinstance(val2, int):
                        if inst.op == TACOp.ADD:
                            v = val1 + val2
                        elif inst.op == TACOp.SUB:
                            v = val1 - val2
                        elif inst.op == TACOp.MUL:
                            v = val1 * val2
                        elif inst.op == TACOp.DIV and val2 != 0:
                            v = val1 // val2
                        elif inst.op == TACOp.MOD and val2 != 0:
                            v = val1 % val2
                        else:
                            result.append(inst); continue
                        result.append(TACInstruction(TACOp.ASSIGN, inst.result, TACOperand(v, is_constant=True)))
                        continue
                result.append(inst); continue

            # Relacionales
            if inst.op in [TACOp.LT, TACOp.LE, TACOp.GT, TACOp.GE, TACOp.EQ, TACOp.NE]:
                if _is_const(inst.arg1) and _is_const(inst.arg2):
                    v1 = _const_val(inst.arg1)
                    v2 = _const_val(inst.arg2)
                    if isinstance(v1, int) and isinstance(v2, int):
                        if inst.op == TACOp.LT: v = v1 < v2
                        elif inst.op == TACOp.LE: v = v1 <= v2
                        elif inst.op == TACOp.GT: v = v1 > v2
                        elif inst.op == TACOp.GE: v = v1 >= v2
                        elif inst.op == TACOp.EQ: v = v1 == v2
                        else: v = v1 != v2
                        result.append(TACInstruction(TACOp.ASSIGN, inst.result, TACOperand(v, is_constant=True)))
                        continue
                result.append(inst); continue

            # Unarios
            if inst.op == TACOp.NEG:
                if _is_const(inst.arg1):
                    v = _const_val(inst.arg1)
                    if isinstance(v, int):
                        result.append(TACInstruction(TACOp.ASSIGN, inst.result, TACOperand(-v, is_constant=True)))
                        continue
                result.append(inst); continue

            if inst.op == TACOp.NOT:
                if _is_const(inst.arg1):
                    v = _const_val(inst.arg1)
                    if isinstance(v, bool):
                        result.append(TACInstruction(TACOp.ASSIGN, inst.result, TACOperand((not v), is_constant=True)))
                        continue
                result.append(inst); continue

            # Por defecto
            result.append(inst)
        
        return result
    
    def constant_propagation(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Propaga valores constantes conocidos"""
        constants: Dict[str, TACOperand] = {}
        result: List[TACInstruction] = []
        
        for inst in instructions:
            new_inst = inst

            # Sustituir operandos por constantes conocidas (arg1, luego arg2)
            if inst.arg1 and not _is_const(inst.arg1):
                key = str(inst.arg1)
                if key in constants:
                    new_inst = TACInstruction(inst.op, inst.result, constants[key], inst.arg2)
            if new_inst.arg2 and not _is_const(new_inst.arg2):
                key = str(new_inst.arg2)
                if key in constants:
                    new_inst = TACInstruction(new_inst.op, new_inst.result, new_inst.arg1, constants[key])
            
            # Registrar nuevas constantes para ASSIGN var = const
            if inst.op == TACOp.ASSIGN and _is_const(inst.arg1):
                if inst.result and not getattr(inst.result, "is_temp", False):
                    constants[str(inst.result)] = inst.arg1
            
            # Si la variable resultado se modifica con otra op, deja de ser constante
            if inst.result and str(inst.result) in constants and inst.op != TACOp.ASSIGN:
                del constants[str(inst.result)]
            
            result.append(new_inst)
        
        return result
    
    def dead_code_elimination(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Elimina código muerto (variables no usadas)"""
        used_vars: Set[str] = set()
        
        # 1) marcar usos directos
        for inst in instructions:
            if inst.op in [TACOp.PRINT, TACOp.RETURN, TACOp.IF_TRUE, TACOp.IF_FALSE]:
                if inst.arg1 is not None:
                    used_vars.add(str(inst.arg1))
            if inst.op == TACOp.PARAM:
                if inst.arg1 is not None:
                    used_vars.add(str(inst.arg1))
            if inst.arg1 is not None and inst.op != TACOp.ASSIGN:
                used_vars.add(str(inst.arg1))
            if inst.arg2 is not None:
                used_vars.add(str(inst.arg2))
        
        # 2) propagar hacia atrás (muy simplificado)
        changed = True
        while changed:
            changed = False
            for inst in reversed(instructions):
                if inst.result is not None and str(inst.result) in used_vars:
                    if inst.arg1 is not None and str(inst.arg1) not in used_vars:
                        used_vars.add(str(inst.arg1)); changed = True
                    if inst.arg2 is not None and str(inst.arg2) not in used_vars:
                        used_vars.add(str(inst.arg2)); changed = True
        
        # 3) eliminar asignaciones no usadas, pero conservar side-effects/control
        keep_ops = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.PRINT, TACOp.RETURN, TACOp.PARAM, TACOp.CALL,
            TACOp.FUNC_START, TACOp.FUNC_END, TACOp.ARRAY_ASSIGN, TACOp.FIELD_ASSIGN
        }
        result: List[TACInstruction] = []
        for inst in instructions:
            if inst.op in keep_ops:
                result.append(inst)
            elif inst.result is not None and str(inst.result) in used_vars:
                result.append(inst)
            # else: muerto → se elimina
        return result
    
    def algebraic_simplification(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Simplificaciones algebraicas básicas"""
        result: List[TACInstruction] = []

        control_ops = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.FUNC_START, TACOp.FUNC_END, TACOp.RETURN, TACOp.PARAM,
            TACOp.PRINT, TACOp.CALL
        }
        
        for inst in instructions:
            if inst.op in control_ops:
                result.append(inst); continue

            # x + 0 = x, 0 + x = x
            if inst.op == TACOp.ADD:
                if self._is_zero(inst.arg2):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg1))
                elif self._is_zero(inst.arg1):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg2))
                else:
                    result.append(inst)
                continue
            
            # x - 0 = x
            if inst.op == TACOp.SUB:
                if self._is_zero(inst.arg2):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg1))
                else:
                    result.append(inst)
                continue
            
            # x * 0 = 0, 0 * x = 0;  x * 1 = x, 1 * x = x
            if inst.op == TACOp.MUL:
                if self._is_zero(inst.arg1) or self._is_zero(inst.arg2):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, TACOperand(0, is_constant=True)))
                elif self._is_one(inst.arg2):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg1))
                elif self._is_one(inst.arg1):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg2))
                else:
                    result.append(inst)
                continue
            
            # x / 1 = x
            if inst.op == TACOp.DIV:
                if self._is_one(inst.arg2):
                    result.append(TACInstruction(TACOp.ASSIGN, inst.result, inst.arg1))
                else:
                    result.append(inst)
                continue
            
            # por defecto
            result.append(inst)
        
        return result
    
    def remove_redundant_jumps(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Elimina saltos redundantes"""
        result: List[TACInstruction] = []
        
        for i, inst in enumerate(instructions):
            # Eliminar GOTO a la etiqueta inmediata siguiente
            if inst.op == TACOp.GOTO:
                if i + 1 < len(instructions) and instructions[i + 1].op == TACOp.LABEL:
                    if str(inst.arg1) == str(instructions[i + 1].arg1):
                        continue  # quitar el GOTO redundante
            
            # Eliminar etiquetas no referenciadas
            if inst.op == TACOp.LABEL:
                label_name = str(inst.arg1)
                referenced = False
                for other in instructions:
                    if other is inst: 
                        continue
                    if other.arg1 is not None and str(other.arg1) == label_name:
                        referenced = True; break
                    if other.arg2 is not None and str(other.arg2) == label_name:
                        referenced = True; break
                if not referenced:
                    continue  # quitar etiqueta huérfana
            
            result.append(inst)
        
        return result
    
    # -------- helpers de valor ----------
    def _is_constant(self, operand: Optional[TACOperand]) -> bool:
        """Conserva compatibilidad con código existente (usa wrapper)"""
        return _is_const(operand)
    
    def _is_zero(self, operand: Optional[TACOperand]) -> bool:
        """Verifica si un operando es cero"""
        return _is_const(operand) and _const_val(operand) == 0
    
    def _is_one(self, operand: Optional[TACOperand]) -> bool:
        """Verifica si un operando es uno"""
        return _is_const(operand) and _const_val(operand) == 1