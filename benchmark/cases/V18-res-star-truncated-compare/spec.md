# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-036 AUSF stores XRES* and hides it from the SEAF (TS 33.501 6.1.3.2 steps 3-5)
The AUSF stores XRES*, computes HXRES* from RAND and XRES*, and sends only RAND, AUTN and HXRES* to the SEAF. XRES* and K_AUSF are not sent to the SEAF.

## REQ-037 AUSF confirms RES* (TS 33.501 6.1.3.2 steps 11-12)
The AUSF compares the received RES* with the stored XRES* over their full length. K_SEAF is released only if they are equal.
