# === SECCIÓN DE DATOS ===
.data
_newline: .asciiz "\n"   # String para saltos de línea
_true:    .asciiz "true"   # String para boolean true
_false:   .asciiz "false"  # String para boolean false

    # Variables Globales (0x...)
    
# Literales de String
    _str_0: .asciiz ""
    _str_1: .asciiz "rojo"
    _str_2: .asciiz "Hola, mi nombre es "
    _str_3: .asciiz "Ahora tengo "
    _str_4: .asciiz " años."
    _str_5: .asciiz " está estudiando en "
    _str_6: .asciiz " año en la Universidad del Valle de Guatemala (UVG)."
    _str_7: .asciiz "Diego Linares"
    _str_8: .asciiz "saludar"
    _str_9: .asciiz "\n"
    _str_10: .asciiz "estudiar"
    _str_11: .asciiz "incrementarEdad"
    _str_12: .asciiz " es par\n"
    _str_13: .asciiz " es impar\n"
    _str_14: .asciiz "Resultado de la expresión: "
    _str_15: .asciiz "promedioNotas"
    _str_16: .asciiz "Promedio (entero): "
    _str_17: .asciiz "Prueba: Fibonacci recursivo\n"
    _str_18: .asciiz "Fib("
    _str_19: .asciiz ") = "

# === SECCIÓN DE CÓDIGO ===

.text
.globl main

main:

    # Inicializar frame pointer y saltar a script principal
    move $fp, $sp
        # (Reservando 52 bytes para locales de main)
    subu $sp, $sp, 356
    j _script_start          # Saltar sobre definiciones de funciones

    # function toString:
toString:
    # enter 16
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 16
    # return ""
    la $v0, _str_0
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function toString

    # function printInteger:
printInteger:
    # enter 16
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 16
    # t1 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # return t1
    lw $v0, -20($fp)
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function printInteger

    # function printString:
printString:
    # enter 16
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 16
    # t2 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # return t2
    lw $v0, -20($fp)
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function printString

    # function fibonacci:
