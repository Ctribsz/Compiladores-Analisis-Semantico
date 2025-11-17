function toString(x: integer): string { return ""; }

class Estudiante {
  let nombre: string;
  let edad: integer;
  let grado: integer;
  
  function constructor(nombre: string, edad: integer, grado: integer) {
    this.nombre = nombre;
    this.edad = edad;
    this.grado = grado;
  }
  
  function saludar(): string {
    return "Hola, soy " + this.nombre;
  }
}

let e: Estudiante = new Estudiante("Diego", 15, 4);
print(e.saludar());