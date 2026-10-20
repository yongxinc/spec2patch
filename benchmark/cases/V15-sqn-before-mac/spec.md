# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-031 UE verifies the AUTN MAC (TS 33.102 6.3.3)
The USIM computes XMAC from RAND, the recovered SQN and the AMF, and compares it with the MAC in AUTN. If they differ, the UE rejects the authentication with a MAC failure.

## REQ-032 UE verifies SQN freshness (TS 33.102 6.3.3, Annex C.2.1)
After the MAC check succeeds, the USIM accepts SQN only if it is greater than the stored SQN_MS and not more than DELTA ahead of it. Otherwise it reports a synchronisation failure with AUTS.

## REQ-033 MAC check before SQN check (TS 33.102 6.3.3)
The USIM verifies the AUTN MAC first and only then checks the freshness of SQN. A MAC failure is reported without evaluating the SQN.

## REQ-034 UE checks the separation bit (TS 33.501 6.1.3.2 step 7)
The ME checks that the AMF separation bit in AUTN is 1; if it is 0 the authentication is rejected.

## REQ-035 UE updates SQN_MS (TS 33.102 Annex C.2.1)
After a successful authentication the stored SQN_MS is set to the accepted SQN.
