"""
Optimizador de código intermedio TAC
Implementa optimizaciones locales básicas + optimizaciones quirúrgicas avanzadas
"""
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from .tac import TACOp, TACOperand, TACInstruction, TACProgram

# --------- helpers seguros ---------
def _is_const(x) -> bool:
    return getattr(x, "is_constant", False)

def _const_val(x):
    return getattr(x, "value", x)

def _is_temp_name(x) -> bool:
    """Chequea si un operando es un temporal (ej: t1, tt1, t_loop)"""
    s = str(_const_val(x))
    # La regla simple: si empieza con 't' y no es 'true' o 'this', es un temporal.
    return isinstance(s, str) and s.startswith("t") and s not in ("true", "this")
# -----------------------------------

@dataclass
class LivenessInfo:
    """Información de vida de un temporal"""
    first_def: int
    last_use: int
    uses: Set[int]
    defs: Set[int]


class TACOptimizer:
    """Optimizador de código TAC"""
    
    def __init__(self, program: TACProgram):
        self.program = program
        self.optimized_instructions: List[TACInstruction] = []
    
    def optimize(self) -> TACProgram:
        instructions = self.program.instructions.copy()
        
        # Validar y corregir TAC malformado
        instructions = self.validate_tac(instructions)

        # ========== FASE 1: Pase algebraico inicial ==========
        print("📊 Fase 1: Constant folding y propagación...")
        instructions = self.constant_folding(instructions)
        instructions = self.enhanced_constant_folding(instructions)
        instructions = self.constant_propagation(instructions)
        instructions = self.constant_folding(instructions)
        instructions = self.algebraic_simplification(instructions)
        
        # ========== FASE 2: Optimizaciones quirúrgicas ==========
        print("🔧 Fase 2: Optimizaciones quirúrgicas...")
        original_count = len(instructions)
        instructions = self._surgical_optimize(instructions)
        surgical_count = len(instructions)
        print(f"   Eliminadas {original_count - surgical_count} instrucciones redundantes")
        
