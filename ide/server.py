import os, sys, re
from pathlib import Path
from typing import List, Dict
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # para 'program.*'

# --- ANTLR imports (layout plano detectado) ---
from program.gen.CompiscriptLexer import CompiscriptLexer
from program.gen.CompiscriptParser import CompiscriptParser
from program.gen.CompiscriptVisitor import CompiscriptVisitor

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

# --- tu semántico ---
from semantic.semantic_visitor import run_semantic

# -------------------------------------
# Error listener sintáctico a JSON
# -------------------------------------
class SyntaxErrorCollector(ErrorListener):
    def __init__(self):
        super().__init__()
        self.items: List[Dict] = []
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.items.append({
            "line": int(line),
            "column": int(column),
            "code": "SYN",
            "message": msg
        })

# -------------------------------------
# app FastAPI
# -------------------------------------
app = FastAPI(title="Compiscript IDE")
app.mount(
    "/static",
    StaticFiles(directory=str(Path(__file__).parent / "static"), html=False),
    name="static",
)

class AnalyzeBody(BaseModel):
    source: str

@app.post("/analyze")
def analyze(body: AnalyzeBody):
    # 1) Parser
    input_stream = InputStream(body.source)
    lexer = CompiscriptLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = CompiscriptParser(stream)

    syn = SyntaxErrorCollector()
    parser.removeErrorListeners()
    parser.addErrorListener(syn)

    tree = parser.program()

    # 2) Si hay errores sintácticos -> devolverlos
    if syn.items:
        return {"ok": False, "errors": syn.items}

    # 3) Semántico
    sem = run_semantic(tree)

    # --- Adaptador robusto de errores -> JSON ---
    def pick(obj, names, default=None):
        for n in names:
            if isinstance(obj, dict) and n in obj:
                return obj[n]
            if hasattr(obj, n):
                return getattr(obj, n)
        return default

    items = []

    # Caso 1: colección directa (lista) en sem.items / sem.errors
    seq = None
    if hasattr(sem, "items"):
        seq = sem.items
    elif hasattr(sem, "errors"):
        seq = sem.errors

    if isinstance(seq, list) and seq:
        for it in seq:
            # dict
            if isinstance(it, dict):
                l = int(pick(it, ["line", "lineno", "row"], 0) or 0)
                c = int(pick(it, ["column", "col"], 0) or 0)
                code = str(pick(it, ["code", "error_code", "id"], "E???"))
                msg  = str(pick(it, ["message", "msg", "text"], ""))
                items.append({"line": l, "column": c, "code": code, "message": msg})
            # tupla (line, col, code, msg)
            elif isinstance(it, tuple) and len(it) >= 4:
                l, c, code, msg = it[:4]
                items.append({"line": int(l), "column": int(c), "code": str(code), "message": str(msg)})
            # objeto (SemError)
            else:
                l = int(pick(it, ["line", "lineno", "row"], 0) or 0)
                c = int(pick(it, ["column", "col"], 0) or 0)
                code = str(pick(it, ["code", "error_code", "id"], "E???"))
                msg  = str(pick(it, ["message", "msg", "text"], ""))
                items.append({"line": l, "column": c, "code": code, "message": msg})
    else:
        # Caso 2: no hay colección accesible → parsear pretty() "[EXXX] (l:c) msg"
        pretty = sem.pretty() if hasattr(sem, "pretty") else ""
        for ln in pretty.splitlines():
            m = re.match(r"\[(E\d+|SYN)\]\s*\((\d+):(\d+)\)\s*(.*)", ln.strip())
            if m:
                code, l, c, msg = m.groups()
                items.append({"line": int(l), "column": int(c), "code": code, "message": msg})

    ok = len(items) == 0
    return {"ok": ok, "errors": items}


@app.get("/")
def index():
    index_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))