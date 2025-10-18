# Generación de Código Intermedio TAC

Este compilador genera código intermedio en formato TAC (Three-Address Code) optimizado para Compiscript.

## Ejemplo Completo

### Código Fuente Compiscript

```javascript
// --- Utilidad global ---
function toString(x: integer): string {
  return "";
}

// --- Clase base ---
class Persona {
  var nombre: string;
  var edad: integer;
  var color: string;

  function constructor(nombre: string, edad: integer) {
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
  }

  function saludar(): string {
    return "Hola, mi nombre es " + this.nombre;
  }

  function incrementarEdad(anos: integer): string {
    this.edad = this.edad + anos;
    return "Ahora tengo " + toString(this.edad) + " años.";
  }
}

// --- Clase derivada ---
class Estudiante : Persona {
  var grado: integer;

  function constructor(nombre: string, edad: integer, grado: integer) {
    // No hay 'super': inicializamos campos heredados directamente
    this.nombre = nombre;
    this.edad = edad;
    this.color = "rojo";
    this.grado = grado;
  }

  function estudiar(): string {
    return this.nombre + " está estudiando en " + toString(this.grado) + " grado.";
  }

  function promedioNotas(nota1: integer, nota2: integer, nota3: integer): integer {
    let promedio: integer = (nota1 + nota2 + nota3) / 3; // división entera
    return promedio;
  }
}

// --- Programa principal ---
let log: string = "";

let nombre: string = "Erick";
let juan: Estudiante = new Estudiante(nombre, 20, 3);

// "Imprimir" = concatenar al log con saltos de línea
log = log + juan.saludar() + "\n";
log = log + juan.estudiar() + "\n";
log = log + juan.incrementarEdad(5) + "\n";

// Bucle (uso de while por compatibilidad)
let i: integer = 1;
while (i <= 5) {
  if ((i % 2) == 0) {
    log = log + toString(i) + " es par\n";
  } else {
    log = log + toString(i) + " es impar\n";
  }
  i = i + 1;
}

// Expresión aritmética (entera)
let resultado: integer = (juan.edad * 2) + ((5 - 3) / 2);
log = log + "Resultado de la expresión: " + toString(resultado) + "\n";

// Ejemplo de promedio (entero)
let prom: integer = 0;
prom = juan.promedioNotas(90, 85, 95);
log = log + "Promedio (entero): " + toString(prom) + "\n";

// Nota: 'log' contiene todas las salidas.
```

### Código TAC Generado (Optimizado)

