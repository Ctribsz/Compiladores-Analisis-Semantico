class A { function ping(): integer { return 1; } }
let a: A = new A();
let z = a.ping(1);   // aridad inválida E021
