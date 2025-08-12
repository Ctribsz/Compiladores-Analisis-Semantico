# Compiscript – Fase M1: Análisis Semántico (Python + ANTLR4)
Este repo contiene un front-end parcial de Compiscript (subset de TypeScript):
lexer/parser generados con ANTLR4 y un analizador semántico en Python organizado en dos pases:

    Pass 1 – SymbolCollector: construye tabla de símbolos y ámbitos (scopes).

    Pass 2 – TypeCheckerVisitor: valida tipos, usos y reglas semánticas.

El comportamiento esperado es:

    Si el archivo .cps no tiene errores → no imprime nada.

    Si hay errores → se imprimen con el formato [E###] (línea:col) mensaje.

1) Generar lexer/parser de ANTLR

La gramática vive en program/Compiscript.g4.
Compila así (desde la raíz del repo):
```bash
java -jar antlr-4.13.1-complete.jar -Dlanguage=Python3 -visitor -o program/gen program/Compiscript.g4
```
Esto crea en program/gen/ los archivos generados (lexer, parser y visitor).

    No edites nada dentro de program/gen/ a mano.

Cada vez que cambies Compiscript.g4, vuelve a correr el comando.
2) Ejecutar el analizador sobre un archivo .cps

Hay un Driver.py de prueba rápida:
```bash
python program/Driver.py program/program.cps
```
    OK: no imprime nada.

    Error: se listan errores con código y ubicación.

3) Estructura del proyecto
```bash
.
├── program/
│   ├── Compiscript.g4         # gramática ANTLR del lenguaje
│   ├── program.cps            # ejemplo de entrada
│   └── gen/                   # (GENERADO) lexer/parser/visitor
│
├── semantic/
│   ├── errors.py              # ErrorCollector (recolecta y formatea errores)
│   ├── scope.py               # Estructura de scopes (árbol padre-hijo)
│   ├── symbols.py             # Símbolos: VariableSymbol, FunctionSymbol, ClassSymbol
│   ├── types.py               # Sistema de tipos (INTEGER, STRING, BOOLEAN, NULL,
│   │                          #              ArrayType, ClassType, FunctionType, etc.)
│   ├── semantic_visitor.py    # *** núcleo del análisis semántico (Pass 1 + Pass 2) ***
│   └── type_checker.py        # (referencia/experimentos, no requerido para correr)
│
├── tests/
│   ├── valid/                 # .cps que deben PASAR (no imprimir nada)
│   └── invalid/               # .cps que deben FALLAR (imprimir al menos un error)
│
├── antlr-4.13.1-complete.jar  # jar de ANTLR
└── requirements.txt
```
¿Qué hace cada archivo en semantic/?

    errors.py

        Clase ErrorCollector: report(line, col, code, message) y pretty() para mostrar.

    scope.py

        Clase Scope(parent) con define(symbol) y resolve(name) (búsqueda hacia arriba).

    symbols.py

        VariableSymbol(name, typ, is_const, initialized)

        FunctionSymbol(name, typ=FunctionType, params=[VariableSymbol,...])

        ClassSymbol(name, typ=ClassType, fields: dict, methods: dict, base/base_name)

    types.py

        Primitivos: INTEGER, STRING, BOOLEAN y NULL.

        Compuestos: ArrayType(elem), ClassType(name), FunctionType(params: [Type], ret: Type).

        (Opcional) Si usas : void, lo mapeamos a NULL.

    semantic_visitor.py

        Pass 1 – SymbolCollector:

            Crea scopes (global, bloque {}, función, clase).

            Declara variables/const, funciones (con firma) y clases.

            En clases, recolecta fields y methods.

            Registra el scope en cada ctx y resuelve herencia (base no encontrada, ciclos, merge de miembros, overrides compatibles).

        Pass 2 – TypeCheckerVisitor:

            Usa los scopes de Pass 1 para resolver nombres.

            Validaciones (ver lista más abajo).

            Maneja sufijos en LHS: (), [], . para llamadas, indexación y propiedades.

    type_checker.py

        Archivo auxiliar. El runtime usa semantic_visitor.py.

