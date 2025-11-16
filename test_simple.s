# === SECCIÓN DE DATOS ===
.data
_newline: .asciiz "\n"   # String para saltos de línea
_true:    .asciiz "true"   # String para boolean true
_false:   .asciiz "false"  # String para boolean false

    # Variables Globales (0x...)
    global_1000: .word 0
    
# Literales de String

# === SECCIÓN DE CÓDIGO ===

.text
.globl main

main:

    # Inicializar frame pointer para main
    move $fp, $sp
    subu $sp, $sp, 200  # Reservar espacio para temporales
    # 0x1000 = 5
    li $t0, 5
    la $at, global_1000
    sw $t0, 0($at)
    # t1 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # print t1
    lw $a0, -4($fp)
    # (Llamando a print para tipo: integer)
    jal _print_int
    
# Terminar programa
    jal _exit

# === HELPERS DEL RUNTIME ===

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
