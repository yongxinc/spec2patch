# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-001 Generic KDF input encoding (TS 33.220 B.2.0)
The KDF input string is S = FC || P0 || L0 || P1 || L1 || ... where each Li is the length of Pi in octets, encoded as a 2-octet big-endian integer. The output is HMAC-SHA-256 of S keyed with the KDF key.

## REQ-002 K_AUSF derivation (TS 33.501 A.2)
K_AUSF = KDF(CK || IK, FC = 0x6A, P0 = serving network name, P1 = SQN xor AK (6 octets)). The parameters are given in exactly this order. The full 256-bit output is K_AUSF.

## REQ-003 RES* / XRES* derivation (TS 33.501 A.4)
(X)RES* = KDF(CK || IK, FC = 0x6B, P0 = serving network name, P1 = RAND (16 octets), P2 = (X)RES). The 128 least significant bits of the output are (X)RES*.

## REQ-004 HRES* / HXRES* derivation (TS 33.501 A.5)
H(X)RES* is computed as SHA-256 over RAND || (X)RES*, in this order. The 128 least significant bits of the hash are H(X)RES*.

## REQ-005 K_SEAF derivation (TS 33.501 A.6)
K_SEAF = KDF(K_AUSF, FC = 0x6C, P0 = serving network name). The full 256-bit output is K_SEAF.

## REQ-006 Serving network name in KDF input (TS 33.220 B.2.1.2)
Character-string parameters of the KDF, such as the serving network name, are encoded to octets with UTF-8.
