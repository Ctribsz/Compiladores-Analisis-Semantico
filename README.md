# Compilador de Compiscript a MIPS 🚀

## Enlace a video entrega final
https://drive.google.com/file/d/17bVLYLLCcGjHsjT4fnIV3XRCxFSJrFeu/view?usp=sharing 

Este proyecto es un compilador completo escrito en Python que traduce código de un lenguaje de programación de alto nivel, orientado a objetos (llamado **Compiscript**) a código ensamblador MIPS (`.s`).

El compilador maneja todo el flujo: desde el análisis léxico/sintáctico, pasando por el análisis semántico (tipos, scopes) y la generación de código intermedio (TAC), hasta la generación final de código MIPS ejecutable en simuladores como MARS.

## 🌟 Características Principales

El lenguaje Compiscript soporta:

* **Tipos de Datos:** `integer`, `string`, `boolean`, `null`.
* **Declaraciones:** Variables (`let`, `var`) y constantes (`const`).
* **Estructuras de Control:** `if-else`, `while`, `do-while`, `for`, `switch`.
* **Programación Orientada a Objetos:**
    * `class`
    * Herencia (ej. `class Estudiante : Persona`)
    * Puntero `this`
    * Constructores (`constructor`)
    * Métodos y propiedades de instancia
* **Funciones:** Declaración, llamadas y recursión (ej. `fibonacci`).
* **Entrada/Salida:** Una función `print()` integrada.
* **Expresiones:** Operaciones aritméticas, lógicas y relacionales.

## 🛠️ Cómo Ejecutarlo

### Prerrequisitos

1.  **Python 3.x**
2.  **ANTLR4 Python Runtime:**
    ```sh
    pip install antlr4-python3-runtime
    ```
