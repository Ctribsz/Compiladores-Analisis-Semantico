# Compiscript – M1: Análisis Semántico (Python + ANTLR4)

Front-end parcial para **Compiscript** (subset de TypeScript).
Incluye **lexer/parser** generados con ANTLR4, **análisis semántico** en Python (dos pases) y un **IDE web** minimal (FastAPI + Monaco) que muestra errores en el editor.

**Comportamiento esperado del analizador**

* Si el `.cps` está correcto → **no imprime nada** (exit code `0`).
* Si hay errores → imprime líneas tipo:

  ```
  [E004] (12:3) No se puede asignar 'string' a 'integer'.
  ```

  y retorna `exit code != 0`.

---

## Requisitos

* Python 3.10+ (recomendado 3.11).
* Java 8+ (para ejecutar el JAR de ANTLR).
* Paquetes Python:

  ```
  pip install -r requirements.txt
  ```

  (incluye `antlr4-python3-runtime`, `fastapi`, `uvicorn`, `pytest` si lo agregas).

---

## 1) Generar lexer/parser con ANTLR

La gramática está en `program/Compiscript.g4`. Desde la **raíz** del repo:

```bash
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor \
  -o program/gen -Xexact-output-dir program/Compiscript.g4
```

Esto crea en `program/gen/`:

```
CompiscriptLexer.py  CompiscriptParser.py  CompiscriptVisitor.py  (y .interp/.tokens)
```

> No edites nada dentro de `program/gen/`. Si cambias la gramática, vuelve a ejecutar el comando.

---

## 2) Ejecutar el analizador sobre un archivo

```bash
python -m program.Driver program/program.cps
```

# TAC “normal”
```bash
python -m intermediate.tac_driver program/program.cps --format tac -v
```
# TAC numerado (útil para depurar)
```bash
python -m intermediate.tac_driver program/program.cps --format debug -v
```

* Si no hay errores → no imprime nada.
* Si hay errores → imprime `[EXXX] (línea:col) mensaje` y retorna `!= 0`.

> Consejo: ejecuta siempre desde la **raíz** del repo para que los imports funcionen.

---

## 3) IDE web (FastAPI + Monaco)

Estructura:

```
ide/
├── server.py          # endpoint /analyze + estáticos
└── static/
    ├── index.html     # UI del editor
    └── main.js        # lógica del editor (análisis, markers)
```

Levantar el IDE:

```bash
uvicorn ide.server:app --reload --port 3000
# abre http://localhost:3000
```

Cómo funciona:

* El frontend envía el código a `POST /analyze`.
* El backend corre parser + Pass1 + Pass2.
* Devuelve `{"ok": true}` o `{"ok": false, "errors": [...]}`.
* El editor marca los errores en la UI.

> Si ves `405 Method Not Allowed` en `/analyze`, es que montaste estáticos en `/`.
> En `server.py` dejamos `/static` para estáticos y un handler `GET /` que sirve `index.html`.

---

### 3.1) Ver TAC y optimizar desde el IDE

Marca la casilla TAC para ver el código intermedio.

Marca Optimizar para aplicar el optimizador local.

El backend usa intermediate.runner.generate_intermediate_code y (si pides optimizar) intermediate.optimizer.TACOptimizer.

## 4) Suite de tests

Coloca tus casos en:

```
tests/
├── valid/    # casos que deben compilar SIN errores
└── invalid/  # casos que deben producir errores
```

Runner (ejemplo sugerido) en `scripts/run_tests.py`:

```bash
python scripts/run_tests.py                 # corre valid + invalid
python scripts/run_tests.py --only valid
python scripts/run_tests.py --only invalid --show-invalid
```

Criterio:

* `valid/` → exit code `0` (OK).
* `invalid/` → exit code `!= 0` (OK porque era esperado).
  Con `--show-invalid` también muestra los mensajes de error.

---

## 5) Estructura del proyecto

