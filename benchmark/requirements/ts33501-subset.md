# 5G SUCI / 5G-AKA requirements (subset, paraphrased)

Source: 3GPP TS 33.501 Rel-17 (Annex A, Annex C, clause 6.1.3.2, 6.12.2), TS 33.220 B.2,
TS 33.102 6.3 / Annex C / Annex H, TS 35.206 clause 4, TS 23.003 2.2 / 2.2B, TS 29.503 Annex C.
This file is a paraphrase written for the benchmark, one checkable rule per entry. Clause numbers
follow the citations in the implementation under test; verify them against the Rel-17 text before
quoting this file anywhere.

## REQ-001 Generic KDF input encoding (TS 33.220 B.2.0)
The KDF input string is S = FC || P0 || L0 || P1 || L1 || ... where each Li is the length of Pi in octets, encoded as a 2-octet big-endian integer. The output is HMAC-SHA-256 of S keyed with the KDF key.
Code: crypto/kdf.py::kdf

## REQ-002 K_AUSF derivation (TS 33.501 A.2)
K_AUSF = KDF(CK || IK, FC = 0x6A, P0 = serving network name, P1 = SQN xor AK (6 octets)). The parameters are given in exactly this order. The full 256-bit output is K_AUSF.
Code: crypto/kdf.py::derive_kausf, FC_KAUSF

## REQ-003 RES* / XRES* derivation (TS 33.501 A.4)
(X)RES* = KDF(CK || IK, FC = 0x6B, P0 = serving network name, P1 = RAND (16 octets), P2 = (X)RES). The 128 least significant bits of the output are (X)RES*.
Code: crypto/kdf.py::derive_res_star, FC_RES_STAR

## REQ-004 HRES* / HXRES* derivation (TS 33.501 A.5)
H(X)RES* is computed as SHA-256 over RAND || (X)RES*, in this order. The 128 least significant bits of the hash are H(X)RES*.
Code: crypto/kdf.py::derive_hres_star

## REQ-005 K_SEAF derivation (TS 33.501 A.6)
K_SEAF = KDF(K_AUSF, FC = 0x6C, P0 = serving network name). The full 256-bit output is K_SEAF.
Code: crypto/kdf.py::derive_kseaf, FC_KSEAF

## REQ-006 Serving network name in KDF input (TS 33.220 B.2.1.2)
Character-string parameters of the KDF, such as the serving network name, are encoded to octets with UTF-8.
Code: crypto/kdf.py::_snn, _encode_snn

## REQ-007 Serving network name format (TS 33.501 6.1.1.4)
SNN = "5G:mnc" MNC ".mcc" MCC ".3gppnetwork.org". The MNC is always written with three digits, so a two-digit MNC gets a leading zero.
Code: formats/snn.py::serving_network_name

## REQ-008 OPc derivation (TS 35.206 4.1)
OPc = OP xor E[OP]K, where E is AES-128 encryption under K.
Code: crypto/milenage.py::compute_opc

## REQ-009 MILENAGE constants and rotations (TS 35.206 4.1)
The constants are c1 = 0, c2 = 1, c3 = 2, c4 = 4, c5 = 8 (128-bit values, the number in the last octet). The rotations are r1 = 64, r2 = 0, r3 = 32, r4 = 64, r5 = 96 bits.
Code: crypto/milenage.py::C1, C2, C3, C4, C5, R1, R2, R3, R4, R5

## REQ-010 MILENAGE f1 / f1* input (TS 35.206 4.1)
TEMP = E[RAND xor OPc]K. IN1 = SQN || AMF || SQN || AMF. OUT1 = E[TEMP xor rot(IN1 xor OPc, r1) xor c1]K xor OPc. MAC-A is the leftmost 64 bits of OUT1 and MAC-S is the rightmost 64 bits.
Code: crypto/milenage.py::f1_f1star

