"""25 hand-written changes to the 5G SUCI / 5G-AKA reference implementation.

V01-V20: each breaks exactly one rule of the specification (`target` = the REQ in
requirements/ts33501-subset.md that it violates).
B01-B05: behaviour-preserving edits (rename, comment, refactor); no finding is expected.

`needs_context=True` marks a case whose verdict cannot be reached from the diff alone (V19: the
parameter order of `derive_hres_star` is not visible in the diff).

`edits` is a list of (old, new, count): `old` must occur exactly `count` times in the file.
"""

# fmt: off
VIOLATIONS = [
    dict(id="V01", slug="res-star-fc", file="crypto/kdf.py", target="REQ-003",
         summary="RES* 推導的 FC 值由 0x6B 改成 0x6A(K_AUSF 的 FC)",
         expected="應指出 REQ-003:RES*/XRES* 的 FC 必須是 0x6B,diff 把它改成 0x6A。",
         edits=[("FC_RES_STAR = 0x6B       # TS 33.501 A.4", "FC_RES_STAR = 0x6A       # TS 33.501 A.4", 1)]),
    dict(id="V02", slug="kseaf-fc", file="crypto/kdf.py", target="REQ-005",
         summary="K_SEAF 推導的 FC 值由 0x6C 改成 0x6D(K_AMF 的 FC)",
         expected="應指出 REQ-005:K_SEAF 的 FC 必須是 0x6C,diff 把它改成 0x6D。",
         edits=[("FC_KSEAF = 0x6C          # TS 33.501 A.6", "FC_KSEAF = 0x6D          # TS 33.501 A.6", 1)]),
    dict(id="V03", slug="res-star-msb", file="crypto/kdf.py", target="REQ-003",
         summary="RES* 取 KDF 輸出的前 128 bits(最高位)而非後 128 bits(最低位)",
         expected="應指出 REQ-003:(X)RES* 是輸出的 128 least significant bits,diff 改取 [:16]。",
         edits=[("return kdf(ck + ik, FC_RES_STAR, _snn(serving_network_name), rand, res)[16:]",
                 "return kdf(ck + ik, FC_RES_STAR, _snn(serving_network_name), rand, res)[:16]", 1)]),
    dict(id="V04", slug="hres-star-msb", file="crypto/kdf.py", target="REQ-004",
         summary="HXRES* 取 SHA-256 輸出的前 128 bits 而非後 128 bits",
         expected="應指出 REQ-004:H(X)RES* 是 SHA-256 的 128 least significant bits,diff 改取 [:16]。",
         edits=[("return hashlib.sha256(rand + res_star).digest()[16:]",
                 "return hashlib.sha256(rand + res_star).digest()[:16]", 1)]),
    dict(id="V05", slug="kausf-param-order", file="crypto/kdf.py", target="REQ-002",
         summary="K_AUSF 推導的參數順序對調(P0=SQN xor AK, P1=SNN)",
         expected="應指出 REQ-002:P0 必須是 SNN、P1 必須是 SQN xor AK,diff 把順序對調。",
         edits=[("return kdf(ck + ik, FC_KAUSF, _snn(serving_network_name), sqn_xor_ak)",
                 "return kdf(ck + ik, FC_KAUSF, sqn_xor_ak, _snn(serving_network_name))", 1)]),
    dict(id="V06", slug="snn-no-zero-pad", file="formats/snn.py", target="REQ-007",
         summary="Serving Network Name 的 MNC 不再補零到三位",
         expected="應指出 REQ-007:MNC 必須補零成三位,diff 移除了 zfill(3)。",
         edits=[('return f"5G:mnc{mnc.zfill(3)}.mcc{mcc}.3gppnetwork.org"',
                 'return f"5G:mnc{mnc}.mcc{mcc}.3gppnetwork.org"', 1)]),
    dict(id="V07", slug="milenage-r3", file="crypto/milenage.py", target="REQ-009",
         summary="MILENAGE 旋轉常數 r3 由 32 改成 64",
         expected="應指出 REQ-009:r3 必須是 32 bits,diff 改成 64。",
         edits=[("R1, R2, R3, R4, R5 = 64, 0, 32, 64, 96", "R1, R2, R3, R4, R5 = 64, 0, 64, 64, 96", 1)]),
    dict(id="V08", slug="opc-no-xor", file="crypto/milenage.py", target="REQ-008",
         summary="OPc 推導漏掉與 OP 的 XOR,直接回傳 E[OP]K",
         expected="應指出 REQ-008:OPc = OP xor E[OP]K,diff 只回傳 E[OP]K。",
         edits=[("    return _xor(op, _e(k, op))\n", "    return _e(k, op)\n", 1)]),
    dict(id="V09", slug="f1-in1-order", file="crypto/milenage.py", target="REQ-010",
         summary="f1 的 IN1 組成由 SQN||AMF||SQN||AMF 改成 AMF||SQN||AMF||SQN",
         expected="應指出 REQ-010:IN1 = SQN || AMF || SQN || AMF,diff 把 SQN 與 AMF 順序對調。",
         edits=[("in1 = sqn + amf + sqn + amf", "in1 = amf + sqn + amf + sqn", 1)]),
    dict(id="V10", slug="ck-ik-swap", file="crypto/milenage.py", target="REQ-011",
         summary="f3/f4 輸出對調:CK 取 OUT4、IK 取 OUT3",
         expected="應指出 REQ-011:CK = OUT3、IK = OUT4,diff 把兩者對調。",
         edits=[("        ck=out3,\n        ik=out4,\n", "        ck=out4,\n        ik=out3,\n", 1)]),
    dict(id="V11", slug="profile-b-uncompressed", file="crypto/ecies.py", target="REQ-013",
         summary="Profile B 的臨時公鑰不做點壓縮(compressed=False)",
         expected="應指出 REQ-013:Profile B 的臨時公鑰必須是壓縮點(33 octets),diff 改成 compressed=False。",
         edits=[("eph_pub = public_key(profile, eph_private_key, compressed=True)",
                 "eph_pub = public_key(profile, eph_private_key, compressed=False)", 1)]),
    dict(id="V12", slug="mac-rightmost", file="crypto/ecies.py", target="REQ-017",
         summary="ECIES MAC tag 取 HMAC 輸出的最右 8 octets 而非最左 8 octets",
         expected="應指出 REQ-017:MAC tag 是 HMAC-SHA-256 最左 64 bits,diff 改取 [-MAC_LEN:]。",
         edits=[("return hmac.new(mac_key, ciphertext, hashlib.sha256).digest()[:MAC_LEN]",
                 "return hmac.new(mac_key, ciphertext, hashlib.sha256).digest()[-MAC_LEN:]", 1)]),
    dict(id="V13", slug="ek-icb-swap", file="crypto/ecies.py", target="REQ-015",
         summary="ECIES 金鑰切分時 EK 與 ICB 對調",
         expected="應指出 REQ-015:EK 是最左 128 bits、ICB 是中間 128 bits,diff 把兩者對調。",
         edits=[("return k[:ENC_KEY_LEN], k[ENC_KEY_LEN:ENC_KEY_LEN + ICB_LEN], k[-MAC_KEY_LEN:]",
                 "return k[ENC_KEY_LEN:ENC_KEY_LEN + ICB_LEN], k[:ENC_KEY_LEN], k[-MAC_KEY_LEN:]", 1)]),
    dict(id="V14", slug="decrypt-before-mac", file="crypto/ecies.py", target="REQ-019",
         summary="SUCI 解封裝先解密、後驗證 MAC(驗證順序顛倒;結果仍會拒絕,但違反先驗後解)",
         expected="應指出 REQ-019:必須先驗證 MAC 再解密,diff 把解密移到 MAC 驗證之前。",
         edits=[("""    expected_mac = _mac(mac_key, ciphertext)
    # Not constant time on purpose: side-channel resistance is out of scope (README).
    if expected_mac != received_mac:
        raise EciesMacFailure(f"MAC tag mismatch: received {received_mac.hex()}")
    plaintext = _aes128_ctr(enc_key, icb, ciphertext)
""", """    plaintext = _aes128_ctr(enc_key, icb, ciphertext)
    expected_mac = _mac(mac_key, ciphertext)
    # Not constant time on purpose: side-channel resistance is out of scope (README).
    if expected_mac != received_mac:
        raise EciesMacFailure(f"MAC tag mismatch: received {received_mac.hex()}")
""", 1)]),
    dict(id="V15", slug="sqn-before-mac", file="ue/auth.py", target="REQ-033",
         summary="UE 先檢查 SQN 再驗證 AUTN 的 MAC(順序顛倒)",
         expected="應指出 REQ-033:必須先驗 AUTN MAC 再檢查 SQN,diff 把 SQN 檢查移到 MAC 檢查之前。",
         edits=[("""    # Not constant time on purpose: side-channel resistance is out of scope (README).
    if out.mac_a != mac:
        raise AutnMacFailure(f"XMAC {out.mac_a.hex()} != MAC {mac.hex()}")

    sqn = int.from_bytes(sqn_bytes, "big")
    if not (sqn_ms < sqn <= sqn_ms + delta):
        raise SynchronisationFailure(
            f"SQN {sqn:#014x} not in ({sqn_ms:#014x}, {sqn_ms + delta:#014x}]",
            auts=build_auts(k, opc, rand, sqn_ms), sqn_ms=sqn_ms, sqn_received=sqn)
""", """    sqn = int.from_bytes(sqn_bytes, "big")
    if not (sqn_ms < sqn <= sqn_ms + delta):
        raise SynchronisationFailure(
            f"SQN {sqn:#014x} not in ({sqn_ms:#014x}, {sqn_ms + delta:#014x}]",
            auts=build_auts(k, opc, rand, sqn_ms), sqn_ms=sqn_ms, sqn_received=sqn)

    # Not constant time on purpose: side-channel resistance is out of scope (README).
    if out.mac_a != mac:
        raise AutnMacFailure(f"XMAC {out.mac_a.hex()} != MAC {mac.hex()}")
""", 1)]),
    dict(id="V16", slug="sqn-range-removed", file="ue/auth.py", target="REQ-032",
         summary="移除 UE 的 SQN 範圍(新鮮度)檢查",
         expected="應指出 REQ-032:UE 必須檢查 SQN 在 (SQN_MS, SQN_MS+DELTA] 內,diff 移除了這段檢查。",
         edits=[("""    if not (sqn_ms < sqn <= sqn_ms + delta):
        raise SynchronisationFailure(
            f"SQN {sqn:#014x} not in ({sqn_ms:#014x}, {sqn_ms + delta:#014x}]",
            auts=build_auts(k, opc, rand, sqn_ms), sqn_ms=sqn_ms, sqn_received=sqn)

""", "\n", 1)]),
    dict(id="V17", slug="separation-bit-check-removed", file="ue/auth.py", target="REQ-034",
         summary="移除 ME 對 AMF separation bit 的檢查",
         expected="應指出 REQ-034:ME 必須檢查 AMF separation bit 為 1,diff 移除了這段檢查。",
         edits=[("""    if separation_bit(amf) != 1:
        raise AmfSeparationBitNotSet(f"AMF {amf.hex()} has separation bit 0")

""", "", 1)]),
    dict(id="V18", slug="res-star-truncated-compare", file="ausf/ausf.py", target="REQ-037",
         summary="AUSF 比對 RES* 與 XRES* 時只比對前 8 octets",
         expected="應指出 REQ-037:必須比對 RES* 與 XRES* 的完整長度,diff 只比對前 8 octets。",
         edits=[("if res_star != context.xres_star:", "if res_star[:8] != context.xres_star[:8]:", 1)]),
    dict(id="V19", slug="hres-arg-swap", file="seaf/seaf.py", target="REQ-038", needs_context=True,
         summary="SEAF 計算 HRES* 時 RAND 與 RES* 的順序對調",
         expected="應指出 REQ-038:HRES* 必須用與 HXRES* 相同的函式(RAND || RES*),diff 把參數順序對調。",
         edits=[("hres_star = kdf.derive_hres_star(rand, res_star)", "hres_star = kdf.derive_hres_star(res_star, rand)", 1)]),
    dict(id="V20", slug="mac-s-check-removed", file="udm/arpf.py", target="REQ-030",
         summary="重同步時移除 MAC-S 驗證",
         expected="應指出 REQ-030:重同步必須驗證 AUTS 的 MAC-S,diff 移除了比對與拒絕。",
         edits=[("""    if xmac_s != auts[6:]:
        raise AutsMacFailure(f"XMAC-S {xmac_s.hex()} != MAC-S {auts[6:].hex()}")
""", "", 1)]),
]

