# === SECCIÓN DE DATOS ===
.data
_newline: .asciiz "\n"   # String para saltos de línea
_true:    .asciiz "true"   # String para boolean true
_false:   .asciiz "false"  # String para boolean false

    # Variables Globales (0x...)
    global_1000: .word 0
    global_1004: .word 0
    global_1010: .word 0
    global_1014: .word 0
    global_101c: .word 0
    global_1020: .word 0
    global_1028: .word 0
    global_1034: .word 0
    global_1038: .word 0
    global_103c: .word 0
    
# Literales de String
    _str_0: .asciiz "One"
    _str_1: .asciiz "Two"
    _str_2: .asciiz "Other"
    _str_3: .asciiz "x"
    _str_4: .asciiz "y"
    _str_5: .asciiz "getX"

# === SECCIÓN DE CÓDIGO ===

.text
.globl main

main:

    # 0x1000 = 10
    li $t0, 10
    la $at, global_1000
    sw $t0, 0($at)
    # 0x1004 = 20
    li $t0, 20
    la $at, global_1004
    sw $t0, 0($at)
    # t2 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # t1 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -8($fp)
    # t3 = t2 add t1
    lw $t0, -4($fp)
    lw $t1, -8($fp)
    add $t2, $t0, $t1
    sw $t2, -12($fp)
    # t3 = t2
    lw $t0, -4($fp)
    sw $t0, -12($fp)
    # t1 = t2 add t2
    lw $t0, -4($fp)
    lw $t1, -4($fp)
    add $t2, $t0, $t1
    sw $t2, -8($fp)
    # t3 = t1
    lw $t0, -8($fp)
    sw $t0, -12($fp)
    # t2 = t1 div 5
    lw $t0, -8($fp)
    li $t1, 5
    div $t2, $t0, $t1
    sw $t2, -4($fp)
    # t3 = t1 add t2
    lw $t0, -8($fp)
    lw $t1, -4($fp)
    add $t2, $t0, $t1
    sw $t2, -12($fp)
    # t2 = t3 sub 3
    lw $t0, -12($fp)
    li $t1, 3
    sub $t2, $t0, $t1
    sw $t2, -4($fp)
    # t2 = t3
    lw $t0, -12($fp)
    sw $t0, -4($fp)
    # t1 = t3 < t3
    lw $t0, -12($fp)
    lw $t1, -12($fp)
    slt $t2, $t0, $t1
    sw $t2, -8($fp)
    # 0x1010 = t1
    lw $t0, -8($fp)
    la $at, global_1010
    sw $t0, 0($at)
    # t3 = t2
    lw $t0, -4($fp)
    sw $t0, -12($fp)
    # t2 = t3 == 10
    lw $t0, -12($fp)
    li $t1, 10
    seq $t2, $t0, $t1
    sw $t2, -4($fp)
    # ifFalse t2 goto L0
    lw $t0, -4($fp)
    beq $t0, $zero, L0
    # t2 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # t3 = t2 != 0
    lw $t0, -4($fp)
    li $t1, 0
    sne $t2, $t0, $t1
    sw $t2, -12($fp)
    # t1 = t3
    lw $t0, -12($fp)
    sw $t0, -8($fp)
    # goto L1
    j L1
    # L0:
L0:
    # t1 = false
    li $t0, 0
    sw $t0, -8($fp)
    # L1:
L1:
    # 0x1014 = t1
    lw $t0, -8($fp)
    la $at, global_1014
    sw $t0, 0($at)
    # t3 = @0x1010
    la $t0, global_1010
    lw $t1, 0($t0)
    sw $t1, -12($fp)
    # t2 = !t3
    lw $t0, -12($fp)
    seq $t0, $t0, $zero
    sw $t0, -4($fp)
    # if t2 goto L2
    lw $t0, -4($fp)
    bne $t0, $zero, L2
    # t2 = @0x1014
    la $t0, global_1014
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # t1 = t2
    lw $t0, -4($fp)
    sw $t0, -8($fp)
    # goto L3
    j L3
    # L2:
L2:
    # t1 = true
    li $t0, 1
    sw $t0, -8($fp)
    # L3:
L3:
    # t1 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -8($fp)
    # t2 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # t3 = t1 < t2
    lw $t0, -8($fp)
    lw $t1, -4($fp)
    slt $t2, $t0, $t1
    sw $t2, -12($fp)
    # ifFalse t3 goto L4
    lw $t0, -12($fp)
    beq $t0, $zero, L4
    # t2 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # goto L5
    j L5
    # L4:
L4:
    # t2 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # L5:
L5:
    # 0x101c = 0
    li $t0, 0
    la $at, global_101c
    sw $t0, 0($at)
    # L6:
