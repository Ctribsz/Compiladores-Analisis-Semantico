0x1000 = 10
0x1004 = 20
t1 = @0x1000
t2 = @0x1004
t3 = t1 add t2
0x1008 = t3
t3 = @0x1000
t2 = t3 mul 2
t3 = @0x1004
t1 = t3 div 5
t3 = t2 add t1
t1 = t3 sub 3
0x100c = t1
t1 = @0x1000
t3 = @0x1004
t2 = t1 < t3
0x1010 = t2
t3 = @0x1000
t1 = t3 == 10
ifFalse t1 goto L0
t1 = @0x1004
t3 = t1 != 0
t2 = t3
goto L1
L0:
t2 = false
L1:
0x1014 = t2
t3 = @0x1010
t1 = !t3
if t1 goto L2
t1 = @0x1014
t2 = t1
goto L3
L2:
t2 = true
L3:
0x1018 = t2
t2 = @0x1000
t1 = @0x1004
t3 = t2 < t1
ifFalse t3 goto L4
t1 = @0x1000
0x1008 = t1
goto L5
L4:
t1 = @0x1004
0x1008 = t1
L5:
0x101c = 0
L6:
t1 = @0x101c
t2 = t1 < 5
ifFalse t2 goto L7
t1 = @0x101c
print t1
t1 = @0x101c
t4 = t1 add 1
0x101c = t4
goto L6
L7:
0x1020 = 0
L8:
t2 = @0x1020
t4 = t2 < 3
ifFalse t4 goto L10
t2 = @0x1020
print t2
L9:
t2 = @0x1020
t1 = t2 add 1
j = t1
goto L8
L10:
function add:
enter 20
t4 = @FP[-4]
t1 = @FP[-8]
t2 = t4 add t1
return t2
leave
end_function add
push 3
push 5
call add, 2
SP = SP + 8
pop t2
0x1024 = t2
function max:
enter 20
t2 = @FP[-4]
t1 = @FP[-8]
t4 = t2 > t1
ifFalse t4 goto L11
t1 = @FP[-4]
return t1
goto L12
L11:
t1 = @FP[-8]
return t1
L12:
leave
end_function max
t1 = new 5
t1[0] = 1
t1[1] = 2
t1[2] = 3
t1[3] = 4
t1[4] = 5
0x1028 = t1
t1 = @0x1028
t2 = t1[0]
0x102c = t2
t2 = @0x1028
t2[1] = 10
t2 = @0x1000
t5 = @0x1004
t6 = t2 < t5
ifFalse t6 goto L13
t2 = @0x1000
t5 = t2
goto L14
L13:
t7 = @0x1004
t5 = t7
L14:
0x1030 = t5
0x1034 = 0
L15:
t5 = @0x1034
t7 = t5 add 1
0x1034 = t7
L16:
t7 = @0x1034
t5 = t7 < 3
if t5 goto L15
L17:
0x1038 = 2
t5 = @0x1038
t7 = t5 == 1
if t7 goto L19
t7 = t5 == 2
if t7 goto L20
goto L21
L19:
print "One"
L20:
print "Two"
L21:
print "Other"
L18:
function constructor:
enter 20
t7 = @FP[-4]
this."x" = t7
t7 = @FP[-8]
this."y" = t7
leave
end_function constructor
function getX:
enter 12
t7 = this."x"
return t7
leave
end_function getX
t7 = new Point
push 10
push 20
call Point.constructor, 2
0x103c = t7
t7 = @0x103c
t2 = t7."getX"
call t2, 0
pop t6
0x1040 = t6
t6 = @0x103c
t6."x" = 30