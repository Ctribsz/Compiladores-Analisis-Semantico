// Declaración necesaria para que el semántico no se queje
function toString(n: integer): string {
    return ""; 
}

function main() {
    let n: integer = 12345;
    let s: string = "Numero: " + toString(n);
    print(s);
    
    let neg: integer = -50;
    print("Negativo: " + toString(neg));
    
    print("Cero: " + toString(0));
}

main();