class A {
  let n: integer;
  function get(): integer { return this.n; }
}

class B : A {
  function set(v: integer) { this.n = v; }
}

let b: B = new B();
b.set(3);
let x: integer = b.get();
