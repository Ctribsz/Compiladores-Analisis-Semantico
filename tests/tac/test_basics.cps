// Test 1: Declaraciones y asignaciones básicas
let x: integer = 10;
let y: integer = 20;
let z: integer = x + y;

// Test 2: Expresiones aritméticas
let a: integer = (x * 2) + (y / 5) - 3;

// Test 3: Expresiones booleanas y comparaciones
let b: boolean = x < y;
let c: boolean = (x == 10) && (y != 0);
let d: boolean = !b || c;

// Test 4: Control de flujo if-else
if (x < y) {
    z = x;
} else {
    z = y;
}

// Test 5: Loops
let i: integer = 0;
while (i < 5) {
    print(i);
    i = i + 1;
}

// Test 6: For loop
for (let j: integer = 0; j < 3; j = j + 1) {
    print(j);
}

// Test 7: Función simple
function add(a: integer, b: integer): integer {
    return a + b;
}

let result: integer = add(5, 3);

// Test 8: Función con control de flujo
function max(x: integer, y: integer): integer {
    if (x > y) {
        return x;
    } else {
        return y;
    }
}

// Test 9: Arrays
let arr: integer[] = [1, 2, 3, 4, 5];
let first: integer = arr[0];
arr[1] = 10;

// Test 10: Operador ternario
let min: integer = (x < y) ? x : y;

// Test 11: Do-while
let counter: integer = 0;
do {
    counter = counter + 1;
} while (counter < 3);

// Test 12: Switch statement
let option: integer = 2;
switch (option) {
    case 1:
        print("One");
    case 2:
        print("Two");
    default:
        print("Other");
}

// Test 13: Clase simple
class Point {
    let x: integer;
    let y: integer;
    
    function constructor(px: integer, py: integer) {
        this.x = px;
        this.y = py;
    }
    
    function getX(): integer {
        return this.x;
    }
}

let p: Point = new Point(10, 20);
let px: integer = p.getX();
p.x = 30;