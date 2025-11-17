import sys
import os
from antlr4 import FileStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

# Permitir imports tipo "program.gen.*" y "semantic.*" ejecutando desde la raíz
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from program.gen.CompiscriptLexer import CompiscriptLexer
from program.gen.CompiscriptParser import CompiscriptParser

# -----------------------------
# Listener para errores sintácticos bonitos
# -----------------------------
class SyntaxErrorCollector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.count = 0

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.count += 1
        # Formato requerido por el IDE / enunciado
        print(f"[SYN] ({line}:{column}) {msg}")

# -----------------------------
# Utils para imprimir errores semánticos
# -----------------------------
def _print_semantic_errors_from_list(errors_list):
    """
    Recibe una lista de errores (dicts, tuplas u objetos con attrs)
    y los imprime como: [EXXX] (l:c) msg
    """
    def pick(obj, names, default=None):
        for n in names:
            if isinstance(obj, dict) and n in obj:
                return obj[n]
            if hasattr(obj, n):
                return getattr(obj, n)
        return default

    for it in errors_list:
        if isinstance(it, tuple) and len(it) >= 4:
            l, c, code, msg = it[:4]
            print(f"[{code}] ({int(l)}:{int(c)}) {msg}")
        else:
            l = int(pick(it, ["line", "lineno", "row"], 0) or 0)
            c = int(pick(it, ["column", "col"], 0) or 0)
            code = str(pick(it, ["code", "error_code", "id"], "E???"))
            msg  = str(pick(it, ["message", "msg", "text"], ""))
            print(f"[{code}] ({l}:{c}) {msg}")

# -----------------------------
# Main
# -----------------------------
def main(argv):
    # Parsear argumentos con más opciones
    if len(argv) < 2:
        print("Uso: python -m program.Driver <archivo.cps> [opciones]")
        print("Opciones:")
        print("  --tac          Generar código intermedio TAC")
        print("  --optimize     Aplicar optimizaciones al TAC")
        print("  --output FILE  Guardar TAC en archivo")
        sys.exit(2)

    in_path = argv[1]
    
    # Parsear flags opcionales
    generate_tac = "--tac" in argv
    optimize = "--optimize" in argv
    output_file = None
    
    if "--output" in argv:
        idx = argv.index("--output")
        if idx + 1 < len(argv):
            output_file = argv[idx + 1]
    
    if not os.path.exists(in_path):
        print(f"Archivo no encontrado: {in_path}")
        sys.exit(2)

    # 1) Parser
    input_stream = FileStream(in_path, encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)

    syn_errors = SyntaxErrorCollector()
    parser.removeErrorListeners()
    parser.addErrorListener(syn_errors)

    tree = parser.program()  # Regla inicial según tu gramática

    # 2) Si hubo errores de sintaxis -> exit 1
    if syn_errors.count > 0:
        sys.exit(1)

    # 3) Semántico
    from semantic.semantic_visitor import run_semantic
    sem = run_semantic(tree)

    # 3a) Normalizar cómo vienen los errores
    errors_list = getattr(sem, "errors", None)
    if errors_list is not None:
        has_err = len(errors_list) > 0
        if has_err:
            # Si hay pretty() úsalo; si no, imprime uno por uno
            if hasattr(sem, "pretty") and callable(getattr(sem, "pretty")):
                pretty = sem.pretty()
                if pretty:
                    print(pretty, end="" if pretty.endswith("\n") else "\n")
                else:
                    _print_semantic_errors_from_list(errors_list)
            else:
                _print_semantic_errors_from_list(errors_list)
            sys.exit(1)
        
        # Si no hay errores semánticos y pidieron TAC
        if generate_tac:
            try:
                from intermediate.runner import generate_intermediate_code
                from intermediate.optimizer import TACOptimizer
                
                # Generar TAC
                tac_result = generate_intermediate_code(tree)
                
                if tac_result.has_errors:
                    print("Errores generando TAC:", file=sys.stderr)
                    for error in tac_result.errors:
                        print(f"  [{error.code}] ({error.line}:{error.col}) {error.msg}", 
                              file=sys.stderr)
                    sys.exit(1)
                
                tac_program = tac_result.tac_program
                
                # Aplicar optimizaciones si se pidió
                if optimize:
                    optimizer = TACOptimizer(tac_program)
                    tac_program = optimizer.optimize()
                    print(f"# TAC optimizado (reducción de {tac_result.tac_program.temp_counter - tac_program.temp_counter} temporales)")
                
                # Generar salida
                tac_code = str(tac_program)
                
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(tac_code)
                    print(f"TAC generado en: {output_file}")
                else:
                    print("\n=== CÓDIGO INTERMEDIO TAC ===")
                    print(tac_code)
                    print("=== FIN TAC ===\n")
                    
            except ImportError:
                print("Módulo de generación TAC no disponible. Instale las dependencias.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error generando TAC: {e}", file=sys.stderr)
                sys.exit(1)
        
        # Si no hay errores y no pidieron TAC, comportamiento normal (exit 0 sin imprimir nada)
        sys.exit(0)

    # Caso B: compatibilidad con ErrorCollector clásico
    has_err = False
    if hasattr(sem, "has_errors") and callable(getattr(sem, "has_errors")):
        has_err = sem.has_errors()
    if has_err:
        if hasattr(sem, "pretty") and callable(getattr(sem, "pretty")):
            out = sem.pretty()
            if out:
                print(out, end="" if out.endswith("\n") else "\n")
        sys.exit(1)

    # OK
    sys.exit(0)

if __name__ == "__main__":
    main(sys.argv)