## REQ-011 MILENAGE f2-f5* output mapping (TS 35.206 4.1)
OUTi = E[rot(TEMP xor OPc, ri) xor ci]K xor OPc for i = 2..5. RES = OUT2 bits 64..127, AK = OUT2 bits 0..47, CK = OUT3, IK = OUT4, AK* = OUT5 bits 0..47.
Code: crypto/milenage.py::milenage, _out, f5, f5star

## REQ-012 ECIES Profile A key agreement (TS 33.501 C.3.4.1)
Profile A uses X25519. The X25519 output is used directly as the shared secret Z for the key derivation.
Code: crypto/ecies.py::_shared_secret

## REQ-013 ECIES Profile B ephemeral public key (TS 33.501 C.3.4.2)
Profile B uses secp256r1. The ephemeral public key sent in the scheme output must be point-compressed (33 octets, first octet 0x02 or 0x03).
Code: crypto/ecies.py::encrypt, public_key, split_scheme_output

## REQ-014 ECIES key derivation (TS 33.501 C.3.4.1, C.3.4.2)
The ECIES key material is derived with ANSI-X9.63-KDF using SHA-256. SharedInfo1 is the ephemeral public key sent in the scheme output.
Code: crypto/ecies.py::_derive_keys

## REQ-015 ECIES key material split (TS 33.501 C.3.2)
The derived key K is split as: encryption key EK = leftmost 128 bits, initial counter block ICB = next 128 bits, MAC key MK = rightmost 256 bits.
Code: crypto/ecies.py::_derive_keys

## REQ-016 ECIES encryption (TS 33.501 C.3.4.0)
The plaintext is encrypted with AES-128 in CTR mode using EK and the ICB as the initial counter block.
Code: crypto/ecies.py::_aes128_ctr

## REQ-017 ECIES MAC (TS 33.501 C.3.4.0)
The MAC tag is the 64 leftmost bits (8 octets) of HMAC-SHA-256 computed with MK over the ciphertext.
Code: crypto/ecies.py::_mac

## REQ-018 ECIES scheme output layout (TS 33.501 C.3.2)
The scheme output is the concatenation: ephemeral public key || ciphertext || MAC tag.
Code: crypto/ecies.py::encrypt, split_scheme_output

## REQ-019 ECIES MAC verified before decryption (TS 33.501 C.3.3)
The home network recomputes the MAC tag over the received ciphertext and compares it with the received tag before decrypting. If they differ, the SUCI is rejected and no plaintext, not even partial, is produced.
Code: crypto/ecies.py::decrypt; udm/sidf.py::deconceal

## REQ-020 SUCI string format (TS 29.503 Annex C, TS 23.003 2.2B)
A SUCI of SUPI type IMSI is written suci-0-MCC-MNC-RoutingIndicator-ProtectionSchemeId-HomeNetworkPublicKeyId-SchemeOutput. For ECIES schemes the scheme output is the hex string of the ECIES output; for the null-scheme it is the MSIN digits.
Code: formats/suci.py::Suci

## REQ-021 Home Network Public Key Identifier (TS 23.003 2.2B)
The Home Network Public Key Identifier is 0 if and only if the null-scheme is used.
Code: formats/suci.py::Suci

## REQ-022 Routing Indicator (TS 23.003 2.2B)
The Routing Indicator is 1 to 4 decimal digits; leading zeros are significant, so "012" and "12" are different values.
Code: formats/suci.py::Suci

## REQ-023 SUPI / IMSI structure (TS 23.003 2.2)
An IMSI is at most 15 digits: MCC (3 digits), MNC (2 or 3 digits) and MSIN. The IMSI does not say by itself how long the MNC is.
Code: formats/supi.py::ImsiSupi

## REQ-024 MSIN scheme input encoding (TS 33.501 C.3.1, TS 24.501 Figure 9.11.3.4.3a)
The MSIN is encoded as packed BCD. In each octet the first digit of the pair goes in bits 1-4 (low nibble) and the second in bits 5-8 (high nibble). An odd number of digits is padded with the nibble 1111.
Code: formats/supi.py::msin_to_scheme_input, scheme_input_to_msin