L6:
    # t2 = @0x101c
    la $t0, global_101c
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # t1 = t2 < 5
    lw $t0, -4($fp)
    li $t1, 5
    slt $t2, $t0, $t1
    sw $t2, -8($fp)
    # ifFalse t1 goto L7
    lw $t0, -8($fp)
    beq $t0, $zero, L7
    # t2 = @0x101c
    la $t0, global_101c
    lw $t1, 0($t0)
    sw $t1, -4($fp)
    # print t2
    lw $a0, -4($fp)
    # (Llamando a print para tipo: None)
    jal _print_int
    # t3 = t2 add 1
    lw $t0, -4($fp)
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, -12($fp)
    # 0x101c = t3
    lw $t0, -12($fp)
    la $at, global_101c
    sw $t0, 0($at)
    # goto L6
    j L6
    # L7:
L7:
    # 0x1020 = 0
    li $t0, 0
    la $at, global_1020
    sw $t0, 0($at)
    # L8:
L8:
    # t1 = @0x1020
    la $t0, global_1020
    lw $t1, 0($t0)
    sw $t1, -8($fp)
    # t3 = t1 < 3
    lw $t0, -8($fp)
    li $t1, 3
    slt $t2, $t0, $t1
    sw $t2, -12($fp)
    # ifFalse t3 goto L10
    lw $t0, -12($fp)
    beq $t0, $zero, L10
    # t1 = @0x1020
    la $t0, global_1020
    lw $t1, 0($t0)
    sw $t1, -8($fp)
    # print t1
    lw $a0, -8($fp)
    # (Llamando a print para tipo: None)
    jal _print_int
    # t1 = @0x1020
    la $t0, global_1020
    lw $t1, 0($t0)
    sw $t1, -8($fp)
    # t2 = t1 add 1
    lw $t0, -8($fp)
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, -4($fp)
    # goto L8
    j L8
    # L10:
L10:
    # function add:
add:
    # enter 20
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 20
    # t3 = @FP[-4]
    addi $t0, $fp, -4
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t2 = @FP[-8]
    addi $t0, $fp, -8
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t1 = t3 add t2
    lw $t0, -24($fp)
    lw $t1, -28($fp)
    add $t2, $t0, $t1
    sw $t2, -32($fp)
    # return t1
    lw $v0, -32($fp)
    jr $ra
    # leave
    addu $sp, $sp, 20
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    # end_function add
    # push 3
    li $t0, 3
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 5
    li $t0, 5
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # call add, 2
    jal add
    # SP = SP + 8
    addu $sp, $sp, 8
    # pop t1
    lw $t0, 0($sp)
    addu $sp, $sp, 4
    sw $t0, -32($fp)
    # function max:
max:
    # enter 20
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 20
    # t1 = @FP[-4]
    addi $t0, $fp, -4
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t2 = @FP[-8]
    addi $t0, $fp, -8
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t3 = t1 > t2
    lw $t0, -24($fp)
    lw $t1, -28($fp)
    sgt $t2, $t0, $t1
    sw $t2, -32($fp)
    # ifFalse t3 goto L11
    lw $t0, -32($fp)
    beq $t0, $zero, L11
    # t2 = @FP[-4]
    addi $t0, $fp, -4
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # return t2
    lw $v0, -28($fp)
    jr $ra
    # goto L12
    j L12
    # L11:
L11:
    # t2 = @FP[-8]
    addi $t0, $fp, -8
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # return t2
    lw $v0, -28($fp)
    jr $ra
    # L12:
L12:
    # leave
    addu $sp, $sp, 20
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    # end_function max
    # t2 = new 5
    # Alocando 20 bytes para array[5]
    li $a0, 20
    jal _alloc
    sw $v0, -28($fp)
    # t2[0] = 1
    lw $t0, -28($fp)
    li $t1, 0
    li $t2, 1
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # t2[1] = 2
    lw $t0, -28($fp)
    li $t1, 1
    li $t2, 2
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # t2[2] = 3
    lw $t0, -28($fp)
    li $t1, 2
    li $t2, 3
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # t2[3] = 4
    lw $t0, -28($fp)
    li $t1, 3
    li $t2, 4
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # t2[4] = 5
    lw $t0, -28($fp)
    li $t1, 4
    li $t2, 5
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # 0x1028 = t2
    lw $t0, -28($fp)
    la $at, global_1028
    sw $t0, 0($at)
    # t1 = t2[0]
    lw $t0, -28($fp)
    li $t1, 0
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    lw $t2, 0($t0)
    sw $t2, -24($fp)
    # t1 = @0x1028
    la $t0, global_1028
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t1[1] = 10
    lw $t0, -24($fp)
    li $t1, 1
    li $t2, 10
    sll $t1, $t1, 2
    add $t0, $t0, $t1
    sw $t2, 0($t0)
    # t1 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t4 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -36($fp)
    # t3 = t1 < t4
    lw $t0, -24($fp)
    lw $t1, -36($fp)
    slt $t2, $t0, $t1
    sw $t2, -32($fp)
    # ifFalse t3 goto L13
    lw $t0, -32($fp)
    beq $t0, $zero, L13
    # t1 = @0x1000
    la $t0, global_1000
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t4 = t1
    lw $t0, -24($fp)
    sw $t0, -36($fp)
    # goto L14
    j L14
    # L13:
