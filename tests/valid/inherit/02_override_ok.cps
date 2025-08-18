class A {
  function f(a: integer): integer { return a; }
}

class B : A {
  function f(a: integer): integer { return a + 1; }  // misma firma
}