## REQ-025 Only the MSIN is concealed (TS 33.501 6.12.2)
Concealment applies to the MSIN only. MCC and MNC stay in clear in the SUCI so the serving network can route to the home network.
Code: ue/suci.py::conceal

## REQ-026 Null-scheme (TS 33.501 C.2)
With the null-scheme the scheme output equals the scheme input, unchanged.
Code: ue/suci.py::conceal

## REQ-027 AUTN layout (TS 33.102 6.3.2)
AUTN = (SQN xor AK) (48 bits) || AMF (16 bits) || MAC (64 bits), in this order.
Code: formats/autn.py::build_autn, split_autn

## REQ-028 AMF separation bit (TS 33.102 Annex H)
The AMF separation bit is bit 0 of the AMF, numbered from the most significant bit. For the resynchronisation MAC-S the AMF is a dummy value of all zeros.
Code: formats/autn.py::separation_bit, AMF_RESYNC

## REQ-029 ARPF sets the separation bit (TS 33.501 6.1.3.2 step 1)
The ARPF generates 5G authentication vectors with the AMF separation bit set to 1.
Code: udm/arpf.py::generate_he_av

## REQ-030 Resynchronisation at the home network (TS 33.102 6.3.5)
From AUTS the home network recovers SQN_MS = (SQN_MS xor AK*) xor AK* and verifies MAC-S with the dummy AMF 0x0000. If MAC-S does not match, the resynchronisation is rejected and SQN_HE is not changed.
Code: udm/arpf.py::resynchronise

## REQ-031 UE verifies the AUTN MAC (TS 33.102 6.3.3)
The USIM computes XMAC from RAND, the recovered SQN and the AMF, and compares it with the MAC in AUTN. If they differ, the UE rejects the authentication with a MAC failure.
Code: ue/auth.py::AutnMacFailure, mac_a

## REQ-032 UE verifies SQN freshness (TS 33.102 6.3.3, Annex C.2.1)
After the MAC check succeeds, the USIM accepts SQN only if it is greater than the stored SQN_MS and not more than DELTA ahead of it. Otherwise it reports a synchronisation failure with AUTS.
Code: ue/auth.py::SynchronisationFailure, sqn_ms, delta, DELTA, build_auts

## REQ-033 MAC check before SQN check (TS 33.102 6.3.3)
The USIM verifies the AUTN MAC first and only then checks the freshness of SQN. A MAC failure is reported without evaluating the SQN.
Code: ue/auth.py::AutnMacFailure, SynchronisationFailure

## REQ-034 UE checks the separation bit (TS 33.501 6.1.3.2 step 7)
The ME checks that the AMF separation bit in AUTN is 1; if it is 0 the authentication is rejected.
Code: ue/auth.py::separation_bit, AmfSeparationBitNotSet

## REQ-035 UE updates SQN_MS (TS 33.102 Annex C.2.1)
After a successful authentication the stored SQN_MS is set to the accepted SQN.
Code: ue/auth.py::sqn_ms_after

## REQ-036 AUSF stores XRES* and hides it from the SEAF (TS 33.501 6.1.3.2 steps 3-5)
The AUSF stores XRES*, computes HXRES* from RAND and XRES*, and sends only RAND, AUTN and HXRES* to the SEAF. XRES* and K_AUSF are not sent to the SEAF.
Code: ausf/ausf.py::prepare, SeAv

## REQ-037 AUSF confirms RES* (TS 33.501 6.1.3.2 steps 11-12)
The AUSF compares the received RES* with the stored XRES* over their full length. K_SEAF is released only if they are equal.
Code: ausf/ausf.py::confirm

## REQ-038 SEAF compares HRES* with HXRES* (TS 33.501 6.1.3.2 step 9)
The SEAF computes HRES* from RAND and the received RES* with the same function as HXRES* and compares it with the stored HXRES*. If they differ, the authentication is rejected.
Code: seaf/seaf.py::verify_res_star
