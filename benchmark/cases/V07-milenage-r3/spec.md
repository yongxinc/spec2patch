# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-008 OPc derivation (TS 35.206 4.1)
OPc = OP xor E[OP]K, where E is AES-128 encryption under K.

## REQ-009 MILENAGE constants and rotations (TS 35.206 4.1)
The constants are c1 = 0, c2 = 1, c3 = 2, c4 = 4, c5 = 8 (128-bit values, the number in the last octet). The rotations are r1 = 64, r2 = 0, r3 = 32, r4 = 64, r5 = 96 bits.

## REQ-010 MILENAGE f1 / f1* input (TS 35.206 4.1)
TEMP = E[RAND xor OPc]K. IN1 = SQN || AMF || SQN || AMF. OUT1 = E[TEMP xor rot(IN1 xor OPc, r1) xor c1]K xor OPc. MAC-A is the leftmost 64 bits of OUT1 and MAC-S is the rightmost 64 bits.

## REQ-011 MILENAGE f2-f5* output mapping (TS 35.206 4.1)
OUTi = E[rot(TEMP xor OPc, ri) xor ci]K xor OPc for i = 2..5. RES = OUT2 bits 64..127, AK = OUT2 bits 0..47, CK = OUT3, IK = OUT4, AK* = OUT5 bits 0..47.
