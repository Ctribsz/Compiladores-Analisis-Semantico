#!/usr/bin/env python3
"""
Driver CLI para generar código intermedio TAC
Uso: python -m intermediate.tac_driver archivo.cps [opciones]
"""
import sys
import os
import argparse
from pathlib import Path

# Configurar path para imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from program.gen.CompiscriptLexer import CompiscriptLexer
from program.gen.CompiscriptParser import CompiscriptParser
from intermediate.runner import generate_intermediate_code

class SyntaxErrorCollector(ErrorListener):
    """Colector de errores sintácticos"""
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
    """Función principal del driver TAC"""
    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description='Generador de código intermedio TAC para Compiscript'
    )
    parser.add_argument(
        'input_file',
        help='Archivo fuente Compiscript (.cps)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Archivo de salida para el código TAC',
        default=None
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mostrar información detallada'
    )
    parser.add_argument(
        '--no-optimize',
        action='store_true',
        help='Desactivar optimizaciones (por implementar)'
    )
    parser.add_argument(
        '--format',
        choices=['tac', 'json', 'debug'],
        default='tac',
        help='Formato de salida'
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: El archivo '{input_path}' no existe", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.suffix == '.cps':
        print(f"Advertencia: Se esperaba un archivo .cps", file=sys.stderr)
    
    if args.verbose:
        print(f"Procesando: {input_path}")
        print(f"=" * 50)
    
    try:
        # Fase 1: Análisis léxico y sintáctico
        input_stream = FileStream(str(input_path), encoding='utf-8')
        lexer = CompiscriptLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(token_stream)
        
        # Configurar listener de errores
        syntax_collector = SyntaxErrorCollector()
        parser.removeErrorListeners()
        parser.addErrorListener(syntax_collector)
        
        # Parsear
        tree = parser.program()
        
        # Verificar errores sintácticos
        if syntax_collector.errors:
            print("Errores sintácticos encontrados:", file=sys.stderr)
            for error in syntax_collector.errors:
                print(f"  [{error['line']}:{error['column']}] {error['message']}", 
                      file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print("✓ Análisis sintáctico completado")
        
        # Fase 2: Análisis semántico y generación de TAC
        result = generate_intermediate_code(tree)
        
        if result.has_errors:
            print("Errores semánticos encontrados:", file=sys.stderr)
            for error in result.errors:
                print(f"  [{error.code}] ({error.line}:{error.col}) {error.msg}", 
                      file=sys.stderr)
            sys.exit(1)
        
        if args.verbose:
            print("✓ Análisis semántico completado")
            print("✓ Código intermedio generado")
            print(f"  Instrucciones TAC: {len(result.tac_program.instructions)}")
            print(f"  Temporales usados: {result.tac_program.temp_counter}")
            print(f"  Etiquetas usadas: {result.tac_program.label_counter}")
        
        # Generar salida según formato
        if args.format == 'tac':
            output = result.get_tac_code()
        elif args.format == 'json':
            import json
            output = json.dumps({
                'instructions': result.get_tac_lines(),
                'temp_count': result.tac_program.temp_counter,
                'label_count': result.tac_program.label_counter
            }, indent=2)
        elif args.format == 'debug':
            output = f"# Código TAC generado desde {input_path.name}\n"
            output += f"# Temporales: {result.tac_program.temp_counter}\n"
            output += f"# Etiquetas: {result.tac_program.label_counter}\n"
            output += f"# Instrucciones: {len(result.tac_program.instructions)}\n"
            output += "#" + "="*50 + "\n\n"
            output += result.tac_program.to_string(numbered=True)  # usamos la versión numerada

        else:
            output = result.get_tac_code()
        
        # Escribir salida
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(output, encoding='utf-8')
            if args.verbose:
                print(f"\n✓ Código TAC escrito en: {output_path}")
        else:
            # Imprimir a stdout
            if args.verbose:
                print("\nCódigo TAC generado:")
                print("=" * 50)
            print(output)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()