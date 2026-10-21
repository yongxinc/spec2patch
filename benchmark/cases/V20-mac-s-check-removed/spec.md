# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-029 ARPF sets the separation bit (TS 33.501 6.1.3.2 step 1)
The ARPF generates 5G authentication vectors with the AMF separation bit set to 1.
Code: udm/arpf.py::generate_he_av

## REQ-030 Resynchronisation at the home network (TS 33.102 6.3.5)
From AUTS the home network recovers SQN_MS = (SQN_MS xor AK*) xor AK* and verifies MAC-S with the dummy AMF 0x0000. If MAC-S does not match, the resynchronisation is rejected and SQN_HE is not changed.
Code: udm/arpf.py::resynchronise
