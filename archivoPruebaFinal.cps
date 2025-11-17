// Helpers "declarados" en el lenguaje; la implementación real la hace el backend MIPS.
function toString(x: integer): string {
  return "";
}

function printInteger(x: integer): integer { return x; }
function printString(x: string): string { return x; }

// Recursividad: Fibonacci
function fibonacci(n: integer): integer {
  if (n <= 1) {
    return n;
  }
  let a: integer = fibonacci(n - 1);
  let b: integer = fibonacci(n - 2);
  let r: integer = a + b;
  return r;
}

// Clase base
class Persona {
  let nombre: string;
  let edad: integer;
  let color: string;

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

// Clase derivada
class Estudiante : Persona {
  let grado: integer;

    function constructor(nombre: string, edad: integer, grado: integer) {
        this.edad = edad;         // Asigna edad (int) a offset 4
        this.nombre = nombre;     // Asigna nombre (string) a offset 0
        this.color = "rojo";      // Asigna "rojo" (string) a offset 8
        this.grado = grado;       // Asigna grado (int) a offset 12
    }

  function estudiar(): string {
    return this.nombre + " está estudiando en " + toString(this.grado) + " año en la Universidad del Valle de Guatemala (UVG).";
  }

  function promedioNotas(n1: integer, n2: integer, n3: integer, n4: integer, n5: integer, n6: integer): integer {
    let promedio: integer = (n1 + n2 + n3 + n4 + n5 + n6) / 6; // división entera
    return promedio;
  }
}

// Programa principal
let log: string = "";

let nombre: string = "Diego Linares";
let nombre_estudiante1: Estudiante = new Estudiante(nombre, 15, 4);

let nombre1: string = "Diego Linares";
let nombre_estudiante2: Estudiante = new Estudiante(nombre1, 15, 4);

let nombre2: string = "Diego Linares";
let nombre_estudiante3: Estudiante = new Estudiante(nombre2, 15, 4);

// Cabecera y acciones básicas
log = log + nombre_estudiante1.saludar() + "\n";
log = log + nombre_estudiante1.estudiar() + "\n";
log = log + nombre_estudiante1.incrementarEdad(6) + "\n";

log = log + nombre_estudiante2.saludar() + "\n";
log = log + nombre_estudiante2.estudiar() + "\n";
log = log + nombre_estudiante2.incrementarEdad(7) + "\n";

log = log + nombre_estudiante3.saludar() + "\n";
log = log + nombre_estudiante3.estudiar() + "\n";
log = log + nombre_estudiante3.incrementarEdad(6) + "\n";

// Bucle (solo a log, sin imprimir en caliente)
let i: integer = 1;
while (i <= 12) {
  if ((i % 2) == 0) {
    log = log + toString(i) + " es par\n";
  } else {
    log = log + toString(i) + " es impar\n";
  }
  i = i + 1;
}

// Expresión aritmética (entera)
// Corregido: 'sergio.edad' reemplazado por una variable declarada
let resultado: integer = (nombre_estudiante1.edad * 2) + ((5 - 3) / 2);
log = log + "Resultado de la expresión: " + toString(resultado) + "\n";

// Promedio (entero)
let prom: integer = 0;
prom = nombre_estudiante1.promedioNotas(99, 95, 98, 100, 95, 94);
log = log + "Promedio (entero): " + toString(prom) + "\n";

// Prueba: Fibonacci recursivo
log = log + "Prueba: Fibonacci recursivo\n";
let nFib: integer = 20;
let k: integer = 0;
while (k <= nFib) {
  let fk: integer = fibonacci(k);
  log = log + "Fib(" + toString(k) + ") = " + toString(fk) + "\n";
  k = k + 1;
}

print(log);