# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-038 SEAF compares HRES* with HXRES* (TS 33.501 6.1.3.2 step 9)
The SEAF computes HRES* from RAND and the received RES* with the same function as HXRES* and compares it with the stored HXRES*. If they differ, the authentication is rejected.
