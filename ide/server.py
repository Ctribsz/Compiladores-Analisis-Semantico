import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# -------------------------------------------------------------------
# Rutas / imports
# -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# --- ANTLR imports ---
from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener
from program.gen.CompiscriptLexer import CompiscriptLexer
from program.gen.CompiscriptParser import CompiscriptParser

# --- Semántico / utilidades ---
from semantic.semantic_visitor import run_semantic
from semantic.scope import serialize_scope

# -------------------------------------------------------------------
# Error listener de sintaxis
# -------------------------------------------------------------------
class SyntaxErrorCollector(ErrorListener):
    def __init__(self) -> None:
        super().__init__()
        self.items: List[Dict[str, Any]] = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e) -> None:
        self.items.append({
            "line": int(line),
            "column": int(column),
            "code": "SYN",
            "message": msg
        })

# -------------------------------------------------------------------
# App FastAPI
# -------------------------------------------------------------------
app = FastAPI(title="Compiscript IDE")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="static")

class AnalyzeBody(BaseModel):
    source: str
    generate_tac: bool = False  # Opción para generar TAC
    optimize_tac: bool = False  # Opción para optimizar TAC

def _pick(obj: Any, names: List[str], default: Optional[Any] = None) -> Any:
    """Obtiene el primer atributo/clave disponible de 'names' en obj."""
    for n in names:
        if isinstance(obj, dict) and n in obj:
            return obj[n]
        if hasattr(obj, n):
            return getattr(obj, n)
    return default

@app.post("/analyze")
def analyze(body: AnalyzeBody):
    """
    Analiza código Compiscript con opción de generar TAC
    """
    try:
        # 1) Lexer/Parser
        input_stream = InputStream(body.source)
        lexer = CompiscriptLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = CompiscriptParser(stream)

        syn = SyntaxErrorCollector()
        parser.removeErrorListeners()
        parser.addErrorListener(syn)

        tree = parser.program()

        # 2) Errores sintácticos
        if syn.items:
            return JSONResponse({
                "ok": False, 
                "errors": syn.items, 
                "symbols": None,
                "tac": None
            }, status_code=422)

        # 3) Análisis semántico
        sem = run_semantic(tree)

        # Adaptador de errores semánticos
        items: List[Dict[str, Any]] = []
        seq = None
        if hasattr(sem, "items"):
            seq = sem.items
        elif hasattr(sem, "errors"):
            seq = sem.errors

        if isinstance(seq, list) and seq:
            for it in seq:
                if isinstance(it, dict):
                    l = int(_pick(it, ["line", "lineno", "row"], 0) or 0)
                    c = int(_pick(it, ["column", "col"], 0) or 0)
                    code = str(_pick(it, ["code", "error_code", "id"], "E???"))
                    msg = str(_pick(it, ["message", "msg", "text"], ""))
                    items.append({"line": l, "column": c, "code": code, "message": msg})
                elif isinstance(it, tuple) and len(it) >= 4:
                    l, c, code, msg = it[:4]
                    items.append({"line": int(l), "column": int(c), "code": str(code), "message": str(msg)})
                else:
                    l = int(_pick(it, ["line", "lineno", "row"], 0) or 0)
                    c = int(_pick(it, ["column", "col"], 0) or 0)
                    code = str(_pick(it, ["code", "error_code", "id"], "E???"))
                    msg = str(_pick(it, ["message", "msg", "text"], ""))
                    items.append({"line": l, "column": c, "code": code, "message": msg})
        else:
            # No hay colección accesible: intentar parsear pretty()
            pretty = sem.pretty() if hasattr(sem, "pretty") else ""
            for ln in pretty.splitlines():
                m = re.match(r"\[(E\d+|SYN)\]\s*\((\d+):(\d+)\)\s*(.*)", ln.strip())
                if m:
                    code, l, c, msg = m.groups()
                    items.append({"line": int(l), "column": int(c), "code": code, "message": msg})

        ok = len(items) == 0
        
        # 3b) Tabla de símbolos
        global_scope = getattr(sem, "global_scope", None) or getattr(sem, "scope", None)
        symbols_payload = serialize_scope(global_scope) if global_scope is not None else None

        # 4) Generación de TAC si se solicita y no hay errores
        tac_payload = None
        if ok and body.generate_tac:
            try:
                from intermediate.runner import generate_intermediate_code
                from intermediate.optimizer import TACOptimizer
                
                tac_result = generate_intermediate_code(tree)
                
                if not tac_result.has_errors:
                    tac_program = tac_result.tac_program
                    
                    # Optimizar si se pidió
                    if body.optimize_tac:
                        optimizer = TACOptimizer(tac_program)
                        tac_program = optimizer.optimize()
                    
                    tac_payload = {
                        "code": tac_program.to_list(),
                        "stats": {
                            "instructions": len(tac_program.instructions),
                            "temporals": tac_program.temp_counter,
                            "labels": tac_program.label_counter
                        }
                    }
            except ImportError:
                # Módulo TAC no disponible
                pass
            except Exception as e:
                # Error generando TAC
                items.append({
                    "line": 0, 
                    "column": 0, 
                    "code": "TAC_ERR", 
                    "message": f"Error generando TAC: {str(e)}"
                })
                ok = False

        status = 200 if ok else 422
        return JSONResponse({
            "ok": ok, 
            "errors": items, 
            "symbols": symbols_payload,
            "tac": tac_payload
        }, status_code=status)

    except Exception as e:
        # Error inesperado en el servidor
        return JSONResponse(
            {
                "ok": False, 
                "errors": [{"code": "EXC", "message": str(e), "line": 0, "column": 0}], 
                "symbols": None,
                "tac": None
            },
            status_code=500
        )

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    """
    Sube un archivo .cps y devuelve su contenido para cargarlo en el editor.
    """
    name = (file.filename or "").strip()
    if not name.lower().endswith(".cps"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .cps")
    content_bytes = await file.read()
    content = content_bytes.decode("utf-8", errors="replace")
    return {"ok": True, "filename": name, "code": content}

@app.get("/")
def index():
    """
    Sirve la UI del IDE (index.html).
    """
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))