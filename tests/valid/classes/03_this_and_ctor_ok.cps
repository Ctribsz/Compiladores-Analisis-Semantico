class A {
  let n: integer;

  function constructor(x: integer) {
    this.n = x;
  }

  function get(): integer { return this.n; }
}

let a: A = new A(5);
let y: integer = a.get();
