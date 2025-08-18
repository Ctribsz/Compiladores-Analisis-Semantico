class A {
  let n: integer;
  function get(): integer { return 1; }
}

let a: A = new A();
let x: integer = a.n;
let y: integer = a.get();
