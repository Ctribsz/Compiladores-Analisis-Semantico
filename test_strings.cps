// Prueba simple de strings y concatenación

function main() {
    let a: string = "Hola ";
    let b: string = "Mundo";
    let c: string = a + b;
    
    print(c); // Debería imprimir "Hola Mundo"
    
    // Prueba de toString (si logramos implementarlo)
    let num: integer = 42;
    // print("El numero es: " + num); // Esto requiere toString implícito o explícito
}

main();