# Benchmark: llama3.1-8b-split-schema

backend=ollama model=llama3.1:8b spec2patch@bbb643b

- 真陽性 TP: **8/20**
- 部分正確: **9/20**
- 漏報: **3/20**
- 假警報(嚴格): **3/5**
- 假警報(寬鬆): **3/5**
- TP 案例中同時多報非目標 flag: 6
- 目標被判 missing 但無 evidence(算漏報): 0
- 有 LLM 呼叫失敗的案例: 0

| case | class | target status | flags |
| --- | --- | --- | --- |
| V01 | TP | missing | [('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing')] |
| V02 | partial | covered | [('REQ-006', 'missing')] |
| V03 | partial | covered | [('REQ-001', 'missing'), ('REQ-006', 'missing')] |
| V04 | partial | covered | [('REQ-001', 'missing'), ('REQ-002', 'missing')] |
| V05 | partial | covered | [('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing')] |
| V06 | TP | missing | [('REQ-007', 'missing')] |
| V07 | partial | covered | [('REQ-010', 'missing'), ('REQ-011', 'missing')] |
| V08 | TP | missing | [('REQ-008', 'missing'), ('REQ-009', 'missing'), ('REQ-010', 'missing'), ('REQ-011', 'missing')] |
| V09 | partial | covered | [('REQ-008', 'missing'), ('REQ-009', 'missing'), ('REQ-011', 'missing')] |
| V10 | TP | missing | [('REQ-009', 'missing'), ('REQ-010', 'missing'), ('REQ-011', 'missing')] |
| V11 | TP | missing | [('REQ-013', 'missing'), ('REQ-014', 'missing'), ('REQ-015', 'missing'), ('REQ-017', 'missing'), ('REQ-019', 'missing')] |
| V12 | TP | missing | [('REQ-012', 'missing'), ('REQ-013', 'missing'), ('REQ-015', 'missing'), ('REQ-016', 'missing'), ('REQ-017', 'missing')] |
| V13 | partial | covered | [('REQ-012', 'missing')] |
| V14 | miss | covered | [] |
| V15 | miss | covered | [] |
| V16 | partial | covered | [('REQ-033', 'missing'), ('REQ-035', 'missing')] |
| V17 | partial | covered | [('REQ-031', 'missing'), ('REQ-032', 'missing'), ('REQ-033', 'missing')] |
| V18 | TP | missing | [('REQ-037', 'missing')] |
| V19 | miss | covered | [] |
| V20 | TP | missing | [('REQ-029', 'missing'), ('REQ-030', 'missing')] |
| B01 | false_alarm | - | [('REQ-001', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing')] |
| B02 | false_alarm | - | [('REQ-031', 'missing'), ('REQ-033', 'missing')] |
| B03 | clean | - | [] |
| B04 | false_alarm | - | [('REQ-030', 'missing')] |
| B05 | clean | - | [] |