L13:
    # t2 = @0x1004
    la $t0, global_1004
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t4 = t2
    lw $t0, -28($fp)
    sw $t0, -36($fp)
    # L14:
L14:
    # 0x1034 = 0
    li $t0, 0
    la $at, global_1034
    sw $t0, 0($at)
    # L15:
L15:
    # t4 = @0x1034
    la $t0, global_1034
    lw $t1, 0($t0)
    sw $t1, -36($fp)
    # t2 = t4 add 1
    lw $t0, -36($fp)
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, -28($fp)
    # 0x1034 = t2
    lw $t0, -28($fp)
    la $at, global_1034
    sw $t0, 0($at)
    # t2 = @0x1034
    la $t0, global_1034
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t4 = t2 < 3
    lw $t0, -28($fp)
    li $t1, 3
    slt $t2, $t0, $t1
    sw $t2, -36($fp)
    # if t4 goto L15
    lw $t0, -36($fp)
    bne $t0, $zero, L15
    # 0x1038 = 2
    li $t0, 2
    la $at, global_1038
    sw $t0, 0($at)
    # t4 = @0x1038
    la $t0, global_1038
    lw $t1, 0($t0)
    sw $t1, -36($fp)
    # t2 = t4 == 1
    lw $t0, -36($fp)
    li $t1, 1
    seq $t2, $t0, $t1
    sw $t2, -28($fp)
    # if t2 goto L19
    lw $t0, -28($fp)
    bne $t0, $zero, L19
    # t2 = t4 == 2
    lw $t0, -36($fp)
    li $t1, 2
    seq $t2, $t0, $t1
    sw $t2, -28($fp)
    # if t2 goto L20
    lw $t0, -28($fp)
    bne $t0, $zero, L20
    # goto L21
    j L21
    # L19:
L19:
    # print "One"
    la $a0, _str_0
    # (Llamando a print para tipo: string)
    jal _print_string
    # L20:
L20:
    # print "Two"
    la $a0, _str_1
    # (Llamando a print para tipo: string)
    jal _print_string
    # L21:
L21:
    # print "Other"
    la $a0, _str_2
    # (Llamando a print para tipo: string)
    jal _print_string
    # function constructor:
constructor:
    # enter 20
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 20
    # t2 = @FP[-4]
    addi $t0, $fp, -4
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # this."x" = t2
    # (Asignando a campo 'x' en offset 0)
    lw $t0, -28($fp)
    lw $t1, -24($fp)
    sw $t1, 0($t0)
    # t2 = @FP[-8]
    addi $t0, $fp, -8
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # this."y" = t2
    # (Asignando a campo 'y' en offset 4)
    lw $t0, -28($fp)
    lw $t1, -24($fp)
    sw $t1, 4($t0)
    # leave
    addu $sp, $sp, 20
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    # end_function constructor
    # function getX:
getX:
    # enter 12
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 12
    # t2 = this."x"
    # (Accediendo a campo 'x' en offset 0)
    lw $t0, -16($fp)
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # return t2
    lw $v0, -20($fp)
    jr $ra
    # leave
    addu $sp, $sp, 12
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    # end_function getX
    # t2 = new Point
    # Alocando 8 bytes para Point
    li $a0, 8
    jal _alloc
    sw $v0, -20($fp)
    # push 10
    li $t0, 10
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 20
    li $t0, 20
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # call Point.constructor, 2
    jal Point_constructor
    # 0x103c = t2
    lw $t0, -20($fp)
    la $at, global_103c
    sw $t0, 0($at)
    # t1 = t2."getX"
    # (Resolviendo dirección de método getX)
    la $t0, getX
    sw $t0, -24($fp)
    # call t1, 0
    lw $t0, -24($fp)
    jalr $t0
    # pop t3
    lw $t0, 0($sp)
    addu $sp, $sp, 4
    sw $t0, -28($fp)
    # t3 = @0x103c
    la $t0, global_103c
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t3."x" = 30
    # (Asignando a campo 'x' en offset 0)
    lw $t0, -28($fp)
    li $t1, 30
    sw $t1, 0($t0)

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
