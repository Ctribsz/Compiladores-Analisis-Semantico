"""
Runtime de MIPS - Código Boilerplate
Provee las funciones helper estáticas para MIPS,
como la E/S, alocación de memoria y finalización del programa.
"""

from typing import List, Dict

def get_data_preamble() -> str:
    """
    Retorna la sección .data estática.
    El MIPSGenerator deberá añadir aquí las variables globales dinámicas
    y los literales de string.
    """
    return (
        ".data\n"
        "_newline: .asciiz \"\\n\"   # String para saltos de línea\n"
        "_true:    .asciiz \"true\"   # String para boolean true\n"
        "_false:   .asciiz \"false\"  # String para boolean false\n"
    )

def get_text_preamble() -> str:
    """
    Retorna el preámbulo de la sección .text, incluyendo la
    etiqueta 'main' global.
    """
    return (
        "\n.text\n"
        ".globl main\n"
        "\nmain:\n"
    )

def get_syscall_helpers() -> str:
    """
    Retorna un bloque de string MIPS con todas las funciones
    helper para syscalls (print, alloc, exit).
    """
    return """
# =================================================================
# FUNCIONES HELPER DEL RUNTIME (SYSCALLS)
# =================================================================

# -----------------------------------------------------------------
# _print_int:
# Imprime un entero en $a0, seguido de un newline.
# Args:
#   $a0: El entero a imprimir
# Preserva: $a0, $ra
# -----------------------------------------------------------------
_print_int:
    subu $sp, $sp, 8      # Reservar espacio en stack
    sw $ra, 4($sp)        # Guardar return address
    sw $a0, 0($sp)        # Guardar $a0 (el argumento)

    li $v0, 1             # Syscall 1: print_int
    syscall               # $a0 ya tiene el entero

    jal _print_newline    # Imprimir un salto de línea

    lw $a0, 0($sp)        # Restaurar $a0
    lw $ra, 4($sp)        # Restaurar return address
    addu $sp, $sp, 8      # Liberar stack
    jr $ra                # Retornar

# -----------------------------------------------------------------
# _print_string:
# Imprime un string (null-terminated) desde la dirección en $a0.
# Args:
#   $a0: Dirección del string
# Preserva: $a0, $ra
# -----------------------------------------------------------------
_print_string:
    subu $sp, $sp, 8      # Reservar espacio en stack
    sw $ra, 4($sp)        # Guardar return address
    sw $a0, 0($sp)        # Guardar $a0 (la dirección)

    li $v0, 4             # Syscall 4: print_string
    syscall               # $a0 ya tiene la dirección

    # NOTA: No imprimimos newline aquí, 'print' de Compiscript sí lo hace.
    # Si 'print' debe imprimir newline, la llamada MIPS debe ser:
    #   jal _print_string
    jal _print_newline
    
    lw $a0, 0($sp)        # Restaurar $a0
    lw $ra, 4($sp)        # Restaurar return address
    addu $sp, $sp, 8      # Liberar stack
    jr $ra                # Retornar

# -----------------------------------------------------------------
# _print_boolean:
# Imprime 'true' o 'false' basado en el valor de $a0.
# Args:
#   $a0: El booleano (0 para false, 1 para true)
# Preserva: $a0, $ra
# -----------------------------------------------------------------
_print_boolean:
    subu $sp, $sp, 8      # Reservar espacio
    sw $ra, 4($sp)        # Guardar $ra
    sw $a0, 0($sp)        # Guardar $a0 (argumento)

    bne $a0, $zero, _pb_true # Si $a0 != 0, es true
_pb_false:
    la $a0, _false        # Cargar dirección de "false"
    j _pb_print
_pb_true:
    la $a0, _true         # Cargar dirección de "true"
_pb_print:
    li $v0, 4             # Syscall 4: print_string
    syscall

    jal _print_newline    # Imprimir un salto de línea

    lw $a0, 0($sp)        # Restaurar $a0
    lw $ra, 4($sp)        # Restaurar $ra
    addu $sp, $sp, 8      # Liberar stack
    jr $ra

# -----------------------------------------------------------------
# _string_len:
# Calcula la longitud de un string (sin contar null terminator).
# Args: $a0 = dirección del string
# Ret:  $v0 = longitud
# -----------------------------------------------------------------
_string_len:
    li $v0, 0             # contador = 0
_strlen_loop:
    lb $t0, 0($a0)        # cargar byte
    beq $t0, $zero, _strlen_end
    addi $v0, $v0, 1      # contador++
    addi $a0, $a0, 1      # puntero++
    j _strlen_loop
_strlen_end:
    jr $ra

# -----------------------------------------------------------------
# _string_concat:
# Concatena dos strings.
# Args: $a0 = str1, $a1 = str2
# Ret:  $v0 = puntero al nuevo string (str1 + str2)
# -----------------------------------------------------------------
_string_concat:
    subu $sp, $sp, 16     # Reservar stack
    sw $ra, 12($sp)
    sw $s0, 8($sp)        # Guardar str1
    sw $s1, 4($sp)        # Guardar str2
    sw $s2, 0($sp)        # Guardar longitudes

    move $s0, $a0         # $s0 = str1
    move $s1, $a1         # $s1 = str2

    # 1. Calcular largo total
    move $a0, $s0
    jal _string_len
    move $s2, $v0         # $s2 = len(str1)

    move $a0, $s1
    jal _string_len
    add $s2, $s2, $v0     # $s2 = len(str1) + len(str2)
    addi $s2, $s2, 1      # +1 para null terminator

    # 2. Alocar memoria nueva
    move $a0, $s2
    li $v0, 9             # syscall sbrk
    syscall
    move $t0, $v0         # $t0 = puntero destino (nuevo string)
    move $v1, $v0         # Guardar inicio para retornar en $v0 al final

    # 3. Copiar str1
    move $t1, $s0
_copy_str1:
    lb $t2, 0($t1)
    beq $t2, $zero, _copy_str2_init
    sb $t2, 0($t0)
    addi $t0, $t0, 1
    addi $t1, $t1, 1
    j _copy_str1

_copy_str2_init:
    move $t1, $s1
_copy_str2:
    lb $t2, 0($t1)
    beq $t2, $zero, _concat_done
    sb $t2, 0($t0)
    addi $t0, $t0, 1
    addi $t1, $t1, 1
    j _copy_str2

_concat_done:
    sb $zero, 0($t0)      # Poner null terminator al final

    move $v0, $v1         # Resultado en $v0

    lw $s2, 0($sp)
    lw $s1, 4($sp)
    lw $s0, 8($sp)
    lw $ra, 12($sp)
    addu $sp, $sp, 16
    jr $ra   
    
# -----------------------------------------------------------------
# _int_to_string:
# Convierte un entero ($a0) a un nuevo string en el heap.
# Args: $a0 = entero
# Ret:  $v0 = puntero al string
# -----------------------------------------------------------------
_int_to_string:
    subu $sp, $sp, 32
    sw $ra, 28($sp)
    sw $s0, 24($sp)   # Guardar el número original
    sw $s1, 20($sp)   # Guardar puntero al buffer temporal
    
    move $s0, $a0     # $s0 = n

    # 1. Alocar un buffer temporal pequeño (16 bytes es suficiente para 32-bit int)
    li $a0, 16
    li $v0, 9         # sbrk
    syscall
    move $s1, $v0     # $s1 = inicio del buffer
    move $t0, $s1     # <--- ¡ESTA ES LA LÍNEA CORREGIDA!

    # 2. Manejar caso especial 0
    bne $s0, $zero, _its_check_sign
    li $t1, 48        # ASCII '0'
    sb $t1, 0($t0)
    addi $t0, $t0, 1
    j _its_reverse    # Ir directo a terminar

_its_check_sign:
    # 3. Manejar signo
    li $t3, 0         # $t3 = flag de negativo (0 = false)
    bgez $s0, _its_loop
    li $t3, 1         # Es negativo
    neg $s0, $s0      # Hacerlo positivo para el loop

_its_loop:
    beqz $s0, _its_add_sign
    li $t1, 10
    div $s0, $t1
    mfhi $t2          # $t2 = n % 10 (dígito)
    mflo $s0          # $s0 = n / 10 (resto)
    
    addi $t2, $t2, 48 # Convertir a ASCII
    sb $t2, 0($t0)    # Guardar en buffer
    addi $t0, $t0, 1  # Avanzar cursor
    j _its_loop

_its_add_sign:
    beqz $t3, _its_reverse
    li $t1, 45        # ASCII '-'
    sb $t1, 0($t0)
    addi $t0, $t0, 1

_its_reverse:
    sb $zero, 0($t0)  # Null terminator temporal
    
    # Calcular longitud real
    sub $t4, $t0, $s1 # $t4 = longitud (fin - inicio)
    
    # 4. Alocar memoria FINAL para el string correcto
    move $a0, $t4
    addi $a0, $a0, 1  # +1 para null terminator
    li $v0, 9
    syscall
    move $v1, $v0     # $v1 será el resultado final

    # 5. Copiar invertido (Buffer -> String Final)
    addi $t0, $t0, -1 # Retroceder cursor del buffer (estaba en null)
    move $t5, $v1     # Cursor destino

_its_copy_loop:
    blt $t0, $s1, _its_done
    lb $t6, 0($t0)
    sb $t6, 0($t5)
    addi $t0, $t0, -1
    addi $t5, $t5, 1
    j _its_copy_loop

_its_done:
    sb $zero, 0($t5)  # Null terminator final
    move $v0, $v1     # Resultado en $v0

    lw $s1, 20($sp)
    lw $s0, 24($sp)
    lw $ra, 28($sp)
    addu $sp, $sp, 32
    jr $ra
    

# -----------------------------------------------------------------
# _print_newline:
# Imprime un único caracter de salto de línea.
# Preserva: $a0, $ra
# -----------------------------------------------------------------
_print_newline:
    subu $sp, $sp, 8      # Reservar espacio
    sw $ra, 4($sp)        # Guardar $ra
    sw $a0, 0($sp)        # Guardar $a0 (para preservarlo)

    li $v0, 4
    la $a0, _newline
    syscall

    lw $a0, 0($sp)        # Restaurar $a0
    lw $ra, 4($sp)        # Restaurar $ra
    addu $sp, $sp, 8      # Liberar stack
    jr $ra

# -----------------------------------------------------------------
# _alloc:
# Aloca 'n' bytes en el heap usando 'sbrk'.
# Args:
#   $a0: Número de bytes a alocar
# Returns:
#   $v0: Puntero al inicio del bloque de memoria alocado
# -----------------------------------------------------------------
_alloc:
    li $v0, 9             # Syscall 9: sbrk
    syscall               # $a0 tiene el tamaño, $v0 recibe el puntero
    jr $ra                # Retornar

# -----------------------------------------------------------------
# _exit:
# Termina la ejecución del programa limpiamente.
# -----------------------------------------------------------------
_exit:
    li $v0, 10            # Syscall 10: exit
    syscall
"""