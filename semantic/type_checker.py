from .types import Type, INTEGER, BOOLEAN, STRING, NULL, ArrayType

def is_assignable(src: Type, dst: Type) -> bool:
    # Regla base: mismo tipo
    if src.name == dst.name: return True
    # null asignable (decisión inicial): a arreglos y clases, NO a primitivos
    if src.name == "null" and (isinstance(dst, ArrayType) or dst.name not in ("integer","boolean","string")):
        return True
    return False

def expects_integer(t: Type) -> bool:
    return t.name == "integer"

def expects_boolean(t: Type) -> bool:
    return t.name == "boolean"
