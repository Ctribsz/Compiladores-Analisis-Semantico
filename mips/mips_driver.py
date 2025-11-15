"""
Driver CLI para generar código MIPS (Fase 3)
Uso: python -m mips.driver archivo.cps [opciones]
"""
import sys
import os
import argparse
from pathlib import Path

# Configurar path para imports
# Esto asume que 'mips/' está en la raíz del proyecto
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from program.gen.CompiscriptLexer import CompiscriptLexer
from program.gen.CompiscriptParser import CompiscriptParser
from intermediate.runner import generate_intermediate_code
# --- NUEVOS IMPORTS ---
from intermediate.optimizer import TACOptimizer
# (Estos archivos los crearemos a continuación)
from .mips_generator import MIPSGenerator
from .runtime import get_data_preamble, get_text_preamble, get_syscall_helpers
# --- FIN NUEVOS IMPORTS ---

class SyntaxErrorCollector(ErrorListener):
    """Colector de errores sintácticos (igual que en tac_driver.py)"""
    def __init__(self):
        super().__init__()
        self.errors = []
    
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append({
            'line': line,
            'column': column,
            'message': msg
        })

def main():
    """Función principal del driver MIPS"""
    # --- ARGPARSE MODIFICADO ---
    parser = argparse.ArgumentParser(
        description='Generador de código MIPS para Compiscript (Fase 3)'
    )
    parser.add_argument(
        'input_file',
        help='Archivo fuente Compiscript (.cps)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Archivo de salida para el código MIPS (.s). '
             'Si no se especifica, se usa el nombre de entrada con extensión .s',
        default=None
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostrar información detallada del proceso'
    )
    parser.add_argument(
        '--no-optimize',
        action='store_true',
        help='Desactivar el pase de optimización de TAC'
    )
    parser.add_argument(
        '--optimized-tac-out',
        help='(Debug) Guardar el TAC optimizado en un archivo separado',
        default=None
    )
    # --- FIN ARGPARSE MODIFICADO ---
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: El archivo '{input_path}' no existe", file=sys.stderr)
        sys.exit(1)
    
    if args.verbose:
        print(f"Iniciando compilación MIPS para: {input_path}")
        print(f"=" * 50)
    
    try:
        # --- FASE 1: ANÁLISIS SINTÁCTICO (Igual) ---
        input_stream = FileStream(str(input_path), encoding='utf-8')
        lexer = CompiscriptLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(token_stream)
        
        syntax_collector = SyntaxErrorCollector()
        parser.removeErrorListeners()
        parser.addErrorListener(syntax_collector)
        
        tree = parser.program()
        
        if syntax_collector.errors:
            print("Errores sintácticos encontrados:", file=sys.stderr)
            for error in syntax_collector.errors:
                print(f"  [{error['line']}:{error['column']}] {error['message']}", 
                      file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print("✓ Fase 1: Análisis sintáctico completado")
        
        # --- FASE 2: ANÁLISIS SEMÁNTICO Y GEN. TAC (Igual) ---
        result = generate_intermediate_code(tree)
        
        if result.has_errors:
            print("Errores semánticos (Fase 1/2) encontrados:", file=sys.stderr)
            for error in result.errors:
                print(f"  [{error.code}] ({error.line}:{error.col}) {error.msg}", 
                      file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print(f"✓ Fase 2: Semántica y Gen. TAC completada ({len(result.tac_program.instructions)} inst.)")

        # --- FASE 2.5: OPTIMIZACIÓN DE TAC (NUEVO) ---
        tac_program = result.tac_program
        if not args.no_optimize:
            if args.verbose:
                print("Iniciando Fase 2.5: Optimización de TAC...")
            optimizer = TACOptimizer(tac_program)
            optimized_tac = optimizer.optimize()
            tac_program = optimized_tac
            
            if args.verbose:
                print(f"✓ Fase 2.5: Optimización completada ({len(tac_program.instructions)} inst. restantes)")
        else:
            if args.verbose:
                print("Saltando Fase 2.5: Optimización de TAC")
        
        # (Debug) Guardar TAC optimizado si se pidió
        if args.optimized_tac_out:
            opt_out_path = Path(args.optimized_tac_out)
            opt_out_path.write_text(tac_program.to_string(), encoding='utf-8')
            if args.verbose:
                print(f"  (Debug) TAC optimizado guardado en: {opt_out_path}")

        # --- FASE 3: GENERACIÓN DE CÓDIGO MIPS (NUEVO) ---
        if args.verbose:
            print("Iniciando Fase 3: Generación de código MIPS...")
        
       
        mips_gen = MIPSGenerator(tac_program, result.global_scope, result.scopes_by_ctx) 
        mips_code = mips_gen.generate()
        
        if args.verbose:
            print("✓ Fase 3: Generación MIPS completada")

        # --- ESCRITURA DE SALIDA (MODIFICADO) ---
        
        # Determinar path de salida
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix('.s')
        
        # Escribir salida MIPS
        output_path.write_text(mips_code, encoding='utf-8')
        if args.verbose:
            print(f"\n✓ Compilación exitosa: Código MIPS escrito en: {output_path}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\nError inesperado durante la compilación: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()