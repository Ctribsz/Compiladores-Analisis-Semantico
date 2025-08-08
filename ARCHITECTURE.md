# 🧪 Compiscript – Arquitectura & Plan de Trabajo  
*(Fase de Análisis Semántico – 3 personas)*

---

## 1. Tecnologías y Decisiones Clave

| Decision | Motivo |
|---|---|
| **ANTLR Visitor** | Más control que Listener; facilita devolver y propagar tipos. |
| **ANTLR sin Docker** | Menos fricción → `pip install antlr4-python3-runtime` + JAR oficial. |
| **IDE Web ligero** | Monaco-editor + FastAPI; 15 pts sin escribir extensión VS Code. |
| **Tabla de símbolos** | Stack de scopes (`List[Dict[str, Symbol]]`). |
| **Tests** | `.cps` en `tests/valid/` y `tests/invalid/` + pytest runner. |

---

## 2. Estructura Final del Repositorio

```
compiscript-semantico/
├── program/
│   ├── Compiscript.g4
│   ├── Compiscript.interp / .tokens (generados)
│   └── Driver.py            # CLI de prueba rápida
├── semantic/
│   ├── __init__.py
│   ├── SymbolTable.py       # stack de scopes
│   ├── SemanticVisitor.py   # hereda de CompiscriptVisitor
│   └── TypeChecker.py       # helpers de compatibilidad
├── ide/
│   ├── server.py            # FastAPI
│   ├── static/
│   │   ├── index.html
│   │   └── main.js          # Monaco
│   └── Dockerfile           # opcional para la entrega
├── tests/
│   ├── test_semantic.py     # pytest que recorre .cps
│   ├── valid/               # casos exitosos
│   └── invalid/             # casos que deben fallar
├── README.md                # cómo correr todo
└── requirements.txt         # antlr4-python3-runtime, fastapi, uvicorn, pytest
```

---

## 3. Flujo de Trabajo Local (sin Docker)

```bash
# 1. Generar parser
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 program/Compiscript.g4

# 2. Ejecutar un archivo
python program/Driver.py archivo.cps

# 3. Suite de tests
pytest tests/

# 4. Levantar IDE web
uvicorn ide.server:app --reload --port 3000
# abrir http://localhost:3000
```

---

## 4. Convención de Tests

| Carpeta | Contenido | Ejemplo |
|---|---|---|
| `tests/valid/` | `.cps` que **deben compilar sin errores**. | `01_arithmetic_ok.cps` |
| `tests/invalid/` | `.cps` que **deben lanzar error semántico**. | `02_undeclared_var.cps` |

Plantilla de cabecera en cada archivo `.cps`:
```
// TEST: VALID
// Verifica que la suma de enteros funcione
```

El runner `test_semantic.py` lee la cabecera y comprueba el resultado esperado.

---

## 5. División de Trabajo (3 personas)

| Integrante | Responsabilidad Principal | Archivos / Tareas |
|---|---|---|
| **A – Tabla & Scopes** | 25 pts | `SymbolTable.py`, manejo de scopes, re-declaraciones, variables no declaradas. |
| **B – Visitor & Tipos** | 35 pts | `SemanticVisitor.py`, `TypeChecker.py`, operaciones aritméticas/lógicas, asignaciones, funciones, clases. |
| **C – IDE & Tests** | 25 + 15 = 40 pts | `ide/`, `tests/`, casos `.cps`, runner pytest, documentación final. |

> **Criterio de equidad:** Cada integrante tiene **~33-35 pts de trabajo**, salvo C que además hace el IDE (15 pts). Si alguien termina antes, ayuda al que falte.
