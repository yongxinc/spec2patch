# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-012 ECIES Profile A key agreement (TS 33.501 C.3.4.1)
Profile A uses X25519. The X25519 output is used directly as the shared secret Z for the key derivation.

## REQ-013 ECIES Profile B ephemeral public key (TS 33.501 C.3.4.2)
Profile B uses secp256r1. The ephemeral public key sent in the scheme output must be point-compressed (33 octets, first octet 0x02 or 0x03).

## REQ-014 ECIES key derivation (TS 33.501 C.3.4.1, C.3.4.2)
The ECIES key material is derived with ANSI-X9.63-KDF using SHA-256. SharedInfo1 is the ephemeral public key sent in the scheme output.

## REQ-015 ECIES key material split (TS 33.501 C.3.2)
The derived key K is split as: encryption key EK = leftmost 128 bits, initial counter block ICB = next 128 bits, MAC key MK = rightmost 256 bits.

## REQ-016 ECIES encryption (TS 33.501 C.3.4.0)
The plaintext is encrypted with AES-128 in CTR mode using EK and the ICB as the initial counter block.

## REQ-017 ECIES MAC (TS 33.501 C.3.4.0)
The MAC tag is the 64 leftmost bits (8 octets) of HMAC-SHA-256 computed with MK over the ciphertext.

## REQ-018 ECIES scheme output layout (TS 33.501 C.3.2)
The scheme output is the concatenation: ephemeral public key || ciphertext || MAC tag.

## REQ-019 ECIES MAC verified before decryption (TS 33.501 C.3.3)
The home network recomputes the MAC tag over the received ciphertext and compares it with the received tag before decrypting. If they differ, the SUCI is rejected and no plaintext, not even partial, is produced.
