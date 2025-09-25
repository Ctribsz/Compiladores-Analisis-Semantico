"""
Runner para la generación de código intermedio
Integra TAC con el pipeline de compilación existente
"""
from typing import Optional
from dataclasses import dataclass

from semantic.semantic_visitor import SymbolCollector, TypeCheckerVisitor
from semantic.errors import ErrorCollector
from .tac_generator import TACGenerator
from .tac import TACProgram

@dataclass
class IntermediateResult:
    """Resultado de la generación de código intermedio"""
    tac_program: Optional[TACProgram]
    errors: list
    has_errors: bool
    
    def get_tac_code(self) -> str:
        """Obtiene el código TAC como string"""
        if self.tac_program:
            return str(self.tac_program)
        return ""
    
    def get_tac_lines(self) -> list:
        """Obtiene el código TAC como lista de líneas"""
        if self.tac_program:
            return self.tac_program.to_list()
        return []

def generate_intermediate_code(tree) -> IntermediateResult:
    """
    Genera código intermedio a partir del AST
    Primero ejecuta el análisis semántico, luego genera TAC si no hay errores
    """
    # Fase 1: Análisis semántico (recolección de símbolos)
    errors = ErrorCollector()
    symbol_collector = SymbolCollector(errors)
    symbol_collector.visit(tree)
    
    # Fase 2: Chequeo de tipos
    type_checker = TypeCheckerVisitor(
        errors, 
        symbol_collector.global_scope, 
        symbol_collector.scopes_by_ctx
    )
    type_checker.visit(tree)
    
    # Si hay errores semánticos, no generar código intermedio
    if errors.has_errors():
        return IntermediateResult(
            tac_program=None,
            errors=errors.errors,
            has_errors=True
        )
    
    # Fase 3: Generación de código intermedio
    try:
        tac_gen = TACGenerator(
            symbol_collector.global_scope,
            symbol_collector.scopes_by_ctx
        )
        tac_program = tac_gen.visit(tree)
        
        return IntermediateResult(
            tac_program=tac_program,
            errors=[],
            has_errors=False
        )
    except Exception as e:
        # Error en la generación de TAC
        errors.report(0, 0, "TAC_ERROR", f"Error generando código intermedio: {str(e)}")
        return IntermediateResult(
            tac_program=None,
            errors=errors.errors,
            has_errors=True
        )