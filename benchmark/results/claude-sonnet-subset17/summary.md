# Benchmark: claude-sonnet-subset17

backend=claude-cli model=sonnet spec2patch@0605569

- 真陽性 TP: **10/12**
- 部分正確: **0/12**
- 漏報: **2/12**
- 假警報(嚴格): **3/5**
- 假警報(寬鬆): **3/5**
- TP 案例中同時多報非目標 flag: 10
- 目標被判 missing 但無 evidence(算漏報): 1
- 有 LLM 呼叫失敗的案例: 0

| case | class | target status | flags |
| --- | --- | --- | --- |
| V02 | TP | missing | [('REQ-001', 'missing'), ('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing')] |
| V03 | TP | missing | [('REQ-001', 'missing'), ('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-004', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing')] |
| V04 | TP | missing | [('REQ-001', 'missing'), ('REQ-003', 'missing'), ('REQ-004', 'missing'), ('REQ-005', 'missing')] |
| V05 | TP | missing | [('REQ-001', 'missing'), ('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing')] |
| V07 | TP | missing | [('REQ-008', 'missing'), ('REQ-009', 'missing'), ('REQ-010', 'missing'), ('REQ-011', 'missing')] |
| V09 | TP | missing | [('REQ-010', 'missing'), ('REQ-011', 'missing')] |
| V13 | TP | missing | [('REQ-012', 'missing'), ('REQ-014', 'missing'), ('REQ-015', 'missing'), ('REQ-016', 'missing'), ('REQ-017', 'missing'), ('REQ-019', 'missing')] |
| V14 | TP | missing | [('REQ-015', 'missing'), ('REQ-017', 'missing'), ('REQ-018', 'missing'), ('REQ-019', 'missing')] |
| V15 | TP | missing | [('REQ-032', 'missing'), ('REQ-033', 'missing'), ('REQ-035', 'missing')] |
| V16 | TP | missing | [('REQ-031', 'missing'), ('REQ-032', 'missing'), ('REQ-033', 'missing')] |
| V17 | miss | missing | [] |
| V19 | miss | covered | [] |
| B01 | false_alarm | - | [('REQ-001', 'missing'), ('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-004', 'missing'), ('REQ-005', 'missing')] |
| B02 | false_alarm | - | [('REQ-032', 'missing'), ('REQ-033', 'missing'), ('REQ-035', 'missing')] |
| B03 | clean | - | [] |
| B04 | false_alarm | - | [('REQ-029', 'missing'), ('REQ-030', 'missing')] |
| B05 | clean | - | [] |
