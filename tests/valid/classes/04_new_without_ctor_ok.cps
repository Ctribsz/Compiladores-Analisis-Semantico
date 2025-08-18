class B {
  let s: string;
  function set(v: string): void { }  // si no tienes 'void', omite el tipo
}
let b: B = new B();   // sin constructor declarado → 0 args permitido
