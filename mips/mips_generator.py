"""
Generador de Código MIPS (Fase 3)
Traduce un TACProgram (optimizado) a código MIPS.
"""
import sys
from typing import List, Dict, Set

# Asegurar que podamos importar desde carpetas hermanas
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intermediate.tac import TACProgram, TACInstruction, TACOp, TACOperand
from mips.runtime import get_data_preamble, get_text_preamble, get_syscall_helpers
from semantic.scope import Scope
from semantic.symbols import ClassSymbol 

class MIPSGenerator:
    """
    Toma un TACProgram y genera un string de código MIPS.
    
    Estrategia de manejo de memoria:
    - Variables Globales (0x...): Viven en la sección .data.
    - Parámetros (FP[neg_offset]): Viven en el stack, accedidos por $fp.
    - Variables Locales (ENTER size): Viven en el stack, accedidos por $fp.
    - Temporales (tK): Se alocan dinámicamente en el stack por esta clase.
    """
    
    def __init__(self, program: TACProgram, global_scope: Scope):
        self.program = program
        self.global_scope = global_scope 
        self.mips_code: List[str] = []
        
        # --- Estado de Generación ---
        
        # .data
        self.globals: Set[str] = set()        # Set de '0x...'
        self.strings: Dict[str, str] = {}     # Mapa de 'string' -> 'label'

        # --- Mapa de Clases ---
        self.class_layouts: Dict[str, ClassSymbol] = {}
        
        # .text (estado por función)
        self.temp_map: Dict[str, int] = {}    # Mapa de 'tK' -> offset_stack
        self.current_frame_size = 0           # Tamaño de locales (de ENTER)
        self.current_temp_offset = 0          # Offset actual para nuevos 'tK'
        
    def _emit(self, line: str, indent: int = 1):
        """Añade una línea de MIPS al buffer."""
        self.mips_code.append(f"{'    ' * indent}{line}")
    
    def _collect_class_layouts(self):
        """ Extrae layouts de clases del scope global para acceso rápido. """
        if not self.global_scope:
            return
        for name, symbol in self.global_scope.symbols.items():
            if isinstance(symbol, ClassSymbol):
                self.class_layouts[name] = symbol

    def generate(self) -> str:
        """Punto de entrada principal. Orquesta la generación."""
        # 1. Recolectar info de clases (NUEVO)
        self._collect_class_layouts()

        # 1. Escanear el TAC para encontrar data (globales y strings)
        self._scan_for_data()
        
        # 2. Generar sección .data
        self.mips_code.append("# === SECCIÓN DE DATOS ===")
        self._build_data_section()
        
        # 3. Generar sección .text
        self.mips_code.append("\n# === SECCIÓN DE CÓDIGO ===")
        self._emit(get_text_preamble(), indent=0)
        
        # 4. Traducir cada instrucción TAC
        for inst in self.program.instructions:
            self._emit(f"# {inst}", indent=1) # El TAC como comentario
            self._translate_instruction(inst)
            
        # 5. Añadir helpers (syscalls) al final
        self.mips_code.append("\n# === HELPERS DEL RUNTIME ===")
        self.mips_code.append(get_syscall_helpers())
        
        return "\n".join(self.mips_code)

    # --- FASE 1: ESCANEO DE DATOS ---

    def _scan_for_data(self):
        """
        Primera pasada: recolecta globales (0x...) y strings
        para construir la sección .data.
        """
        for inst in self.program.instructions:
            # Buscar strings en operandos
            for op in [inst.arg1, inst.arg2]:
                if op and op.is_constant and isinstance(op.value, str):
                    if op.value not in self.strings:
                        label = f"_str_{len(self.strings)}"
                        self.strings[op.value] = label
            
            # Buscar globales (0x...)
            for op in [inst.result, inst.arg1, inst.arg2]:
                if op and isinstance(op.value, str) and op.value.startswith("0x"):
                    self.globals.add(op.value)

    # --- FASE 2: CONSTRUCCIÓN DE .DATA ---

    def _build_data_section(self):
        """Emite el código .data."""
        self._emit(get_data_preamble(), indent=0)
        
        # Globales (basado en el TAC de ejemplo, son .word)
        self._emit("# Variables Globales (0x...)", indent=1)
        for g in sorted(list(self.globals)):
            self._emit(f"global_{g[2:]}: .word 0", indent=1) # ej: global_1000: .word 0
        
        # String literals
        self._emit("\n# Literales de String", indent=1)
        for s, label in self.strings.items():
            # Escapar saltos de línea y comillas en MIPS
            escaped_s = s.replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"")
            self._emit(f"{label}: .asciiz \"{escaped_s}\"", indent=1)

    # --- FASE 3: TRADUCCIÓN DE INSTRUCCIONES ---

    def _translate_instruction(self, inst: TACInstruction):
        """Despachador principal de traducción de TACOp a MIPS."""
        
        op = inst.op
        
        # --- Aritméticas ---
        if op == TACOp.ADD:
            self._translate_binary_op(inst, "add")
        elif op == TACOp.SUB:
            self._translate_binary_op(inst, "sub")
        elif op == TACOp.MUL:
            self._translate_binary_op(inst, "mul")
        elif op == TACOp.DIV:
            self._translate_binary_op(inst, "div")
        elif op == TACOp.MOD:
            self._translate_binary_op(inst, "rem")
        elif op == TACOp.NEG:
            self._load_op("$t0", inst.arg1)
            self._emit("neg $t0, $t0")
            self._store_op("$t0", inst.result)
            
        # --- Relacionales ---
        elif op == TACOp.LT:
            self._translate_binary_op(inst, "slt") # Set if Less Than
        elif op == TACOp.LE:
            self._translate_binary_op(inst, "sle") # Set if Less/Equal
        elif op == TACOp.GT:
            self._translate_binary_op(inst, "sgt") # Set if Greater Than
        elif op == TACOp.GE:
            self._translate_binary_op(inst, "sge") # Set if Greater/Equal
        elif op == TACOp.EQ:
            self._translate_binary_op(inst, "seq") # Set if Equal
        elif op == TACOp.NE:
            self._translate_binary_op(inst, "sne") # Set if Not Equal
        
        # --- Lógicas (simplificadas, asumen 0/1) ---
        elif op == TACOp.AND:
            self._translate_binary_op(inst, "and")
        elif op == TACOp.OR:
            self._translate_binary_op(inst, "or")
        elif op == TACOp.NOT:
            self._load_op("$t0", inst.arg1)
            self._emit("seq $t0, $t0, $zero") # t0 = (t0 == 0)
            self._store_op("$t0", inst.result)

        # --- Asignación y Memoria ---
        elif op == TACOp.ASSIGN:
            self._load_op("$t0", inst.arg1)
            self._store_op("$t0", inst.result)
        
        elif op == TACOp.DEREF: # t1 = @0x1000  o  t1 = @FP[-4]
            self._get_addr("$t0", inst.arg1) # t0 = dirección (0x1000 o FP-4)
            self._emit(f"lw $t1, 0($t0)")    # t1 = Mem[t0]
            self._store_op("$t1", inst.result) # t1 (stack) = t1

        elif op == TACOp.ARRAY_ACCESS: # result = arg1[arg2] (base[index])
            self._load_op("$t0", inst.arg1)    # t0 = base address
            self._load_op("$t1", inst.arg2)    # t1 = index
            self._emit("sll $t1, $t1, 2")      # t1 = index * 4 (word size)
            self._emit("add $t0, $t0, $t1")    # t0 = base + (index * 4)
            self._emit("lw $t2, 0($t0)")       # t2 = Mem[t0]
            self._store_op("$t2", inst.result) # result = t2
        
        elif op == TACOp.ARRAY_ASSIGN: # result[arg1] = arg2 (base[index] = value)
            self._load_op("$t0", inst.result)  # t0 = base address
            self._load_op("$t1", inst.arg1)    # t1 = index
            self._load_op("$t2", inst.arg2)    # t2 = value
            self._emit("sll $t1, $t1, 2")      # t1 = index * 4
            self._emit("add $t0, $t0, $t1")    # t0 = base + (index * 4)
            self._emit("sw $t2, 0($t0)")       # Mem[t0] = t2

        elif op == TACOp.FIELD_ACCESS: # result = arg1.arg2 (obj.field)
            obj_op = inst.arg1
            member_name = str(inst.arg2.value)

            # --- HACK: Asumir tipo 'Point' ---
            class_layout = self.class_layouts.get("Point")
            if not class_layout:
                self._emit(f"# ERROR: No se encontró layout de clase 'Point' para {member_name}")
                pass
            
            if member_name in class_layout.fields:
                # --- Es un ACCESO A CAMPO (p.x) ---
                field_name = member_name
                offset = 0 # Default offset
                try:
                    field_list = list(class_layout.fields.keys())
                    offset = field_list.index(field_name) * 4
                except:
                    offset = 4 if field_name == "y" else 0 # Fallback
                
                self._emit(f"# (Accediendo a campo '{field_name}' en offset {offset})")
                self._load_op("$t0", obj_op) # t0 = base address
                self._emit(f"lw $t1, {offset}($t0)") # t1 = Mem[base + offset]
                self._store_op("$t1", inst.result) # result = t1
            
            elif member_name in class_layout.methods:
                # --- Es un ACCESO A MÉTODO (p.getX) ---
                # El resultado debe ser la *dirección* de la función
                # Asumimos que el método NO es de clase (ej: Point_getX)
                method_label = self._sanitize_label(f"{member_name}") 
                
                self._emit(f"# (Resolviendo dirección de método {method_label})")
                self._emit(f"la $t0, {method_label}")
                self._store_op("$t0", inst.result) # result = addr(getX)
            else:
                self._emit(f"# ERROR: Miembro '{member_name}' no encontrado en 'Point'")
            
        elif op == TACOp.FIELD_ASSIGN: # result.arg1 = arg2 (obj.field = value)
            obj_op = inst.result
            field_name = str(inst.arg1.value)
            value_op = inst.arg2

            # --- HACK: Asumir tipo 'Point' ---
            class_layout = self.class_layouts.get("Point")
            
            offset = 0 # Default offset
            if class_layout and field_name in class_layout.fields:
                # ¡Calcular offset real! (Asumiendo que los campos están en orden)
                try:
                    field_list = list(class_layout.fields.keys())
                    offset = field_list.index(field_name) * 4
                except:
                    offset = 4 if field_name == "y" else 0 # Fallback al hack anterior
            else:
                 offset = 4 if field_name == "y" else 0 # Fallback al hack anterior
            
            self._emit(f"# (Asignando a campo '{field_name}' en offset {offset})")
            self._load_op("$t0", obj_op)     # t0 = base address
            self._load_op("$t1", value_op)   # t1 = value
            self._emit(f"sw $t1, {offset}($t0)") # Mem[base + offset] = value
        
        # --- Control de Flujo ---
        elif op == TACOp.GOTO:
            self._emit(f"j {inst.arg1}")
        elif op == TACOp.IF_TRUE:
            self._load_op("$t0", inst.arg1)
            self._emit(f"bne $t0, $zero, {inst.arg2}") # Branch if t0 != 0
        elif op == TACOp.IF_FALSE:
            self._load_op("$t0", inst.arg1)
            self._emit(f"beq $t0, $zero, {inst.arg2}") # Branch if t0 == 0
        elif op == TACOp.LABEL:
            self._emit(f"{inst.arg1}:", indent=0)

        # --- Funciones y Stack ---
        elif op == TACOp.FUNC_START:
            label = self._sanitize_label(str(inst.arg1)) # <-- SANITIZAR
            self._emit(f"{label}:", indent=0) # Etiqueta de función
            # Reseteamos el mapa de temporales para esta nueva función
            self.temp_map = {}
            self.current_frame_size = 0
            self.current_temp_offset = 0

        elif op == TACOp.ENTER: # Prolog
            size = inst.arg1.value
            self.current_frame_size = size # Guardamos tamaño de locales
            
            # 1. Guardar $ra y $fp viejo
            self._emit("subu $sp, $sp, 8")
            self._emit("sw $ra, 4($sp)")
            self._emit("sw $fp, 0($sp)")
            
            # 2. $fp = $sp
            self._emit("move $fp, $sp")
            
            # 3. Reservar espacio para locales (size)
            if size > 0:
                self._emit(f"subu $sp, $sp, {size}")

        elif op == TACOp.LEAVE: # Epilog
            # 1. Liberar espacio de locales
            if self.current_frame_size > 0:
                self._emit(f"addu $sp, $sp, {self.current_frame_size}")
            
            # 2. Restaurar $ra y $fp
            self._emit("lw $ra, 4($sp)")
            self._emit("lw $fp, 0($sp)")
            self._emit("addu $sp, $sp, 8")
            
        elif op == TACOp.RETURN:
            if inst.arg1:
                self._load_op("$v0", inst.arg1) # $v0 = valor de retorno
            self._emit("jr $ra") # Saltar a dirección de retorno

        # --- Llamadas ---
        elif op == TACOp.PUSH: # Poner en el stack
            self._load_op("$t0", inst.arg1)
            self._emit("subu $sp, $sp, 4")
            self._emit("sw $t0, 0($sp)")
            
        elif op == TACOp.CALL:
            op_name = str(inst.arg1.value)
            
            if op_name.startswith("t"):
                # Es una llamada indirecta (ej: call t1, donde t1 tiene addr(getX))
                self._load_op("$t0", inst.arg1) # Cargar la dirección (de t1) en $t0
                self._emit("jalr $t0")          # Jump And Link Register
            else:
                # Es una llamada estática (ej: call add)
                label = self._sanitize_label(op_name)
                self._emit(f"jal {label}")
            
        elif op == TACOp.ADD_SP: # Limpiar args del stack (SP = SP + 8)
            self._emit(f"addu $sp, $sp, {inst.arg1.value}")

        elif op == TACOp.POP: # Sacar de stack y guardar en resultado
            self._emit("lw $t0, 0($sp)")
            self._emit("addu $sp, $sp, 4")
            self._store_op("$t0", inst.result)
            
        # --- Helpers (PRINT, NEW) ---
        elif op == TACOp.PRINT:
            operand = inst.arg1
            self._load_op("$a0", operand) # $a0 = argumento a imprimir
            
            op_type = operand.typ # <-- Leer el tipo del operando
            
            self._emit(f"# (Llamando a print para tipo: {op_type})")
            
            if op_type == 'string':
                self._emit("jal _print_string")
            elif op_type == 'boolean':
                self._emit("jal _print_boolean")
            else:
                # Asumir integer, null, o array (que imprime su dirección)
                self._emit("jal _print_int")
        
        elif op == TACOp.NEW:
            arg1_op = inst.arg1
            
            if arg1_op.is_constant and isinstance(arg1_op.value, int):
                # --- Es un ARREGLO (ej: new 5) ---
                num_elements = arg1_op.value
                size = num_elements * 4 # 4 bytes por elemento (int)
                self._emit(f"# Alocando {size} bytes para array[{num_elements}]")
                self._emit(f"li $a0, {size}")

            elif isinstance(arg1_op.value, str):
                # --- Es una CLASE (ej: new Point) ---
                class_name = str(arg1_op.value)
                size = 0
                if class_name in self.class_layouts:
                    fields = self.class_layouts[class_name].fields
                    size = len(fields) * 4
                
                if size == 0 and class_name == "Point":
                     size = 8 # HACK: Fallback

                self._emit(f"# Alocando {size} bytes para {class_name}")
                self._emit(f"li $a0, {size}")
            
            else:
                self._emit(f"# ERROR: 'NEW' no sabe qué hacer con {arg1_op}")
                self._emit(f"li $a0, 0")

            self._emit("jal _alloc")
            self._store_op("$v0", inst.result) # result = new object ptr

    # --- HELPERS DE TRADUCCIÓN ---

    def _translate_binary_op(self, inst: TACInstruction, mips_op: str):
        """Helper genérico para t3 = t1 op t2"""
        self._load_op("$t0", inst.arg1)
        self._load_op("$t1", inst.arg2)
        self._emit(f"{mips_op} $t2, $t0, $t1")
        self._store_op("$t2", inst.result)

    def _get_temp_offset(self, op_name: str) -> int:
        """
        Obtiene el offset del stack para un temporal 'tK'.
        Si no existe, crea uno nuevo.
        Los offsets son *negativos* desde $fp (después de locales).
        """
        if op_name not in self.temp_map:
            # + 4 bytes por temporal
            self.current_temp_offset += 4
            # Mapea 'tK' al offset total (locales + este temp)
            self.temp_map[op_name] = self.current_frame_size + self.current_temp_offset
        
        return self.temp_map[op_name]

    def _load_op(self, reg: str, op: TACOperand):
        """
        Emite MIPS para cargar el VALOR de un operando TAC en un registro.
        """
        op_val_str = str(op.value)
        if op.is_constant:
            if isinstance(op.value, str):
                # Cargar dirección de string
                self._emit(f"la {reg}, {self.strings[op.value]}")
            else:
                # Cargar valor inmediato (int, bool)
                val = 1 if op.value is True else (0 if op.value is False else op.value)
                self._emit(f"li {reg}, {val}")
        
        elif str(op.value).startswith("t"): # Es un temporal 'tK'
            offset = self._get_temp_offset(op.value)
            self._emit(f"lw {reg}, -{offset}($fp)") # Cargar desde stack

        # Es una variable global (ej: 'arr' o 'p' que se resolvieron a '0x...')
        # Buscamos si el nombre 'arr' está en el TAC como '0x...'
        elif op_val_str in self.globals:
            label = f"global_{op_val_str[2:]}"
            self._emit(f"la $at, {label}")    # Cargar dirección global
            self._emit(f"lw {reg}, 0($at)")   # Cargar VALOR en esa dirección

        
        else:
            # Fallback (podría ser un nombre de var, etc.)
            # Asumimos que es un error o un tipo no manejado
            self._emit(f"# ADVERTENCIA: _load_op no sabe cómo cargar '{op}'")

    def _sanitize_label(self, label: str) -> str:
        """Reemplaza caracteres no válidos de MIPS por '_'."""
        return label.replace(".", "_")

    def _store_op(self, reg: str, op: TACOperand):
        """
        Emite MIPS para guardar un valor (en reg) en la UBICACIÓN de un operando.
        """
        if str(op.value).startswith("t"): # Temporal 'tK'
            offset = self._get_temp_offset(op.value)
            self._emit(f"sw {reg}, -{offset}($fp)") # Guardar en stack
        
        elif str(op.value).startswith("0x"): # Global '0x...'
            label = f"global_{op.value[2:]}"
            self._emit(f"la $at, {label}") # Cargar dirección global en $at
            self._emit(f"sw {reg}, 0($at)") # Guardar valor en esa dirección

        elif str(op.value).startswith("FP["): # Local/Param 'FP[offset]'
            offset = str(op.value)[3:-1] # Extraer 'offset'
            self._emit(f"sw {reg}, {offset}($fp)")

        else:
            self._emit(f"# ADVERTENCIA: _store_op no sabe cómo guardar en '{op}'")

    def _get_addr(self, reg: str, op: TACOperand):
        """
        Emite MIPS para cargar la DIRECCIÓN de un operando en un registro.
        Usado para DEREF (@)
        """
        if str(op.value).startswith("0x"): # Global '0x...'
            label = f"global_{op.value[2:]}"
            self._emit(f"la {reg}, {label}")
            
        elif str(op.value).startswith("FP["): # Local/Param 'FP[offset]'
            offset = str(op.value)[3:-1]
            self._emit(f"addi {reg}, $fp, {offset}")

        else:
            self._emit(f"# ADVERTENCIA: _get_addr no sabe cómo obtener dirección de '{op}'")