```assembly
function toString:
enter 16
return ""
leave
end_function toString

function constructor:
enter 24
t1 = @FP[-4]
this."nombre" = t1
t1 = @FP[-12]
this."edad" = t1
this."color" = "rojo"
leave
end_function constructor

function saludar:
enter 12
t1 = this."nombre"
t3 = "Hola, mi nombre es " add t1
return t3
leave
end_function saludar

function incrementarEdad:
enter 16
t3 = this."edad"
t1 = @FP[-4]
t2 = t3 add t1
this."edad" = t2
t2 = this."edad"
push t2
call toString, 1
SP = SP + 4
pop t1
t2 = "Ahora tengo " add t1
t1 = t2 add " años."
return t1
leave
end_function incrementarEdad

function constructor:
enter 28
t1 = @FP[-4]
this."nombre" = t1
t1 = @FP[-12]
this."edad" = t1
this."color" = "rojo"
t1 = @FP[-16]
this."grado" = t1
leave
end_function constructor

function estudiar:
enter 12
t1 = this."nombre"
t2 = t1 add " está estudiando en "
t1 = this."grado"
push t1
call toString, 1
SP = SP + 4
pop t3
t1 = t2 add t3
t3 = t1 add " grado."
return t3
leave
end_function estudiar

function promedioNotas:
enter 28
t3 = @FP[-4]
t1 = @FP[-8]
t2 = t3 add t1
t1 = @FP[-12]
t3 = t2 add t1
t1 = t3 div 3
FP[0] = t1
return FP[0]
leave
end_function promedioNotas

; === Código principal ===
0x1000 = ""
t1 = new Estudiante
t3 = @"Erick"
push t3
push 20
push 3
call Estudiante.constructor, 3
0x1008 = t1

t1 = @0x1000
t3 = t1
t2 = t1."saludar"
call t2, 0
pop t2
t3 = t1 add t2
t2 = t3 add "\n"
0x1000 = t2

t3 = @0x1008
t1 = t3."estudiar"
call t1, 0
pop t1
t3 = t2 add t1
t1 = t3 add "\n"
0x1000 = t1

t2 = t3."incrementarEdad"
push 5
call t2, 1
SP = SP + 4
pop t2
t3 = t1 add t2
t2 = t3 add "\n"
0x1000 = t2

0x100c = 1
L0:
t2 = @0x100c
t3 = t2 <= 5
ifFalse t3 goto L1
t2 = @0x100c
t1 = t2 mod 2
t2 = t1 == 0
ifFalse t2 goto L2

t1 = @0x1000
t4 = @0x100c
push t4
call toString, 1
SP = SP + 4
pop t2
t4 = t1 add t2
t2 = t4 add " es par\n"
0x1000 = t2
goto L3

L2:
t2 = @0x1000
t4 = @0x100c
push t4
call toString, 1
SP = SP + 4
pop t1
t4 = t2 add t1
t1 = t4 add " es impar\n"
0x1000 = t1

L3:
t1 = @0x100c
t4 = t1 add 1
0x100c = t4
goto L0

L1:
t3 = @0x1008
t4 = t3."edad"
t1 = t4 add t4            ; Optimización: x*2 → x+x
t4 = t1 add 1
t4 = @0x1000
t2 = t4 add "Resultado de la expresión: "
push t4
call toString, 1
SP = SP + 4
pop t1
t4 = t2 add t1
t1 = t4 add "\n"
0x1000 = t1

t1 = t3
t4 = t3."promedioNotas"
push 95
push 85
push 90
call t4, 3
SP = SP + 12
pop t2

t2 = @0x1000
t3 = t2 add "Promedio (entero): "
push t2
call toString, 1
SP = SP + 4
pop t1
t2 = t3 add t1
t1 = t2 add "\n"
0x1000 = t1
```

## Características del TAC Generado

### ✅ Optimizaciones Aplicadas

1. **Constant Folding**: Expresiones constantes evaluadas en tiempo de compilación
   - `5 - 3` → `2`
   - `2 / 2` → `1`

2. **Strength Reduction**: Operaciones costosas reemplazadas por más eficientes
   - `x * 2` → `x + x` (línea: `t1 = t4 add t4`)

3. **Register Allocation**: Uso eficiente de temporales
   - Solo 4 temporales (`t1-t4`) para todo el programa

4. **Dead Code Elimination**: Código muerto eliminado

5. **Copy Propagation**: Copias innecesarias eliminadas

### 📊 Métricas

- **Temporales utilizados**: 4 (t1, t2, t3, t4)
- **Funciones generadas**: 7 (toString + 6 métodos de clases)
- **Variables globales**: 3 (direcciones 0x1000, 0x1008, 0x100c)
- **Etiquetas**: 4 (L0-L3)

### 🏗️ Estructura del Frame de Activación

Cada función utiliza la siguiente estructura:

```
[ Parámetros ]     ← FP[-n]  (offsets negativos)
[ Return Address ]
[ Old FP ]         ← FP
[ Locals ]         ← FP[0+]  (offsets positivos)
```

Ejemplo en `promedioNotas`:
- `FP[-4]`: nota1
- `FP[-8]`: nota2
- `FP[-12]`: nota3
- `FP[0]`: promedio (variable local)

### 🎯 Convenciones de Llamadas

1. **Argumentos**: Push en orden inverso (derecha a izquierda)
2. **Llamada**: `call function, n_args`
3. **Limpieza**: `SP = SP + (n_args * 4)`
4. **Retorno**: `pop result`