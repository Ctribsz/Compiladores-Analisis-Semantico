import sys, os
from antlr4 import FileStream, CommonTokenStream
from gen.CompiscriptLexer import CompiscriptLexer
from gen.CompiscriptParser import CompiscriptParser
from antlr4.error.ErrorListener import ErrorListener



sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# --- Listener para errores sintácticos bonitos
class SyntaxErrorCollector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.count = 0
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.count += 1
        print(f"[SYN] ({line}:{column}) {msg}")

def main(argv):
    if len(argv) < 2:
        print("Uso: python program/Driver.py <archivo.cps>")
        sys.exit(2)

    input_stream = FileStream(argv[1], encoding="utf-8")
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)

    syn_errors = SyntaxErrorCollector()
    parser.removeErrorListeners()
    parser.addErrorListener(syn_errors)

    tree = parser.program()  # regla inicial (según la gramática)

    if syn_errors.count > 0:
        sys.exit(1)

    # --- Análisis semántico
    from semantic.semantic_visitor import run_semantic
    sem_errors = run_semantic(tree)

    if sem_errors.has_errors():
        print(sem_errors.pretty())
        sys.exit(1)

    # Si todo bien, no imprime nada (comportamiento pedido)
    # print("OK")  # si se quiere confirmar

if __name__ == '__main__':
    main(sys.argv)