3.  **Simulador MIPS:** [**MARS**](https://courses.missouristate.edu/kenvollmar/mars/) (para correr el `.s` final).

### Pasos de Ejecución

El driver principal es `mips.mips_driver.py`. [cite: 19] Se ejecuta como un módulo de Python.

#### 1. Compilar tu archivo `.cps`

Usá este comando en tu terminal. El ejemplo usa `archivoPruebaFinal.cps` y lo compila a `final.s`:

```sh
python -m mips.mips_driver archivoPruebaFinal.cps -o final.s
```

**Comando con opciones (recomendado para debug):**

```sh
# -v: Modo "verbose" (muestra los pasos en la terminal)
# --no-optimize: Salta el paso de optimización de TAC
python -m mips.mips_driver archivoPruebaFinal.cps -o final.s -v --no-optimize
```

#### 2. Ejecutar el resultado en MARS

1.  Abrí el simulador MARS.
2.  Andá a `File > Open...` y seleccioná el archivo `final.s` que acabás de generar.
3.  Presioná `F3` (o `Run > Assemble`) para ensamblarlo.
4.  Presioná `F5` (o `Run > Go`) para ejecutarlo.
5.  ¡Revisá la consola de MARS para ver el resultado de `print(log)`!

---

## 📁 Estructura del Proyecto

El proyecto está organizado en módulos que representan las fases clásicas de un compilador:

```
.
├── archivoPruebaFinal.cps      # 1. El código fuente de entrada
├── final.s             # 6. El código MIPS de salida
│
├── intermediate/       # 3. Fase de Código Intermedio
│   ├── tac_generator.py  # <- (IMPORTANTE) Visitor que convierte AST -> TAC
│   ├── optimizer.py      # <- (Opcional) Limpiador de código TAC
│   └── tac.py            #    Define las instrucciones TAC (TACOp, etc.)
│
├── mips/               # 4. Fase de Backend (Generación MIPS)
│   ├── mips_driver.py    # <- (IMPORTANTE) El ejecutable principal (main)
│   ├── mips_generator.py # <- (IMPORTANTE) Convierte TAC -> MIPS Assembly
│   └── runtime.py        # <- (IMPORTANTE) "Librería" MIPS para I/O, strings, etc.
│
├── program/            # (Generado por ANTLR)
│   ├── CompiscriptLexer.py
│   └── CompiscriptParser.py
│
└── semantic/           # 2. Fase de Análisis Semántico
    ├── semantic_visitor.py # <- (EL CEREBRO) Contiene SymbolCollector y TypeChecker
    ├── scope.py            #    Define la lógica de Scopes (ámbitos)
    └── symbols.py          #    Define Clases, Funciones y Variables como símbolos
```

---

## 🧠 Flujo del Compilador (¿Cómo funciona?)

Cuando ejecutás el comando, esto es lo que pasa paso a paso:

1.  **Fase 1: Parsing (ANTLR)**
    * `mips_driver.py` lee `archivoPruebaFinal.cps`. 
    * `CompiscriptLexer` divide el texto en "tokens" (`let`, `i`, `=`, `1`, `;`).
    * `CompiscriptParser` revisa que los tokens sigan las reglas gramaticales y construye un **AST (Abstract Syntax Tree)**, que es un árbol que representa la lógica del programa.

2.  **Fase 2: Análisis Semántico (El Cerebro - `semantic/`)**
    * El driver pasa el AST a los visitors de `semantic_visitor.py`. [cite: 18]
    * **Pase 1: `SymbolCollector`**
        * **Qué hace:** Recorre el árbol y "descubre" todas tus variables, funciones y clases.
        * **Cómo:** Crea "Scopes" (ámbitos) y una **Tabla de Símbolos**[cite: 18]. Así sabe que `log` es global, pero que `a` y `b` en `fibonacci` solo existen dentro de esa función.
        * **Función Clave:** Aquí calcula los **offsets de memoria**. Decide que las variables locales como `fk` vivirán en el stack (`FP[-52]` en el `.s`), y calcula el `frame_size` (tamaño de la "caja" de memoria) para cada función.
    * **Pase 2: `TypeCheckerVisitor`**
        * **Qué hace:** Recorre el árbol otra vez, pero ahora usa la Tabla de Símbolos para validar las reglas del lenguaje.
        * **Cómo:** Valida que `if (condicion)` use un booleano, que no puedas sumar un `integer` con un `string` (a menos que sea concatenación), y que no uses variables no declaradas.

3.  **Fase 3: Código Intermedio (El Borrador - `intermediate/`)**
    * **`tac_generator.py`** [cite: 11]
        * **Qué hace:** Convierte el AST (que es un árbol complejo) en **TAC (Three-Address Code)**, que es una lista de instrucciones simples y planas.
        * **Ejemplo:** `let r: integer = a + b;` se convierte en:
            ```
            t12 = FP[-4] add FP[-8]  # Carga 'a' y 'b' del stack, suma, guarda en t12
            FP[-12] = t12             # Asigna t12 al espacio de memoria de 'r'
            ```
        * Este paso es crucial porque "aplana" la lógica, haciendo la traducción a MIPS mucho más fácil.

4.  **Fase 4: Optimización (Opcional - `intermediate/`)**
    * **`optimizer.py`** [cite: 12]
        * **Qué hace:** Lee la lista TAC y la "limpia" para que sea más eficiente.
        * **Ejemplo:** Si viera `t1 = 2 + 3`, lo reemplazaría por `t1 = 5` (Constant Folding).
        * (En tu comando lo desactivaste con `--no-optimize`, por eso el `.s` es tan largo y directo).

5.  **Fase 5: Generación de Backend (El Traductor - `mips/`)**
    * **`mips_generator.py`** [cite: 20]
        * **Qué hace:** Es el traductor final. Lee cada instrucción TAC (plana y simple) y la convierte en una o más instrucciones MIPS.
        * **Ejemplo:** `t12 = FP[-4] add FP[-8]` se convierte en:
            ```mips
            lw $t0, -4($fp)     # Carga 'a' de la memoria al registro t0
            lw $t1, -8($fp)     # Carga 'b' de la memoria al registro t1
            add $t2, $t0, $t1   # Suma t0 y t1, guarda en t2
            sw $t2, -68($fp)    # Guarda t2 (que es t12) en su espacio del stack
            ```
    * **`runtime.py`** [cite: 22]
        * `mips_generator` no genera el código para `print` o `toString` cada vez.
        * Simplemente genera una *llamada* (`jal`) a las funciones pre-escritas en `runtime.py`, como `_print_string` o `_int_to_string`. Es la "librería estándar" de tu lenguaje.

6.  **Fase 6: Archivo Final (`final.s`)**
    * Es un archivo de texto plano que contiene todo el código MIPS Assembly generado.
    * Está listo para ser ensamblado y ejecutado por un simulador como MARS.

---

## 🪄 La "Magia" Explicada (Conceptos Clave)

#### 1. ¿Qué es el `.s` que MARS ejecuta?
Es un archivo de **código ensamblador** (Assembly). Es la representación "legible por humanos" del código máquina (binario) que un procesador ejecuta.

MARS es un **simulador**:
1.  **Ensambla:** Lee tu archivo `.s` y lo traduce a código máquina real (`00010101001010...`).
2.  **Simula:** Finge ser un procesador MIPS y ejecuta ese código máquina, instrucción por instrucción.

#### 2. ¿Cómo es posible la Recursión (Fibonacci)?
La respuesta es una palabra: **El Stack (La Pila)**.

El stack es un área de memoria temporal "LIFO" (Last In, First Out). Tu compilador lo usa para crear un **Stack Frame** (una "caja" de memoria) por cada llamada a función.

1.  `main` llama a `fibonacci(3)`.
2.  `fibonacci(3)` crea su "caja" en el stack que contiene:
    * Sus locales: `a`, `b`, `r`.
    * La "dirección de retorno" (adónde volver en `main`).
3.  `fib(3)` llama a `fibonacci(2)`.
4.  `fibonacci(2)` crea una **NUEVA caja** *encima* de la anterior, con:
    * Sus *propios* locales: `a`, `b`, `r`.
    * Su *propia* dirección de retorno (adónde volver en `fib(3)`).
5.  `fib(2)` llama a `fib(1)`. `fib(1)` crea *otra* caja encima.
6.  `fib(1)` llega al `return 1`. Destruye su caja, restaura los registros, y salta a la dirección de retorno (volviendo a `fib(2)`).
7.  `fib(2)` ahora puede seguir ejecutando.

Esta pila de "cajas" (stack frames) es lo que permite que la recursión funcione sin que las variables locales de una llamada se mezclen con las de otra.

#### 3. ¿Cómo es posible la Herencia (Persona/Estudiante)?
Esto es una ilusión muy inteligente creada en el **Pase 2 (Análisis Semántico)**. MIPS no sabe qué es una clase.

1.  **Diseño de Memoria (Offsets):**
    * El `SymbolCollector` [cite: 18] mira `class Estudiante : Persona`.
    * Primero, copia el "plano" de memoria de `Persona`:
        * `nombre` (offset 0)
        * `edad` (offset 4)
        * `color` (offset 8)
    * Luego, añade los campos de `Estudiante` al final:
        * `grado` (offset 12)
    * Resultado: Un objeto `Estudiante` es, en memoria, un objeto `Persona` con datos extra al final.

2.  **Resolución de Métodos:**
    * Cuando tu código llama a `nombre_estudiante1.saludar()`.
    * El compilador busca `saludar` en `Estudiante`. No lo encuentra.
    * Busca en la clase base, `Persona`. **Ahí está**.
    * Entonces, el compilador genera una llamada directa a `jal Persona_saludar`.

3.  **El Puntero `this`:**
    * ¿Cómo sabe `Persona_saludar` que debe usar los datos de `nombre_estudiante1`?
    * Porque el compilador (en `tac_generator.py`) [cite: 11] *secretamente* pasa la dirección de memoria de `nombre_estudiante1` como el primer argumento (`FP[8]`) a `Persona_saludar`. A esto le llamamos `this`.
    * La función `Persona_saludar` accede a `this.nombre`, lo que el `mips_generator` [cite: 20] traduce a "cargar memoria desde la dirección `this` + offset 0".
    * Como el plano de memoria es compatible, `offset 0` siempre es `nombre`, sin importar si el objeto es `Persona` o `Estudiante`.
