// Bloque lineal (sin saltos) para disparar folding + propagación local
let x: integer = 2 + 3;          // -> x = 5
let y: integer = x * 4;          // -> y = 20
let z: integer = y - (1 + 1);    // -> z = 18

// Condición que queda constante (true): (5 == 5) && (20 != 0)
// El optimizador debería plegar el IF a solo la rama 'then' y
// remover el GOTO/label redundantes.
if ( (x == 5) && (y != 0) ) {
  print("then");
} else {
  print("else");
}

// Algebraic simplification (no requiere propagación inter-bloque)
let a: integer = 10;
let b: integer = a + 0;          // -> b = a
let c: integer = b * 1;          // -> c = b
let d: integer = c - 0;          // -> d = c