BENIGN = [
    dict(id="B01", slug="rename-private-helper", file="crypto/kdf.py",
         summary="把私有函式 _snn 改名為 _encode_snn(純改名)",
         edits=[("_snn(", "_encode_snn(", 4)]),
    dict(id="B02", slug="add-comments", file="ue/auth.py",
         summary="在 authenticate 內加兩行說明註解(純註解)",
         edits=[("    sqn = int.from_bytes(sqn_bytes, \"big\")\n",
                 "    # SQN is the 48-bit integer recovered by un-masking SQN xor AK with AK.\n"
                 "    sqn = int.from_bytes(sqn_bytes, \"big\")\n", 1),
                ("    res_star = kdf.derive_res_star(out.ck, out.ik, serving_network_name, rand, out.res)\n",
                 "    # Derive the keys that depend on the serving network name last.\n"
                 "    res_star = kdf.derive_res_star(out.ck, out.ik, serving_network_name, rand, out.res)\n", 1)]),
    dict(id="B03", slug="rename-local-variable", file="seaf/seaf.py",
         summary="把區域變數 hres_star 改名為 computed_hres_star(純改名)",
         edits=[("hres_star = kdf.derive_hres_star(rand, res_star)", "computed_hres_star = kdf.derive_hres_star(rand, res_star)", 1),
                ("if hres_star != hxres_star:", "if computed_hres_star != hxres_star:", 1),
                ('f"HRES* {hres_star.hex()} != HXRES* {hxres_star.hex()}"', 'f"HRES* {computed_hres_star.hex()} != HXRES* {hxres_star.hex()}"', 1),
                ("    return hres_star\n", "    return computed_hres_star\n", 1)]),
    dict(id="B04", slug="extract-xor-helper", file="udm/arpf.py",
         summary="把兩處 bytes(a ^ b ...) 抽成 _xor 輔助函式(重構,行為不變)",
         edits=[("from formats.autn import AMF_RESYNC, build_autn, separation_bit\n",
                 "from formats.autn import AMF_RESYNC, build_autn, separation_bit\n\n\n"
                 "def _xor(a: bytes, b: bytes) -> bytes:\n    return bytes(x ^ y for x, y in zip(a, b))\n", 1),
                ("sqn_xor_ak = bytes(a ^ b for a, b in zip(sqn_bytes, out.ak))", "sqn_xor_ak = _xor(sqn_bytes, out.ak)", 1),
                ("sqn_ms_bytes = bytes(a ^ b for a, b in zip(auts[:6], ak_star))", "sqn_ms_bytes = _xor(auts[:6], ak_star)", 1)]),
    dict(id="B05", slug="split-snn-expression", file="formats/snn.py",
         summary="把 SNN 字串拆成 network_id 與前綴兩步組合(重構,行為不變)",
         edits=[('    return f"5G:mnc{mnc.zfill(3)}.mcc{mcc}.3gppnetwork.org"\n',
                 '    network_id = f"mnc{mnc.zfill(3)}.mcc{mcc}.3gppnetwork.org"\n    return f"5G:{network_id}"\n', 1)]),
]
# fmt: on