# ========== FASE 3: Limpieza y pases finales ==========
        print("🧹 Fase 3: Limpieza final...")
        
        print("   -> (3.1) Copy propagation...")
        instructions = self.copy_propagation(instructions)
        
        print("   -> (3.2) Constant cleanup...")
        instructions = self.constant_cleanup(instructions)
        
        print("   -> (3.3) Remove unused constant loads...")
        instructions = self.remove_unused_constant_loads(instructions)
        
        print("   -> (3.4) Optimize memory loads...")
        instructions = self.optimize_memory_loads(instructions)
        
        print("   -> (3.5) Eliminate copy chains...")
        instructions = self.eliminate_copy_chains(instructions)
        
        print("   -> (3.6) Remove redundant stores...")
        instructions = self.remove_redundant_stores(instructions)
        
        print("   -> (3.7) Dead code elimination...")
        instructions = self.dead_code_elimination(instructions)
        
        print("   -> (3.8) Remove redundant moves...")
        instructions = self.remove_redundant_moves(instructions)
        
        print("   -> (3.9) Strength reduction...")
        instructions = self.strength_reduction(instructions)
        
        print("   -> (3.10) Remove redundant jumps...")
        instructions = self.remove_redundant_jumps(instructions)
        
        print("   -> (3.11) Limpieza final terminada.")

        out = TACProgram()
        out.instructions = instructions
        
        # Contar temporales usados
        max_temp = 0
        for inst in instructions:
            for op in [inst.result, inst.arg1, inst.arg2]:
                if op and _is_temp_name(op):
                    try:
                        num = int(str(op).replace('t', ''))
                        max_temp = max(max_temp, num)
                    except:
                        pass
        
        out.temp_counter = max_temp
        out.label_counter = self.program.label_counter
        
        print(f"✅ Optimización completa: {self.program.temp_counter} → {max_temp} temporales")
        return out
    
    def _copy_operand_with_type(self, operand):  
        """Crea una copia de un operando preservando su tipo."""
        if operand is None:
            return None
        if isinstance(operand, TACOperand):
            return TACOperand(
                value=operand.value,
                is_temp=operand.is_temp,
                is_constant=operand.is_constant,
                is_label=operand.is_label,
                typ=operand.typ
            )
        else:
            return TACOperand(operand)

    def _surgical_optimize(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Aplica optimizaciones quirúrgicas específicas"""
        liveness = self._compute_liveness(instructions)
        
        # Optimización 1: Eliminar temporales de uso único
        instructions = self._opt_single_use(instructions, liveness)
        liveness = self._compute_liveness(instructions)
        
        # Optimización 2: Load forwarding
        instructions = self._opt_load_forwarding(instructions, liveness)
        liveness = self._compute_liveness(instructions)
        
        # Optimización 3: Renumeración óptima
        instructions = self._opt_temp_renaming(instructions, liveness)
        
        return instructions
    
    def _compute_liveness(self, instructions: List[TACInstruction]) -> Dict[str, LivenessInfo]:
        """Calcula información de vida de temporales"""
        info = {}
        
        for i, inst in enumerate(instructions):
            # Definiciones
            if inst.result and _is_temp_name(inst.result):
                name = str(inst.result)
                if name not in info:
                    info[name] = LivenessInfo(i, i, set(), set())
                info[name].defs.add(i)
                info[name].first_def = min(info[name].first_def, i)
            
            # Usos
            for arg in [inst.arg1, inst.arg2]:
                if arg and _is_temp_name(arg):
                    name = str(arg)
                    if name not in info:
                        info[name] = LivenessInfo(0, i, set(), set())
                    info[name].uses.add(i)
                    info[name].last_use = max(info[name].last_use, i)
        
        return info
    
    def _opt_single_use(self, instructions: List[TACInstruction], 
                        liveness: Dict[str, LivenessInfo]) -> List[TACInstruction]:
        """Elimina temporales de uso único"""
        result = []
        single_use = {}
        
        # Identificar candidatos
        for name, info in liveness.items():
            if len(info.uses) == 1 and len(info.defs) == 1:
                def_idx = list(info.defs)[0]
                use_idx = list(info.uses)[0]
                
                # Solo si están cerca y no cruzan boundaries
                if 0 < use_idx - def_idx <= 5:
                    # Verificar que no hay labels/calls entre medio
                    safe = True
                    for j in range(def_idx + 1, use_idx):
                        if instructions[j].op in [TACOp.LABEL, TACOp.CALL, 
                                                   TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE]:
                            safe = False
                            break
                    
                    if safe:
                        single_use[name] = def_idx
        
        skip_indices = set()
        replacements = {}
        
        for i, inst in enumerate(instructions):
            if (inst.result and str(inst.result) in single_use and
                single_use[str(inst.result)] == i):
                
                # Solo optimizar casos seguros
                if inst.op == TACOp.DEREF:
                    replacements[str(inst.result)] = inst.arg1
                    skip_indices.add(i)
                    continue
                elif inst.op == TACOp.ASSIGN and inst.arg1:
                    # Solo si arg1 no es un temporal que va a morir
                    if not _is_temp_name(inst.arg1) or str(inst.arg1) not in single_use:
                        replacements[str(inst.result)] = inst.arg1
                        skip_indices.add(i)
                        continue
        
        # Aplicar reemplazos
        for i, inst in enumerate(instructions):
            if i in skip_indices:
                continue
            
            a1 = inst.arg1
            a2 = inst.arg2
            
            if a1 and str(a1) in replacements:
                a1 = replacements[str(a1)]
            if a2 and str(a2) in replacements:
                a2 = replacements[str(a2)]
            
            result.append(TACInstruction(inst.op, self._copy_operand_with_type(inst.result), 
                                         self._copy_operand_with_type(a1), 
                                         self._copy_operand_with_type(a2)))
        
        return result
    
    def _opt_load_forwarding(self, instructions: List[TACInstruction],
                            liveness: Dict[str, LivenessInfo]) -> List[TACInstruction]:
        """Forward de cargas desde memoria - versión mejorada"""
        result = []
        memory_map = {}  # addr -> (temp, idx)
        
        for i, inst in enumerate(instructions):
            # Invalidar en operaciones peligrosas
            if inst.op in [TACOp.CALL, TACOp.FIELD_ASSIGN, TACOp.ARRAY_ASSIGN,
                          TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE]:
                memory_map.clear()
                result.append(inst)
                continue
            
            # Store: addr = temp
            if (inst.op == TACOp.ASSIGN and 
                inst.result and str(inst.result).startswith("0x") and
                inst.arg1 and _is_temp_name(inst.arg1)):
                
                memory_map[str(inst.result)] = (str(inst.arg1), i)
                result.append(inst)
                continue
            
            # Load: temp = @addr
            if (inst.op == TACOp.DEREF and
                inst.arg1 and str(inst.arg1).startswith("0x")):
                
                addr = str(inst.arg1)
                
                if addr in memory_map:
                    prev_temp, write_idx = memory_map[addr]
                    
                    # Verificar que el temporal siga vivo
                    if prev_temp in liveness:
                        info = liveness[prev_temp]
                        
                        # Forwarding si el temporal está vivo Y no fue modificado
                        if info.last_use >= i and write_idx < i:
                            # Caso especial: si es el mismo temporal, eliminar la carga
                            if str(inst.result) == prev_temp:
                                continue
                            else:
                                # Forwarding: usar el temporal directamente
                                result.append(TACInstruction(
                                    TACOp.ASSIGN, 
                                    self._copy_operand_with_type(inst.result), 
                                    self._copy_operand_with_type(TACOperand(prev_temp, typ=inst.arg1.typ if hasattr(inst.arg1, 'typ') else None))
                                ))
                                continue
                
                result.append(inst)
                continue
            
            result.append(inst)
        
        return result

    # =================== NUEVOS PASES FINALES ===================
    def constant_cleanup(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Limpia asignaciones de constantes no usadas, fortaleciendo el uso directo
        de constantes en vez de temporales intermedios que se pierden.
        """
        result: List[TACInstruction] = []
        const_temps: Dict[str, TACOperand] = {}
        
        for inst in instructions:
            # Resetear en boundaries
            if inst.op in [TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
                           TACOp.CALL, TACOp.FUNC_START, TACOp.FUNC_END]:
                const_temps.clear()
                result.append(inst)
                continue
            
            # Registrar: temp = constante
            if (inst.op == TACOp.ASSIGN and 
                inst.result and _is_temp_name(inst.result) and
                inst.arg1 and _is_const(inst.arg1)):
                const_temps[str(inst.result)] = inst.arg1
                result.append(inst)
                continue
            
            # Sustituir uso de temp por constante
            a1 = inst.arg1
            a2 = inst.arg2
            if a1 and str(a1) in const_temps:
                a1 = const_temps[str(a1)]
            if a2 and str(a2) in const_temps:
                a2 = const_temps[str(a2)]
            new_inst = TACInstruction(
                inst.op, 
                self._copy_operand_with_type(inst.result), 
                self._copy_operand_with_type(a1), 
                self._copy_operand_with_type(a2)
            )
            
            # Si redefinimos el temp, removerlo del mapa
            if new_inst.result and str(new_inst.result) in const_temps:
                del const_temps[str(new_inst.result)]
            
            result.append(new_inst)
        
        return result

    def remove_unused_constant_loads(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Elimina cargas de constantes que nunca se usan si son redefinidas antes de cualquier uso.
        """
        defs: Dict[str, List[int]] = {}
        uses: Dict[str, Set[int]] = {}
        
        for i, inst in enumerate(instructions):
            # Registrar definiciones
            if inst.result and _is_temp_name(inst.result):
                temp = str(inst.result)
                defs.setdefault(temp, []).append(i)
            # Registrar usos
            for arg in [inst.arg1, inst.arg2]:
                if arg and _is_temp_name(arg):
                    temp = str(arg)
                    uses.setdefault(temp, set()).add(i)
        
        # Identificar definiciones muertas
        dead_indices: Set[int] = set()
        for temp, def_indices in defs.items():
            if len(def_indices) > 1:
                for i, def_idx in enumerate(def_indices[:-1]):
                    inst = instructions[def_idx]
                    if inst.op == TACOp.ASSIGN and _is_const(inst.arg1):
                        next_def = def_indices[i + 1]
                        used_between = any(def_idx < use_idx < next_def for use_idx in uses.get(temp, set()))
                        if not used_between:
                            dead_indices.add(def_idx)
        
        # Filtrar
        result: List[TACInstruction] = []
        for i, inst in enumerate(instructions):
            if i not in dead_indices:
                result.append(inst)
        return result

    def optimize_memory_loads(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Optimiza cargas consecutivas de la misma dirección mientras la memoria no cambie.
        """
        result: List[TACInstruction] = []
        last_load: Dict[str, tuple] = {}
        
        for i, inst in enumerate(instructions):
            # Invalidar en escrituras o calls
            if inst.op in [TACOp.CALL, TACOp.ASSIGN]:
                if inst.result and (str(inst.result).startswith("0x") or str(inst.result).startswith("FP[")):
                    addr = str(inst.result)
                    if addr in last_load:
                        del last_load[addr]
            
            # Invalidar todo en boundaries peligrosos
            if inst.op in [TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
                           TACOp.FUNC_START, TACOp.FUNC_END]:
                last_load.clear()
            
            # Detectar load: temp = @addr
            if inst.op == TACOp.DEREF and inst.arg1 is not None:
                addr = str(inst.arg1)
                if addr in last_load:
                    prev_temp, prev_idx = last_load[addr]
                    result.append(TACInstruction(
                        TACOp.ASSIGN, 
                        self._copy_operand_with_type(inst.result),
                        self._copy_operand_with_type(TACOperand(prev_temp, typ=inst.arg1.typ if hasattr(inst.arg1, 'typ') else None))
                    ))
                    last_load[addr] = (str(inst.result), i)
                    continue
                last_load[addr] = (str(inst.result), i)
            
            result.append(inst)
        
        return result

    def strength_reduction(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Reducción de fuerza: reemplaza operaciones costosas por baratas cuando es seguro.
        """
        result: List[TACInstruction] = []
        for inst in instructions:
            if inst.op == TACOp.MUL:
                # x * 2 → x + x
                if _is_const(inst.arg2) and _const_val(inst.arg2) == 2:
                    result.append(TACInstruction(
                        TACOp.ADD, 
                        self._copy_operand_with_type(inst.result), 
                        self._copy_operand_with_type(inst.arg1), 
                        self._copy_operand_with_type(inst.arg1)
                    ))
                    continue
                # 2 * x → x + x
                if _is_const(inst.arg1) and _const_val(inst.arg1) == 2:
                    result.append(TACInstruction(TACOp.ADD, inst.result, inst.arg2, inst.arg2))
                    continue
            result.append(inst)
        return result

    def eliminate_copy_chains(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Elimina cadenas de copias transitivas dentro de regiones lineales.
        """
        result: List[TACInstruction] = []
        copy_map: Dict[str, str] = {}
        
        for inst in instructions:
            # Resetear en boundaries
            if inst.op in [TACOp.LABEL, TACOp.CALL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE]:
                copy_map.clear()
                result.append(inst)
                continue
            
            # Detectar copia simple t_dst = t_src
            if (inst.op == TACOp.ASSIGN and 
                inst.result and _is_temp_name(inst.result) and
                inst.arg1 and _is_temp_name(inst.arg1)):
                src = str(inst.arg1)
                dst = str(inst.result)
                while src in copy_map and copy_map[src] != src:
                    src = copy_map[src]
                copy_map[dst] = src
                result.append(inst)
                continue
            
            # Sustituir usos - CON VERIFICACIÓN DE NONE
            a1 = inst.arg1
            a2 = inst.arg2
            
            # Solo sustituir si a1 no es None Y está en el mapa
            if a1 is not None and str(a1) in copy_map:
                # Crear nuevo operando preservando el tipo de a1
                new_name = copy_map[str(a1)]
                a1 = TACOperand(
                    value=new_name,
                    is_temp=_is_temp_name(new_name),
                    typ=a1.typ if hasattr(a1, 'typ') else None
                )
            
            # Solo sustituir si a2 no es None Y está en el mapa
            if a2 is not None and str(a2) in copy_map:
                # Crear nuevo operando preservando el tipo de a2
                new_name = copy_map[str(a2)]
                a2 = TACOperand(
                    value=new_name,
                    is_temp=_is_temp_name(new_name),
                    typ=a2.typ if hasattr(a2, 'typ') else None
                )
            
            # Crear nueva instrucción preservando tipos
            new_inst = TACInstruction(
                inst.op, 
                self._copy_operand_with_type(inst.result), 
                self._copy_operand_with_type(a1), 
                self._copy_operand_with_type(a2)
            )
            
            # Si redefinimos el destino, invalidar
            if new_inst.result and str(new_inst.result) in copy_map:
                del copy_map[str(new_inst.result)]
            
            result.append(new_inst)
        
        return result

    def _count_temps(self, instructions: List[TACInstruction]) -> int:
        """Cuenta el número máximo de temporales usados"""
        max_temp = 0
        for inst in instructions:
            for op in [inst.result, inst.arg1, inst.arg2]:
                if op and _is_temp_name(op):
                    try:
                        num = int(str(op).replace('t', ''))
                        max_temp = max(max_temp, num)
                    except:
                        pass
        return max_temp
    def enhanced_constant_folding(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Constant folding mejorado que detecta patrones adicionales:
        - t1 = 2; t2 = 1; t3 = t1 + t2 → t3 = 3
        - t1 = const; uso inmediato de t1 → reemplazar
        """
        result = []
        const_map: Dict[str, int] = {}
        
        for inst in instructions:
            # Resetear en boundaries
            if inst.op in [TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE, 
                           TACOp.CALL, TACOp.FUNC_START, TACOp.FUNC_END]:
                const_map.clear()
                result.append(inst)
                continue

            # NUNCA sustituir en un DEREF
            if inst.op == TACOp.DEREF:
                result.append(inst)
                continue
            
            # Si es asignación de constante a temporal, registrar
            if (inst.op == TACOp.ASSIGN and 
                inst.result and _is_temp_name(inst.result) and
                inst.arg1 and _is_const(inst.arg1)):
                
                const_map[str(inst.result)] = _const_val(inst.arg1)
                result.append(inst)
                continue
            
            # Sustituir argumentos por constantes conocidas
            a1 = inst.arg1
            a2 = inst.arg2
            
            if a1 and _is_temp_name(a1) and str(a1) in const_map:
                a1 = TACOperand(const_map[str(a1)], is_constant=True)
            
            if a2 and _is_temp_name(a2) and str(a2) in const_map:
                a2 = TACOperand(const_map[str(a2)], is_constant=True)
            
            new_inst = TACInstruction(inst.op, inst.result, a1, a2)
            
            # Si ahora ambos operandos son constantes, plegar (ej: ADD)
            if new_inst.op == TACOp.ADD and _is_const(a1) and _is_const(a2):
                v1 = _const_val(a1)
                v2 = _const_val(a2)
                if isinstance(v1, int) and isinstance(v2, int):
                    new_inst = TACInstruction(
                        TACOp.ASSIGN, 
                        new_inst.result, 
                        TACOperand(v1 + v2, is_constant=True)
                    )
            
            # Invalidar si el temporal se redefine
            if new_inst.result and str(new_inst.result) in const_map:
                del const_map[str(new_inst.result)]
            
            result.append(new_inst)
        
        return result

    def remove_redundant_stores(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """
        Elimina stores redundantes:
        - 0x1000 = t1; t2 = @0x1000; 0x1000 = t2 → Eliminar último store
        """
        result: List[TACInstruction] = []
        last_store: Dict[str, tuple] = {}
        
        for inst in instructions:
            # Invalidar en boundaries
            if inst.op in [TACOp.CALL, TACOp.LABEL, TACOp.GOTO, 
                           TACOp.IF_TRUE, TACOp.IF_FALSE]:
                last_store.clear()
            
            # Store: addr = temp
            if (inst.op == TACOp.ASSIGN and 
                inst.result and str(inst.result).startswith("0x")):
                
                addr = str(inst.result)
                temp = str(inst.arg1) if inst.arg1 else None
                
                # Si ya hay un store previo al mismo addr con el mismo valor
                if addr in last_store:
                    prev_temp, prev_idx = last_store[addr]
                    
                    if prev_temp == temp:
                        # Redundante: no añadir
                        continue
                    else:
                        # Diferente valor: reemplazar el anterior
                        last_store[addr] = (temp, len(result))
                else:
                    last_store[addr] = (temp, len(result))
            
            result.append(inst)
        
        return result

    def validate_tac(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Valida y corrige TAC malformado"""
        result: List[TACInstruction] = []
        
        for inst in instructions:
            # Corregir: t1 = @t2 (DEREF de temporal) → t1 = t2
            if inst.op == TACOp.DEREF and inst.arg1 and _is_temp_name(inst.arg1):
                result.append(TACInstruction(
                    TACOp.ASSIGN,
                    inst.result,
                    inst.arg1
                ))
                continue
            
            # Corregir: FP[x] = @tn → eliminar DEREF innecesario
            if (inst.op == TACOp.ASSIGN and 
                inst.result and "FP[" in str(inst.result) and
                inst.arg1 and str(inst.arg1).startswith("@") and 
                _is_temp_name(str(inst.arg1)[1:])):
                
                temp = str(inst.arg1)[1:]
                result.append(TACInstruction(
                    TACOp.ASSIGN,
                    inst.result,
                    TACOperand(temp)
                ))
                continue
            
            result.append(inst)
        
        return result
    
    def _opt_temp_renaming(self, instructions: List[TACInstruction],
                          liveness: Dict[str, LivenessInfo]) -> List[TACInstruction]:
        """Renumeración óptima usando graph coloring"""
        if not liveness:
            return instructions
        
        # Construir grafo de interferencia
        interference = {name: set() for name in liveness.keys()}
        
        temps = list(liveness.keys())
        for i in range(len(temps)):
            for j in range(i + 1, len(temps)):
                t1, t2 = temps[i], temps[j]
                info1, info2 = liveness[t1], liveness[t2]
                
                # Interferencia si rangos se solapan
                if not (info1.last_use < info2.first_def or 
                        info2.last_use < info1.first_def):
                    interference[t1].add(t2)
                    interference[t2].add(t1)
        
        # Greedy coloring
        coloring = {}
        sorted_temps = sorted(temps, 
                             key=lambda t: (len(interference[t]), liveness[t].first_def),
                             reverse=True)
        
        for temp in sorted_temps:
            used_colors = {coloring[n] for n in interference[temp] if n in coloring}
            
            color = 1
            while color in used_colors:
                color += 1
            
            coloring[temp] = color
        
        # Aplicar renombramiento
        result = []
        for inst in instructions:
            def rename(op):
                if op and _is_temp_name(op):
                    name = str(op)
                    if name in coloring:
                        # CORRECCIÓN: Crear nuevo operando, pero COPIAR el tipo del original
                        return TACOperand(
                            value=f"t{coloring[name]}",
                            is_temp=True,
                            typ=op.typ if hasattr(op, 'typ') else None
                        )
                # Devolver una copia segura del operando original si no se renombra
                return self._copy_operand_with_type(op)
            
            result.append(TACInstruction(
                inst.op,
                rename(inst.result),
                rename(inst.arg1),
                rename(inst.arg2)
            ))
        
        return result
    
    # ============================================================
    # OPTIMIZACIONES CLÁSICAS (mantener código original)
    # ============================================================
    
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
                        # CORRECCIÓN: Asignar el tipo del resultado (ej: t1) al nuevo operando constante
                        new_const = TACOperand(v, is_constant=True, typ=inst.result.typ if hasattr(inst.result, 'typ') else None)
                        result.append(TACInstruction(TACOp.ASSIGN, inst.result, new_const))
                        continue
                result.append(inst); continue
            
            # IF con condición constante
            if inst.op in (TACOp.IF_TRUE, TACOp.IF_FALSE) and _is_const(inst.arg1):
                cond = bool(_const_val(inst.arg1))
                if (inst.op == TACOp.IF_TRUE and cond) or (inst.op == TACOp.IF_FALSE and not cond):
                    result.append(TACInstruction(TACOp.GOTO, arg1=inst.arg2))
                else:
                    pass
                continue

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
        """Propagación de constantes local a bloque lineal"""
        boundaries = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.RETURN, TACOp.CALL, TACOp.PARAM,
            TACOp.FUNC_START, TACOp.FUNC_END,
            TACOp.ARRAY_ASSIGN, TACOp.FIELD_ASSIGN
        }

        consts: Dict[str, TACOperand] = {}
        out: List[TACInstruction] = []

        def reset():
            consts.clear()

        def subst(opnd: Optional[TACOperand]) -> Optional[TACOperand]:
            if opnd is None or _is_const(opnd):
                return opnd
            key = str(opnd)
            return consts.get(key, opnd)

        for inst in instructions:
            if inst.op in boundaries:
                if inst.op in (TACOp.IF_TRUE, TACOp.IF_FALSE) and _is_const(inst.arg1):
                    cond = bool(_const_val(inst.arg1))
                    if (inst.op == TACOp.IF_TRUE and cond) or (inst.op == TACOp.IF_FALSE and not cond):
                        out.append(TACInstruction(TACOp.GOTO, arg1=inst.arg2))
                    else:
                        pass
                else:
                    out.append(inst)
                reset()
                continue

            # NUNCA sustituir en un DEREF, la dirección debe preservarse
            if inst.op == TACOp.DEREF:
                out.append(inst)
                continue

            a1 = subst(inst.arg1)
            a2 = subst(inst.arg2)
            new_inst = TACInstruction(inst.op, inst.result, a1, a2)

            if new_inst.op == TACOp.ASSIGN and _is_const(new_inst.arg1):
                if new_inst.result is not None:
                    consts[str(new_inst.result)] = new_inst.arg1
            else:
                if new_inst.result is not None and str(new_inst.result) in consts:
                    del consts[str(new_inst.result)]

            out.append(new_inst)

        return out
    
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
            
            result.append(inst)
        
        return result
    
    def copy_propagation(self, instructions):
        """Propagación de copias local a bloque lineal"""
        boundaries = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.RETURN, TACOp.CALL, TACOp.PARAM,
            TACOp.FUNC_START, TACOp.FUNC_END,
            TACOp.ARRAY_ASSIGN, TACOp.FIELD_ASSIGN
        }
        alias = {}

        def reset():
            alias.clear()

        def root(name: str) -> str:
            while name in alias and alias[name] != name:
                name = alias[name]
            return name

        def break_aliases_pointing_to(name: str):
            r = root(name)
            kill = [k for k,v in alias.items() if root(v) == r or k == r]
            for k in kill:
                del alias[k]

        out = []
        for inst in instructions:
            if inst.op in boundaries:
                out.append(inst); reset(); continue

            a1, a2 = inst.arg1, inst.arg2

            # Proteger DEREF: NUNCA sustituir el arg1 de un DEREF
            if inst.op != TACOp.DEREF:
                if a1 is not None and not _is_const(a1):
                    new_name = root(str(a1))
                    # CORRECCIÓN: Crear nuevo operando, pero COPIAR el tipo del original
                    a1 = TACOperand(
                        value=new_name,
                        is_temp=_is_temp_name(new_name),
                        typ=a1.typ if hasattr(a1, 'typ') else None
                    )

            # arg2 siempre es seguro de sustituir
            if a2 is not None and not _is_const(a2):
                new_name = root(str(a2))
                # CORRECCIÓN: Crear nuevo operando, pero COPIAR el tipo del original
                a2 = TACOperand(
                    value=new_name,
                    is_temp=_is_temp_name(new_name),
                    typ=a2.typ if hasattr(a2, 'typ') else None
                )

            new_inst = TACInstruction(inst.op, self._copy_operand_with_type(inst.result), a1, a2)

            if new_inst.result is not None:
                break_aliases_pointing_to(str(new_inst.result))

            if new_inst.op == TACOp.ASSIGN and new_inst.arg1 is not None and not _is_const(new_inst.arg1):
                alias[str(new_inst.result)] = root(str(new_inst.arg1))
            out.append(new_inst)
        return out
    
    def dead_code_elimination(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Elimina código muerto (conservador, intra-bloque)"""
        used_vars: Set[str] = set()

        # 1) Marcar usos directos
        for inst in instructions:
            op = inst.op
            if op in (TACOp.PRINT, TACOp.RETURN, TACOp.IF_TRUE, TACOp.IF_FALSE, TACOp.PARAM):
                if inst.arg1 is not None:
                    used_vars.add(str(inst.arg1))
            if inst.arg1 is not None and op != TACOp.ASSIGN:
                used_vars.add(str(inst.arg1))
            if inst.arg2 is not None:
                used_vars.add(str(inst.arg2))
            if op in (TACOp.ARRAY_ASSIGN, TACOp.FIELD_ASSIGN):
                if inst.result is not None:
                    used_vars.add(str(inst.result))

        # 2) Propagar hacia atrás
        changed = True
        while changed:
            changed = False
            for inst in reversed(instructions):
                if inst.result is not None and str(inst.result) in used_vars:
                    if inst.arg1 is not None and str(inst.arg1) not in used_vars:
                        used_vars.add(str(inst.arg1)); changed = True
                    if inst.arg2 is not None and str(inst.arg2) not in used_vars:
                        used_vars.add(str(inst.arg2)); changed = True

        # 3) Conservar side-effects/flujo siempre
        keep_ops = {
            TACOp.LABEL, TACOp.GOTO, TACOp.IF_TRUE, TACOp.IF_FALSE,
            TACOp.PRINT, TACOp.RETURN, TACOp.PARAM, TACOp.CALL,
            TACOp.FUNC_START, TACOp.FUNC_END, TACOp.ARRAY_ASSIGN, TACOp.FIELD_ASSIGN,
            TACOp.PUSH, TACOp.POP, TACOp.ENTER, TACOp.LEAVE, TACOp.ADD_SP
        }

        result: List[TACInstruction] = []
        for inst in instructions:
            if inst.op in keep_ops:
                result.append(inst)
            elif inst.result is not None and str(inst.result) in used_vars:
                result.append(inst)
        return result
    
    def remove_redundant_moves(self, instructions):
        out = []
        for inst in instructions:
            if inst.op == TACOp.ASSIGN and inst.result is not None and inst.arg1 is not None:
                if str(inst.result) == str(inst.arg1):
                    continue
            out.append(inst)
        return out
    
    def remove_redundant_jumps(self, instructions: List[TACInstruction]) -> List[TACInstruction]:
        """Elimina saltos redundantes"""
        result: List[TACInstruction] = []
        
        for i, inst in enumerate(instructions):
            # Eliminar GOTO a la etiqueta inmediata siguiente
            if inst.op == TACOp.GOTO:
                if i + 1 < len(instructions) and instructions[i + 1].op == TACOp.LABEL:
                    if str(inst.arg1) == str(instructions[i + 1].arg1):
                        continue
            
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
                    continue
            
            result.append(inst)
        
        return result
    
    # -------- helpers de valor ----------
    def _is_constant(self, operand: Optional[TACOperand]) -> bool:
        return _is_const(operand)
    
    def _is_zero(self, operand: Optional[TACOperand]) -> bool:
        return _is_const(operand) and _const_val(operand) == 0
    
    def _is_one(self, operand: Optional[TACOperand]) -> bool:
        return _is_const(operand) and _const_val(operand) == 1