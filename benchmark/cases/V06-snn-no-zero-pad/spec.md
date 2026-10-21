# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)

## REQ-007 Serving network name format (TS 33.501 6.1.1.4)
SNN = "5G:mnc" MNC ".mcc" MCC ".3gppnetwork.org". The MNC is always written with three digits, so a two-digit MNC gets a leading zero.
Code: formats/snn.py::serving_network_name