```
.
├── antlr-4.13.1-complete.jar
├── ide/
│   ├── server.py
│   └── static/ (index.html, main.js)
intermediate/
|  ├── tac.py             # IR: TACOp, TACOperand, TACInstruction, TACProgram
|  ├── tac_generator.py   # Visitor que recorre el AST y emite TAC
|  ├── optimizer.py       # Optimizaciones locales (folding, copy-prop, etc.)
|  ├── tac_driver.py      # CLI para generar TAC desde .cps
|  ├── runner.py          # Helper para integrarlo con el IDE/servidor

├── program/
│   ├── Compiscript.g4        # gramática ANTLR
│   ├── program.cps           # ejemplo
│   ├── Driver.py             # CLI del analizador
│   └── gen/                  # (GENERADO) lexer/parser/visitor
├── semantic/
│   ├── errors.py             # ErrorCollector (report/pretty)
│   ├── scope.py              # Scopes (árbol padre-hijo)
│   ├── symbols.py            # VariableSymbol, FunctionSymbol, ClassSymbol
│   ├── types.py              # INTEGER, STRING, BOOLEAN, NULL, ArrayType, ClassType, FunctionType...
│   └── semantic_visitor.py   # Pass 1 (símbolos) + Pass 2 (tipado/reglas)
├── scripts/
│   └── run_tests.py          # runner de la suite
├── tests/                    # casos valid/ e invalid/
└── requirements.txt
```

---
## 5.1) Especificación del Lenguaje Intermedio (TAC)

Instrucción: formato cuadrúplo op result, arg1, arg2 (o variantes: PRINT arg1, GOTO Lx, LABEL Lx, PARAM arg1, CALL f, n).

Conjunto de ops (principales):
ASSIGN, ADD, SUB, MUL, DIV, MOD, NEG, NOT, LT, LE, GT, GE, EQ, NE,
GOTO, IF_TRUE, IF_FALSE, LABEL, PRINT,
PARAM, CALL, RETURN,
NEW, ARRAY_ACCESS, ARRAY_ASSIGN, FIELD_ACCESS, FIELD_ASSIGN,
FUNC_START, FUNC_END.

Temporales y etiquetas: generados por TACProgram.new_temp() / new_label() con reciclaje de temporales vía free_temp.

Bajos supuestos de representación:

Arrays: NEW t, size crea arreglo; t[i]/t[i] = v → ARRAY_ACCESS/ARRAY_ASSIGN.

Objetos/clases: FIELD_ACCESS t, obj, "x" y FIELD_ASSIGN obj, "x", v.

Llamadas: PARAM arg* seguido de CALL f, n (el resultado, si existe, va a un temporal).

Control de flujo: if, while, do-while, for, switch se traducen a LABEL/IF_*/GOTO.

Mini ejemplo: 
```bash
let x: integer = 2 + 3;
let y: integer = x * 4;
if ((x == 5) && (y != 0)) { print("then"); } else { print("else"); }


0000: t1 = 2 add 3
0001: x = t1
0002: t1 = x mul 4
0003: y = t1
0004: t1 = x == 5
0005: ifFalse t1 goto L0
0006: t1 = y != 0
0007: t2 = t1
0008: goto L1
0009: L0:
0010: t2 = false
0011: L1:
0012: ifFalse t2 goto L2
0013: print "then"
0014: goto L3
0015: L2:
0016: print "else"
0017: L3:
```

## 6) ¿Qué valida el analizador?

### Declaraciones & asignaciones

* Redeclaración (E001), uso de no declarado (E002), `const` sin init (E003 si aplica).
* Incompatibilidad de tipos (E004), reasignar `const` (E005), LHS inválido (E006).
* **Inferencia** en `let/const` si no hay anotación (toma el tipo del initializer).

### Expresiones

* `!` y `-` unario; `&&`, `||`; relacionales; `+/-` (concat string si ambos string); `* / %` solo enteros.
* Paréntesis tipan correctamente.

### Arreglos

* Literales homogéneos (E011 si mezclas).
* Indexación `a[i]`: `i` entero (E030) y receptor arreglo (E031).

### Funciones

* `return`: tipo correcto (E012) y “todas las rutas retornan” si la función declara retorno (E015).
* Llamadas: aridad (E021), tipos por argumento (E022), llamada a no-función (E020).

### Control de flujo