fibonacci:
    # enter 28
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 28
    # t3 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -32($fp)
    # t4 = t3 <= 1
    lw $t0, -32($fp)
    li $t1, 1
    sle $t2, $t0, $t1
    sw $t2, -36($fp)
    # ifFalse t4 goto L1
    lw $t0, -36($fp)
    beq $t0, $zero, L1
    # t5 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -40($fp)
    # return t5
    lw $v0, -40($fp)
    addu $sp, $sp, 28
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # L1:
L1:
    # t6 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -44($fp)
    # t7 = t6 sub 1
    lw $t0, -44($fp)
    li $t1, 1
    sub $t2, $t0, $t1
    sw $t2, -48($fp)
    # push t7
    lw $t0, -48($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t8 = call fibonacci, 1
    jal fibonacci
    sw $v0, -52($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # FP[-4] = t8
    lw $t0, -52($fp)
    sw $t0, -4($fp)
    # t9 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -56($fp)
    # t10 = t9 sub 2
    lw $t0, -56($fp)
    li $t1, 2
    sub $t2, $t0, $t1
    sw $t2, -60($fp)
    # push t10
    lw $t0, -60($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t11 = call fibonacci, 1
    jal fibonacci
    sw $v0, -64($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # FP[-8] = t11
    lw $t0, -64($fp)
    sw $t0, -8($fp)
    # t12 = FP[-4] add FP[-8]
    lw $t0, -4($fp)
    lw $t1, -8($fp)
    add $t2, $t0, $t1
    sw $t2, -68($fp)
    # FP[-12] = t12
    lw $t0, -68($fp)
    sw $t0, -12($fp)
    # return FP[-12]
    lw $v0, -12($fp)
    addu $sp, $sp, 28
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 28
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function fibonacci

    # function Persona.constructor:
Persona_constructor:
    # enter 20
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 20
    # t13 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t14 = @FP[12]
    addi $t0, $fp, 12
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t13.0 = t14
    # (Asignando a campo en offset 0)
    lw $t0, -24($fp)
    lw $t1, -28($fp)
    sw $t1, 0($t0)
    # t15 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -32($fp)
    # t16 = @FP[16]
    addi $t0, $fp, 16
    lw $t1, 0($t0)
    sw $t1, -36($fp)
    # t15.4 = t16
    # (Asignando a campo en offset 4)
    lw $t0, -32($fp)
    lw $t1, -36($fp)
    sw $t1, 4($t0)
    # t17 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -40($fp)
    # t17.8 = "rojo"
    # (Asignando a campo en offset 8)
    lw $t0, -40($fp)
    la $t1, _str_1
    sw $t1, 8($t0)
    # leave
    addu $sp, $sp, 20
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Persona.constructor

    # function Persona.saludar:
Persona_saludar:
    # enter 12
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 12
    # t18 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -16($fp)
    # t19 = t18.0
    lw $t0, -16($fp)
    # (Accediendo a campo en offset 0)
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # t20 = "Hola, mi nombre es " add t19
    # Concatenación de strings detectada
    la $a0, _str_2
    lw $a1, -20($fp)
    jal _string_concat
    sw $v0, -24($fp)
    # return t20
    lw $v0, -24($fp)
    addu $sp, $sp, 12
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 12
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Persona.saludar

    # function Persona.incrementarEdad:
Persona_incrementarEdad:
    # enter 16
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 16
    # t21 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # t22 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -24($fp)
    # t23 = t22.4
    lw $t0, -24($fp)
    # (Accediendo a campo en offset 4)
    lw $t1, 4($t0)
    sw $t1, -28($fp)
    # t24 = @FP[12]
    addi $t0, $fp, 12
    lw $t1, 0($t0)
    sw $t1, -32($fp)
    # t25 = t23 add t24
    lw $t0, -28($fp)
    lw $t1, -32($fp)
    add $t2, $t0, $t1
    sw $t2, -36($fp)
    # t21.4 = t25
    # (Asignando a campo en offset 4)
    lw $t0, -20($fp)
    lw $t1, -36($fp)
    sw $t1, 4($t0)
    # t26 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -40($fp)
    # t27 = t26.4
    lw $t0, -40($fp)
    # (Accediendo a campo en offset 4)
    lw $t1, 4($t0)
    sw $t1, -44($fp)
    # push t27
    lw $t0, -44($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t28 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -48($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t29 = "Ahora tengo " add t28
    # Concatenación de strings detectada
    la $a0, _str_3
    lw $a1, -48($fp)
    jal _string_concat
    sw $v0, -52($fp)
    # t30 = t29 add " años."
    # Concatenación de strings detectada
    lw $a0, -52($fp)
    la $a1, _str_4
    jal _string_concat
    sw $v0, -56($fp)
    # return t30
    lw $v0, -56($fp)
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 16
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Persona.incrementarEdad

    # function Estudiante.constructor:
Estudiante_constructor:
    # enter 24
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 24
    # t31 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t32 = @FP[16]
    addi $t0, $fp, 16
    lw $t1, 0($t0)
    sw $t1, -32($fp)
    # t31.4 = t32
    # (Asignando a campo en offset 4)
    lw $t0, -28($fp)
    lw $t1, -32($fp)
    sw $t1, 4($t0)
    # t33 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -36($fp)
    # t34 = @FP[12]
    addi $t0, $fp, 12
    lw $t1, 0($t0)
    sw $t1, -40($fp)
    # t33.0 = t34
    # (Asignando a campo en offset 0)
    lw $t0, -36($fp)
    lw $t1, -40($fp)
    sw $t1, 0($t0)
    # t35 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -44($fp)
    # t35.8 = "rojo"
    # (Asignando a campo en offset 8)
    lw $t0, -44($fp)
    la $t1, _str_1
    sw $t1, 8($t0)
    # t36 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -48($fp)
    # t37 = @FP[20]
    addi $t0, $fp, 20
    lw $t1, 0($t0)
    sw $t1, -52($fp)
    # t36.12 = t37
    # (Asignando a campo en offset 12)
    lw $t0, -48($fp)
    lw $t1, -52($fp)
    sw $t1, 12($t0)
    # leave
    addu $sp, $sp, 24
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Estudiante.constructor

    # function Estudiante.estudiar:
Estudiante_estudiar:
    # enter 12
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 12
    # t38 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -16($fp)
    # t39 = t38.0
    lw $t0, -16($fp)
    # (Accediendo a campo en offset 0)
    lw $t1, 0($t0)
    sw $t1, -20($fp)
    # t40 = t39 add " está estudiando en "
    # Concatenación de strings detectada
    lw $a0, -20($fp)
    la $a1, _str_5
    jal _string_concat
    sw $v0, -24($fp)
    # t41 = @FP[8]
    addi $t0, $fp, 8
    lw $t1, 0($t0)
    sw $t1, -28($fp)
    # t42 = t41.12
    lw $t0, -28($fp)
    # (Accediendo a campo en offset 12)
    lw $t1, 12($t0)
    sw $t1, -32($fp)
    # push t42
    lw $t0, -32($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t43 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -36($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t44 = t40 add t43
    # Concatenación de strings detectada
    lw $a0, -24($fp)
    lw $a1, -36($fp)
    jal _string_concat
    sw $v0, -40($fp)
    # t45 = t44 add " año en la Universidad del Valle de Guatemala (UVG)."
    # Concatenación de strings detectada
    lw $a0, -40($fp)
    la $a1, _str_6
    jal _string_concat
    sw $v0, -44($fp)
    # return t45
    lw $v0, -44($fp)
    addu $sp, $sp, 12
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 12
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Estudiante.estudiar

    # function Estudiante.promedioNotas:
Estudiante_promedioNotas:
    # enter 40
    subu $sp, $sp, 8
    sw $ra, 4($sp)
    sw $fp, 0($sp)
    move $fp, $sp
    subu $sp, $sp, 40
    # t46 = @FP[12]
    addi $t0, $fp, 12
    lw $t1, 0($t0)
    sw $t1, -44($fp)
    # t47 = @FP[16]
    addi $t0, $fp, 16
    lw $t1, 0($t0)
    sw $t1, -48($fp)
    # t48 = t46 add t47
    lw $t0, -44($fp)
    lw $t1, -48($fp)
    add $t2, $t0, $t1
    sw $t2, -52($fp)
    # t49 = @FP[20]
    addi $t0, $fp, 20
    lw $t1, 0($t0)
    sw $t1, -56($fp)
    # t50 = t48 add t49
    lw $t0, -52($fp)
    lw $t1, -56($fp)
    add $t2, $t0, $t1
    sw $t2, -60($fp)
    # t51 = @FP[24]
    addi $t0, $fp, 24
    lw $t1, 0($t0)
    sw $t1, -64($fp)
    # t52 = t50 add t51
    lw $t0, -60($fp)
    lw $t1, -64($fp)
    add $t2, $t0, $t1
    sw $t2, -68($fp)
    # t53 = @FP[28]
    addi $t0, $fp, 28
    lw $t1, 0($t0)
    sw $t1, -72($fp)
    # t54 = t52 add t53
    lw $t0, -68($fp)
    lw $t1, -72($fp)
    add $t2, $t0, $t1
    sw $t2, -76($fp)
    # t55 = @FP[32]
    addi $t0, $fp, 32
    lw $t1, 0($t0)
    sw $t1, -80($fp)
    # t56 = t54 add t55
    lw $t0, -76($fp)
    lw $t1, -80($fp)
    add $t2, $t0, $t1
    sw $t2, -84($fp)
    # t57 = t56 div 6
    lw $t0, -84($fp)
    li $t1, 6
    div $t2, $t0, $t1
    sw $t2, -88($fp)
    # FP[-4] = t57
    lw $t0, -88($fp)
    sw $t0, -4($fp)
    # return FP[-4]
    lw $v0, -4($fp)
    addu $sp, $sp, 40
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # leave
    addu $sp, $sp, 40
    lw $ra, 4($sp)
    lw $fp, 0($sp)
    addu $sp, $sp, 8
    jr $ra
    # end_function Estudiante.promedioNotas

_script_start:
        # Reseteando estado de frame para main
    # FP[-4] = ""
    la $t0, _str_0
    sw $t0, -4($fp)
    # FP[-8] = "Diego Linares"
    la $t0, _str_7
    sw $t0, -8($fp)
    # t57 = new Estudiante
    # Alocando 64 bytes (hack) para Estudiante
    li $a0, 64
    jal _alloc
    sw $v0, -56($fp)
    # push 4
    li $t0, 4
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 15
    li $t0, 15
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-8]
    lw $t0, -8($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push t57
    lw $t0, -56($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # call Estudiante.constructor, 4
    jal Estudiante_constructor
    # SP = SP + 16
    addu $sp, $sp, 16
    # FP[-12] = t57
    lw $t0, -56($fp)
    sw $t0, -12($fp)
    # FP[-16] = "Diego Linares"
    la $t0, _str_7
    sw $t0, -16($fp)
    # t57 = new Estudiante
    # Alocando 64 bytes (hack) para Estudiante
    li $a0, 64
    jal _alloc
    sw $v0, -56($fp)
    # push 4
    li $t0, 4
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 15
    li $t0, 15
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-16]
    lw $t0, -16($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push t57
    lw $t0, -56($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # call Estudiante.constructor, 4
    jal Estudiante_constructor
    # SP = SP + 16
    addu $sp, $sp, 16
    # FP[-20] = t57
    lw $t0, -56($fp)
    sw $t0, -20($fp)
    # FP[-24] = "Diego Linares"
    la $t0, _str_7
    sw $t0, -24($fp)
    # t57 = new Estudiante
    # Alocando 64 bytes (hack) para Estudiante
    li $a0, 64
    jal _alloc
    sw $v0, -56($fp)
    # push 4
    li $t0, 4
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 15
    li $t0, 15
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-24]
    lw $t0, -24($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push t57
    lw $t0, -56($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # call Estudiante.constructor, 4
    jal Estudiante_constructor
    # SP = SP + 16
    addu $sp, $sp, 16
    # FP[-28] = t57
    lw $t0, -56($fp)
    sw $t0, -28($fp)
    # t57 = FP[-12]."saludar"
    lw $t0, -12($fp)
    # (Resolviendo dirección de método Persona_saludar)
    la $t0, Persona_saludar
    sw $t0, -56($fp)
    # push FP[-12]
    lw $t0, -12($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t58 = call t57, 1
    # Llamada indirecta a puntero en temporal 't57'
    lw $t0, -56($fp)
    jalr $t0
    sw $v0, -60($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t59 = FP[-4] add t58
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -60($fp)
    jal _string_concat
    sw $v0, -64($fp)
    # t60 = t59 add "\n"
    # Concatenación de strings detectada
    lw $a0, -64($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -68($fp)
    # FP[-4] = t60
    lw $t0, -68($fp)
    sw $t0, -4($fp)
    # t61 = FP[-12]."estudiar"
    lw $t0, -12($fp)
    # (Resolviendo dirección de método Estudiante_estudiar)
    la $t0, Estudiante_estudiar
    sw $t0, -72($fp)
    # push FP[-12]
    lw $t0, -12($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t62 = call t61, 1
    # Llamada indirecta a puntero en temporal 't61'
    lw $t0, -72($fp)
    jalr $t0
    sw $v0, -76($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t63 = FP[-4] add t62
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -76($fp)
    jal _string_concat
    sw $v0, -80($fp)
    # t64 = t63 add "\n"
    # Concatenación de strings detectada
    lw $a0, -80($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -84($fp)
    # FP[-4] = t64
    lw $t0, -84($fp)
    sw $t0, -4($fp)
    # t65 = FP[-12]."incrementarEdad"
    lw $t0, -12($fp)
    # (Resolviendo dirección de método Persona_incrementarEdad)
    la $t0, Persona_incrementarEdad
    sw $t0, -88($fp)
    # push 6
    li $t0, 6
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-12]
    lw $t0, -12($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t66 = call t65, 2
    # Llamada indirecta a puntero en temporal 't65'
    lw $t0, -88($fp)
    jalr $t0
    sw $v0, -92($fp)
    # SP = SP + 8
    addu $sp, $sp, 8
    # t67 = FP[-4] add t66
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -92($fp)
    jal _string_concat
    sw $v0, -96($fp)
    # t68 = t67 add "\n"
    # Concatenación de strings detectada
    lw $a0, -96($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -100($fp)
    # FP[-4] = t68
    lw $t0, -100($fp)
    sw $t0, -4($fp)
    # t69 = FP[-20]."saludar"
    lw $t0, -20($fp)
    # (Resolviendo dirección de método Persona_saludar)
    la $t0, Persona_saludar
    sw $t0, -104($fp)
    # push FP[-20]
    lw $t0, -20($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t70 = call t69, 1
    # Llamada indirecta a puntero en temporal 't69'
    lw $t0, -104($fp)
    jalr $t0
    sw $v0, -108($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t71 = FP[-4] add t70
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -108($fp)
    jal _string_concat
    sw $v0, -112($fp)
    # t72 = t71 add "\n"
    # Concatenación de strings detectada
    lw $a0, -112($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -116($fp)
    # FP[-4] = t72
    lw $t0, -116($fp)
    sw $t0, -4($fp)
    # t73 = FP[-20]."estudiar"
    lw $t0, -20($fp)
    # (Resolviendo dirección de método Estudiante_estudiar)
    la $t0, Estudiante_estudiar
    sw $t0, -120($fp)
    # push FP[-20]
    lw $t0, -20($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t74 = call t73, 1
    # Llamada indirecta a puntero en temporal 't73'
    lw $t0, -120($fp)
    jalr $t0
    sw $v0, -124($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t75 = FP[-4] add t74
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -124($fp)
    jal _string_concat
    sw $v0, -128($fp)
    # t76 = t75 add "\n"
    # Concatenación de strings detectada
    lw $a0, -128($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -132($fp)
    # FP[-4] = t76
    lw $t0, -132($fp)
    sw $t0, -4($fp)
    # t77 = FP[-20]."incrementarEdad"
    lw $t0, -20($fp)
    # (Resolviendo dirección de método Persona_incrementarEdad)
    la $t0, Persona_incrementarEdad
    sw $t0, -136($fp)
    # push 7
    li $t0, 7
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-20]
    lw $t0, -20($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t78 = call t77, 2
    # Llamada indirecta a puntero en temporal 't77'
    lw $t0, -136($fp)
    jalr $t0
    sw $v0, -140($fp)
    # SP = SP + 8
    addu $sp, $sp, 8
    # t79 = FP[-4] add t78
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -140($fp)
    jal _string_concat
    sw $v0, -144($fp)
    # t80 = t79 add "\n"
    # Concatenación de strings detectada
    lw $a0, -144($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -148($fp)
    # FP[-4] = t80
    lw $t0, -148($fp)
    sw $t0, -4($fp)
    # t81 = FP[-28]."saludar"
    lw $t0, -28($fp)
    # (Resolviendo dirección de método Persona_saludar)
    la $t0, Persona_saludar
    sw $t0, -152($fp)
    # push FP[-28]
    lw $t0, -28($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t82 = call t81, 1
    # Llamada indirecta a puntero en temporal 't81'
    lw $t0, -152($fp)
    jalr $t0
    sw $v0, -156($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t83 = FP[-4] add t82
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -156($fp)
    jal _string_concat
    sw $v0, -160($fp)
    # t84 = t83 add "\n"
    # Concatenación de strings detectada
    lw $a0, -160($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -164($fp)
    # FP[-4] = t84
    lw $t0, -164($fp)
    sw $t0, -4($fp)
    # t85 = FP[-28]."estudiar"
    lw $t0, -28($fp)
    # (Resolviendo dirección de método Estudiante_estudiar)
    la $t0, Estudiante_estudiar
    sw $t0, -168($fp)
    # push FP[-28]
    lw $t0, -28($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t86 = call t85, 1
    # Llamada indirecta a puntero en temporal 't85'
    lw $t0, -168($fp)
    jalr $t0
    sw $v0, -172($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t87 = FP[-4] add t86
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -172($fp)
    jal _string_concat
    sw $v0, -176($fp)
    # t88 = t87 add "\n"
    # Concatenación de strings detectada
    lw $a0, -176($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -180($fp)
    # FP[-4] = t88
    lw $t0, -180($fp)
    sw $t0, -4($fp)
    # t89 = FP[-28]."incrementarEdad"
    lw $t0, -28($fp)
    # (Resolviendo dirección de método Persona_incrementarEdad)
    la $t0, Persona_incrementarEdad
    sw $t0, -184($fp)
    # push 6
    li $t0, 6
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-28]
    lw $t0, -28($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t90 = call t89, 2
    # Llamada indirecta a puntero en temporal 't89'
    lw $t0, -184($fp)
    jalr $t0
    sw $v0, -188($fp)
    # SP = SP + 8
    addu $sp, $sp, 8
    # t91 = FP[-4] add t90
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -188($fp)
    jal _string_concat
    sw $v0, -192($fp)
    # t92 = t91 add "\n"
    # Concatenación de strings detectada
    lw $a0, -192($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -196($fp)
    # FP[-4] = t92
    lw $t0, -196($fp)
    sw $t0, -4($fp)
    # FP[-32] = 1
    li $t0, 1
    sw $t0, -32($fp)
    # L2:
L2:
    # t93 = FP[-32] <= 12
    lw $t0, -32($fp)
    li $t1, 12
    sle $t2, $t0, $t1
    sw $t2, -200($fp)
    # ifFalse t93 goto L3
    lw $t0, -200($fp)
    beq $t0, $zero, L3
    # t94 = FP[-32] mod 2
    lw $t0, -32($fp)
    li $t1, 2
    rem $t2, $t0, $t1
    sw $t2, -204($fp)
    # t95 = t94 == 0
    lw $t0, -204($fp)
    li $t1, 0
    seq $t2, $t0, $t1
    sw $t2, -208($fp)
    # ifFalse t95 goto L4
    lw $t0, -208($fp)
    beq $t0, $zero, L4
    # push FP[-32]
    lw $t0, -32($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t94 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -204($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t96 = FP[-4] add t94
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -204($fp)
    jal _string_concat
    sw $v0, -212($fp)
    # t97 = t96 add " es par\n"
    # Concatenación de strings detectada
    lw $a0, -212($fp)
    la $a1, _str_12
    jal _string_concat
    sw $v0, -216($fp)
    # FP[-4] = t97
    lw $t0, -216($fp)
    sw $t0, -4($fp)
    # goto L5
    j L5
    # L4:
L4:
    # push FP[-32]
    lw $t0, -32($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t98 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -220($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t99 = FP[-4] add t98
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    lw $a1, -220($fp)
    jal _string_concat
    sw $v0, -224($fp)
    # t100 = t99 add " es impar\n"
    # Concatenación de strings detectada
    lw $a0, -224($fp)
    la $a1, _str_13
    jal _string_concat
    sw $v0, -228($fp)
    # FP[-4] = t100
    lw $t0, -228($fp)
    sw $t0, -4($fp)
    # L5:
L5:
    # t101 = FP[-32] add 1
    lw $t0, -32($fp)
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, -232($fp)
    # FP[-32] = t101
    lw $t0, -232($fp)
    sw $t0, -32($fp)
    # goto L2
    j L2
    # L3:
L3:
    # t93 = FP[-12].4
    lw $t0, -12($fp)
    # (Accediendo a campo en offset 4)
    lw $t1, 4($t0)
    sw $t1, -200($fp)
    # t102 = t93 mul 2
    lw $t0, -200($fp)
    li $t1, 2
    mul $t2, $t0, $t1
    sw $t2, -236($fp)
    # t103 = 5 sub 3
    li $t0, 5
    li $t1, 3
    sub $t2, $t0, $t1
    sw $t2, -240($fp)
    # t104 = t103 div 2
    lw $t0, -240($fp)
    li $t1, 2
    div $t2, $t0, $t1
    sw $t2, -244($fp)
    # t105 = t102 add t104
    lw $t0, -236($fp)
    lw $t1, -244($fp)
    add $t2, $t0, $t1
    sw $t2, -248($fp)
    # FP[-36] = t105
    lw $t0, -248($fp)
    sw $t0, -36($fp)
    # t104 = FP[-4] add "Resultado de la expresión: "
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    la $a1, _str_14
    jal _string_concat
    sw $v0, -244($fp)
    # push FP[-36]
    lw $t0, -36($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t102 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -236($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t106 = t104 add t102
    # Concatenación de strings detectada
    lw $a0, -244($fp)
    lw $a1, -236($fp)
    jal _string_concat
    sw $v0, -252($fp)
    # t107 = t106 add "\n"
    # Concatenación de strings detectada
    lw $a0, -252($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -256($fp)
    # FP[-4] = t107
    lw $t0, -256($fp)
    sw $t0, -4($fp)
    # FP[-40] = 0
    li $t0, 0
    sw $t0, -40($fp)
    # t108 = FP[-12]."promedioNotas"
    lw $t0, -12($fp)
    # (Resolviendo dirección de método Estudiante_promedioNotas)
    la $t0, Estudiante_promedioNotas
    sw $t0, -260($fp)
    # push 94
    li $t0, 94
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 95
    li $t0, 95
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 100
    li $t0, 100
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 98
    li $t0, 98
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 95
    li $t0, 95
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push 99
    li $t0, 99
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # push FP[-12]
    lw $t0, -12($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t109 = call t108, 7
    # Llamada indirecta a puntero en temporal 't108'
    lw $t0, -260($fp)
    jalr $t0
    sw $v0, -264($fp)
    # SP = SP + 28
    addu $sp, $sp, 28
    # FP[-40] = t109
    lw $t0, -264($fp)
    sw $t0, -40($fp)
    # t110 = FP[-4] add "Promedio (entero): "
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    la $a1, _str_16
    jal _string_concat
    sw $v0, -268($fp)
    # push FP[-40]
    lw $t0, -40($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t111 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -272($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t112 = t110 add t111
    # Concatenación de strings detectada
    lw $a0, -268($fp)
    lw $a1, -272($fp)
    jal _string_concat
    sw $v0, -276($fp)
    # t113 = t112 add "\n"
    # Concatenación de strings detectada
    lw $a0, -276($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -280($fp)
    # FP[-4] = t113
    lw $t0, -280($fp)
    sw $t0, -4($fp)
    # t114 = FP[-4] add "Prueba: Fibonacci recursivo\n"
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    la $a1, _str_17
    jal _string_concat
    sw $v0, -284($fp)
    # FP[-4] = t114
    lw $t0, -284($fp)
    sw $t0, -4($fp)
    # FP[-44] = 20
    li $t0, 20
    sw $t0, -44($fp)
    # FP[-48] = 0
    li $t0, 0
    sw $t0, -48($fp)
    # L6:
L6:
    # t115 = FP[-48] <= FP[-44]
    lw $t0, -48($fp)
    lw $t1, -44($fp)
    sle $t2, $t0, $t1
    sw $t2, -288($fp)
    # ifFalse t115 goto L7
    lw $t0, -288($fp)
    beq $t0, $zero, L7
    # push FP[-48]
    lw $t0, -48($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t116 = call fibonacci, 1
    jal fibonacci
    sw $v0, -292($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # FP[-52] = t116
    lw $t0, -292($fp)
    sw $t0, -52($fp)
    # t117 = FP[-4] add "Fib("
    # Concatenación de strings detectada
    lw $a0, -4($fp)
    la $a1, _str_18
    jal _string_concat
    sw $v0, -296($fp)
    # push FP[-48]
    lw $t0, -48($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t118 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -300($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t119 = t117 add t118
    # Concatenación de strings detectada
    lw $a0, -296($fp)
    lw $a1, -300($fp)
    jal _string_concat
    sw $v0, -304($fp)
    # t120 = t119 add ") = "
    # Concatenación de strings detectada
    lw $a0, -304($fp)
    la $a1, _str_19
    jal _string_concat
    sw $v0, -308($fp)
    # push FP[-52]
    lw $t0, -52($fp)
    subu $sp, $sp, 4
    sw $t0, 0($sp)
    # t121 = call toString, 1
    # Interceptando llamada a toString -> _int_to_string
    lw $a0, 0($sp)
    jal _int_to_string
    sw $v0, -312($fp)
    # SP = SP + 4
    addu $sp, $sp, 4
    # t122 = t120 add t121
    # Concatenación de strings detectada
    lw $a0, -308($fp)
    lw $a1, -312($fp)
    jal _string_concat
    sw $v0, -316($fp)
    # t123 = t122 add "\n"
    # Concatenación de strings detectada
    lw $a0, -316($fp)
    la $a1, _str_9
    jal _string_concat
    sw $v0, -320($fp)
    # FP[-4] = t123
    lw $t0, -320($fp)
    sw $t0, -4($fp)
    # t124 = FP[-48] add 1
    lw $t0, -48($fp)
    li $t1, 1
    add $t2, $t0, $t1
    sw $t2, -324($fp)
    # FP[-48] = t124
    lw $t0, -324($fp)
    sw $t0, -48($fp)
    # goto L6
    j L6
    # L7:
L7:
    # print FP[-4]
    lw $a0, -4($fp)
    # (Llamando a print para tipo: string)
    jal _print_string
    
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
    subu $sp, $sp, 16      # Reservar stack
    sw $ra, 12($sp)
    sw $s0, 8($sp)        # Guardar str1
    sw $s1, 4($sp)        # Guardar str2
    sw $s2, 0($sp)        # Guardar longitudes

    move $s0, $a0         # $s0 = str1
    move $s1, $a1         # $s1 = str2

    # --- ***** INICIO DE CORRECCIÓN (Manejo de Nulls) ***** ---
    # Si $s0 (str1) es 0 (null), apuntarlo a _str_0 (string vacío global)
    bne $s0, $zero, _sc_s1_ok
    la $s0, _str_0
_sc_s1_ok:
    # Si $s1 (str2) es 0 (null), apuntarlo a _str_0 (string vacío global)
    bne $s1, $zero, _sc_s2_ok
    la $s1, _str_0
_sc_s2_ok:
    # --- ***** FIN DE CORRECCIÓN ***** ---

    # 1. Calcular largo total
    move $a0, $s0
    jal _string_len
    move $s2, $v0         # $s2 = len(str1)

    move $a0, $s1
    jal _string_len       # <-- Esta llamada (la línea 1430-ish) AHORA ES SEGURA
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
