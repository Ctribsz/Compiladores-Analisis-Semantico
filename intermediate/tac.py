"""
Three-Address Code (TAC) - Definiciones e instrucciones
"""
from dataclasses import dataclass
from typing import Optional, Union, List
from enum import Enum

class TACOp(Enum):
    # Aritméticas
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    NEG = "NEG"
    
    # Lógicas
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Relacionales
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"
    
    # Control de flujo
    GOTO = "GOTO"
    IF_TRUE = "IF_TRUE"
    IF_FALSE = "IF_FALSE"
    
    # Llamadas a función
    CALL = "CALL"
    PARAM = "PARAM"
    RETURN = "RETURN"
    
    # Memoria
    ASSIGN = "ASSIGN"
    ARRAY_ACCESS = "ARRAY_ACCESS"
    ARRAY_ASSIGN = "ARRAY_ASSIGN"
    FIELD_ACCESS = "FIELD_ACCESS"
    FIELD_ASSIGN = "FIELD_ASSIGN"
    
    # Objetos
    NEW = "NEW"
    
    # Etiquetas y funciones
    LABEL = "LABEL"
    FUNC_START = "FUNC_START"
    FUNC_END = "FUNC_END"
    
    # I/O
    PRINT = "PRINT"

@dataclass
class TACOperand:
    """Operando en TAC: puede ser temporal, variable, constante o etiqueta"""
    value: Union[str, int, bool, None]
    is_temp: bool = False
    is_constant: bool = False
    is_label: bool = False
    typ: Optional[str] = None  # tipo del operando
    
    def __str__(self):
        if self.is_temp:
            return f"t{self.value}"
        elif self.is_constant:
            if isinstance(self.value, str):
                return f'"{self.value}"'
            elif isinstance(self.value, bool):
                return "true" if self.value else "false"
            else:
                return str(self.value)
        elif self.is_label:
            return f"L{self.value}"
        else:
            return str(self.value)

@dataclass
class TACInstruction:
    """Instrucción de Three-Address Code"""
    op: TACOp
    result: Optional[TACOperand] = None
    arg1: Optional[TACOperand] = None
    arg2: Optional[TACOperand] = None
    
    def __str__(self):
        if self.op == TACOp.ASSIGN:
            return f"{self.result} = {self.arg1}"
        elif self.op in [TACOp.ADD, TACOp.SUB, TACOp.MUL, TACOp.DIV, TACOp.MOD]:
            return f"{self.result} = {self.arg1} {self.op.value.lower()} {self.arg2}"
        elif self.op == TACOp.NEG:
            return f"{self.result} = -{self.arg1}"
        elif self.op in [TACOp.AND, TACOp.OR]:
            return f"{self.result} = {self.arg1} {self.op.value.lower()} {self.arg2}"
        elif self.op == TACOp.NOT:
            return f"{self.result} = !{self.arg1}"
        elif self.op in [TACOp.LT, TACOp.LE, TACOp.GT, TACOp.GE, TACOp.EQ, TACOp.NE]:
            op_map = {
                TACOp.LT: "<", TACOp.LE: "<=", TACOp.GT: ">",
                TACOp.GE: ">=", TACOp.EQ: "==", TACOp.NE: "!="
            }
            return f"{self.result} = {self.arg1} {op_map[self.op]} {self.arg2}"
        elif self.op == TACOp.GOTO:
            return f"goto {self.arg1}"
        elif self.op == TACOp.IF_TRUE:
            return f"if {self.arg1} goto {self.arg2}"
        elif self.op == TACOp.IF_FALSE:
            return f"ifFalse {self.arg1} goto {self.arg2}"
        elif self.op == TACOp.LABEL:
            return f"{self.arg1}:"
        elif self.op == TACOp.FUNC_START:
            return f"function {self.arg1}:"
        elif self.op == TACOp.FUNC_END:
            return f"end_function {self.arg1}"
        elif self.op == TACOp.PARAM:
            return f"param {self.arg1}"
        elif self.op == TACOp.CALL:
            if self.result:
                return f"{self.result} = call {self.arg1}, {self.arg2}"
            else:
                return f"call {self.arg1}, {self.arg2}"
        elif self.op == TACOp.RETURN:
            if self.arg1:
                return f"return {self.arg1}"
            else:
                return "return"
        elif self.op == TACOp.ARRAY_ACCESS:
            return f"{self.result} = {self.arg1}[{self.arg2}]"
        elif self.op == TACOp.ARRAY_ASSIGN:
            return f"{self.result}[{self.arg1}] = {self.arg2}"
        elif self.op == TACOp.FIELD_ACCESS:
            return f"{self.result} = {self.arg1}.{self.arg2}"
        elif self.op == TACOp.FIELD_ASSIGN:
            return f"{self.result}.{self.arg1} = {self.arg2}"
        elif self.op == TACOp.NEW:
            return f"{self.result} = new {self.arg1}"
        elif self.op == TACOp.PRINT:
            return f"print {self.arg1}"
        else:
            return f"{self.op.value} {self.result} {self.arg1} {self.arg2}"


# --- TempPool simple -------------------------------------------
class TempPool:
    def __init__(self):
        self._free = []      # temporales disponibles p/ reuso (stack)
        self._count = 0      # cuántos he creado en total

    def acquire(self) -> str:
        # Reusar si hay libres
        if self._free:
            return self._free.pop()
        # Si no, crear uno nuevo
        self._count += 1
        return f"t{self._count}"

    def release(self, name: str):
        # Solo liberamos nombres que realmente sean temporales de la forma tK
        if name and isinstance(name, str) and name.startswith("t"):
            self._free.append(name)

    @property
    def created(self) -> int:
        return self._count
# ---------------------------------------------------------------

class TACProgram:
    """Programa completo en TAC"""
    def __init__(self):
        self.instructions: List[TACInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0
        self._temp_pool = TempPool()
        
     # Reemplaza tu new_temp() anterior por:
    def new_temp(self) -> str:
        t = self._temp_pool.acquire()
        # mantén temp_counter como “máximo creado” para reportes
        self.temp_counter = max(self.temp_counter, int(t[1:]))
        return t

    # Nuevo método:
    def free_temp(self, name: str):
        self._temp_pool.release(name)
    
    def new_label(self) -> TACOperand:
        """Genera una nueva etiqueta"""
        label = TACOperand(self.label_counter, is_label=True)
        self.label_counter += 1
        return label
    
    def add_instruction(self, instruction: TACInstruction):
        """Añade una instrucción al programa"""
        self.instructions.append(instruction)
    
    def emit(self, op: TACOp, result=None, arg1=None, arg2=None):
        """Emite una nueva instrucción"""
        self.add_instruction(TACInstruction(op, result, arg1, arg2))
    
    def emit_label(self, label: TACOperand):
        """Emite una etiqueta"""
        self.emit(TACOp.LABEL, arg1=label)
    
    def __str__(self):
        """Representación en string del programa TAC"""
        return "\n".join(str(inst) for inst in self.instructions)
    
    def to_list(self) -> List[str]:
        """Convierte el programa a lista de strings"""
        return [str(inst) for inst in self.instructions]