4) ¿Qué valida el analizador?
    Declaraciones & asignaciones

        Redeclaración (E001), uso de no declarado (E002), const sin init (E003, si aplica),
        incompatibilidad de tipos (E004), reasignación a const (E005), LHS inválido (E006).

        Inferencia de tipo en let/const si no hay anotación (desde el initializer).

    Expresiones

        Unario !/-, lógicos &&/||, relacionales, +/- (concat de string si ambos son string), *,/,% (enteros).

        Paréntesis tipados correctamente.

    Arrays

        Literales homogéneos (E011 si mezclas), indexación a[i] con i: integer (E030) y receptor arreglo (E031).

    Funciones

        Chequeo de return (E012 tipo incorrecto, E013 falta valor).

        “Todas las rutas retornan” para funciones con tipo (E015).

        Llamadas: aridad (E021), tipos por argumento (E022), llamada a no-función (E020).

    Control de flujo

        Condiciones booleanas en if/while/do/for (E040).

        break/continue solo dentro de bucles (E041/E042).

        return fuera de función (E014).

    Clases

        Acceso a propiedad/método obj.prop / obj.metodo():

            No-objeto (E033), propiedad/método inexistente (E034).

            Asignación a propiedad valida tipos (E004).

        this dentro de métodos (E043 si se usa fuera).

        new C(...): clase no declarada (E037), aridad/tipos del constructor (E021/E022).

        Herencia class A : B:

            Base no encontrada (E051), ciclo (E052), override incompatible (E053), conflicto de campo heredado (E054).

            constructor no se hereda.

    switch/case

        Tipo compatible con switch(expr) (E060), case duplicado literal (E061).

    Ternario ?:

        Condición booleana (E040), tipo común de ramas (E070 si incompatibles).

        Permite null como rama hacia tipos de referencia/array (lo resuelve _is_assignable).

    Los códigos exactos y mensajes están centralizados en errors.py y el visitor.

   
5) Cómo correr las pruebas de ejemplo

El repo viene con ejemplos en tests/valid/ y tests/invalid/.
Puedes correr uno a uno:
```bash
# ejemplos
python program/Driver.py tests/valid/ternary/01_ok.cps
python program/Driver.py tests/invalid/switch/02_duplicate_case.cps
```
    

## 🧩 Características del Lenguaje

Compiscript soporta los siguientes conceptos fundamentales:

### ✅ Tipos de Datos

```cps
let a: integer = 10;
let b: string = "hola";
let c: boolean = true;
let d = null;
```

### ✅ Literales

```cps
123          // integer
"texto"      // string
true, false  // boolean
null         // nulo
```

### ✅ Expresiones Aritméticas y Lógicas

```cps
let x = 5 + 3 * 2;
let y = !(x < 10 || x > 20);
```

### ✅ Precedencia y Agrupamiento

```cps
let z = (1 + 2) * 3;
```

### ✅ Declaración y Asignación de Variables

```cps
let nombre: string;
nombre = "Compiscript";
```

### ✅ Constantes (`const`)

```cps
const PI: integer = 314;
```

### ✅ Funciones y Parámetros

```cps
function saludar(nombre: string): string {
  return "Hola " + nombre;
}
```

### ✅ Expresiones de Llamada

```cps
let mensaje = saludar("Mundo");
```

### ✅ Acceso a Propiedades (`.`)

```cps
print(dog.nombre);
```

### ✅ Acceso a Elementos de Arreglo (`[]`)

```cps
let lista = [1, 2, 3];
print(lista[0]);
```

### ✅ Arreglos

```cps
let notas: integer[] = [90, 85, 100];
let matriz: integer[][] = [[1, 2], [3, 4]];
```

### ✅ Funciones como Closures

```cps
function crearContador(): integer {
  function siguiente(): integer {
    return 1;
  }
  return siguiente();
}
```

### ✅ Clases y Constructores

```cps
class Animal {
  let nombre: string;

  function constructor(nombre: string) {
    this.nombre = nombre;
  }

  function hablar(): string {
    return this.nombre + " hace ruido.";
  }
}
```

### ✅ Herencia

```cps
class Perro : Animal {
  function hablar(): string {
    return this.nombre + " ladra.";
  }
}
```

### ✅ `this`

```cps
this.nombre = "Firulais";
```

### ✅ Instanciación con `new`

```cps
let perro: Perro = new Perro("Toby");
```

### ✅ Bloques y Ámbitos

```cps
{
  let x = 42;
  print(x);
}
```

### ✅ Control de Flujo

#### `if` / `else`

```cps
if (x > 10) {
  print("Mayor a 10");
} else {
  print("Menor o igual");
}
```

#### `while`

```cps
while (x < 5) {
  x = x + 1;
}
```

#### `do-while`

```cps
do {
  x = x - 1;
} while (x > 0);
```

#### `for`

```cps
for (let i: integer = 0; i < 3; i = i + 1) {
  print(i);
}
```

#### `foreach`

```cps
foreach (item in lista) {
  print(item);
}
```

#### `break` / `continue`

```cps
foreach (n in notas) {
  if (n < 60) continue;
  if (n == 100) break;
  print(n);
}
```

### ✅ `switch / case`

```cps
switch (x) {
  case 1:
    print("uno");
  case 2:
    print("dos");
  default:
    print("otro");
}
```

### ✅ `try / catch`

```cps
try {
  let peligro = lista[100];
} catch (err) {
  print("Error atrapado: " + err);
}
```

### ✅ `return`

```cps
function suma(a: integer, b: integer): integer {
  return a + b;
}
```

### ✅ Recursión

```cps
function factorial(n: integer): integer {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}
```

---

## 📦 Extensión de Archivo

Todos los archivos fuente de Compiscript deben usar la extensión:

```bash
program.cps
```