* Condiciones booleanas en `if/while/do/for` (E040).
* `break/continue` solo dentro de loops (E041/E042).
* `return` fuera de función (E014).

### Clases, `this`, `new`

* Propiedades/métodos: no-objeto (E033), miembro inexistente (E034), asignación a propiedad verifica tipos (E004).
* `this` fuera de método de clase (E043).
* `new C(...)`: clase no declarada (E037), aridad/tipos del constructor (E021/E022).

### Herencia

* `class A : B` base no encontrada (E051), ciclo (E052).
* Overrides incompatibles (E053), conflictos de campos heredados (E054).
* El constructor **no** se hereda.

### `switch / case`

* Tipo del `switch(expr)` compatible con `case` (E060).
* `case` duplicados de literal (E061).

### Ternario `cond ? a : b`

* Condición booleana (E040).
* Tipo común de ramas (E070 si incompatibles).
* `null` permitido hacia tipos de referencia/array (regla de asignabilidad).

> Los códigos y mensajes se centralizan en `errors.py` y en `semantic_visitor.py`.

---

## 7) Flujo interno (cómo está implementado)

**Pass 1 – `SymbolCollector`**

* Construye la **tabla de símbolos**: stack de `Scope` (`scope.py`), con `define()` y `resolve()`.
* Declara variables/const (con o sin anotación), funciones (firma `FunctionType` con parámetros y retorno) y clases (`ClassSymbol` con `fields` y `methods`).
* En clases: resuelve herencia (base, ciclos, merge de miembros, verificación de overrides).
* Enlaza cada `ctx` del árbol con su `scope` para que Pass 2 pueda entrar al ámbito correcto.

**Pass 2 – `TypeCheckerVisitor`**

* Entra a los scopes guardados (global, función, bloque, clase).
* Resuelve nombres y **tipa expresiones**.
* Implementa sufijos en `leftHandSide`: llamadas `()`, indexación `[]`, acceso `.`.
* Aplica todas las reglas semánticas listadas arriba y reporta errores con línea/columna.

---

## 8) Consejos y solución de problemas

* **`ModuleNotFoundError` (gen)**

  * Asegúrate de generar en `program/gen` (usa `-Xexact-output-dir`) y crea `program/__init__.py` y `program/gen/__init__.py`.
* **`405 Method Not Allowed` en `/analyze`**

  * Monta estáticos en `/static` y sirve `GET /` con un handler (el server ya viene así).
* **IDE devuelve error JSON con atributos diferentes**

  * El `server.py` adapta distintos formatos de errores (`line/lineno`, `column/col`, etc.). Si personalizas `errors.py`, mantén esos nombres o el adaptador.
* **Ejecución del driver**

  * Usa `python -m program.Driver ...` y ejecuta desde la **raíz** del repo.

---

## 9) Lenguaje (subset soportado)

Incluye tipos primitivos (`integer`, `string`, `boolean`, `null`), arreglos `T[]`, funciones con parámetros tipados y retorno, clases con constructor y métodos, `this`, herencia, control de flujo (`if/else`, `while`, `do-while`, `for`, `foreach`, `break/continue`, `return`), `switch/case`, `try/catch`, operadores aritméticos/lógicos y ternario.

## 10) Optimizaciones implementadas

Alcance: intra-bloque (sin CFG).
Pases:

Constant Folding (aritmética, relacionales, !, - y IF_* con condición constante → GOTO/eliminación).

Constant Propagation (intra-bloque; respeta límites en LABEL/GOTO/IF_*/CALL/RETURN/PARAM/ARRAY_/FIELD_).

Copy Propagation (intra-bloque; corta alias al reescribir la fuente).

Algebraic Simplification (x+0, x-0, x*1, x*0, x/1).

Remove Redundant Moves (x=x) y Jumps (goto al LABEL inmediato; labels huérfanas).

Limitaciones (intencionadas en esta fase):

No hay CFG aún → no se hace propagación/opt global entre bloques; no se colapsan ramas que dependen de múltiples caminos.

try/catch simplificado; sin efectos de excepción reales.

No hay asignación de registros ni código máquina (eso es la siguiente fase).
> Los archivos fuente usan extensión **`.cps`**.