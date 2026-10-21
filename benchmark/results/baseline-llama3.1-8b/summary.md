# Benchmark: baseline-llama3.1-8b

backend=ollama model=llama3.1:8b spec2patch@ad237e1

- 真陽性 TP: **8/20**
- 部分正確: **12/20**
- 漏報: **0/20**
- 假警報(嚴格): **5/5**
- 假警報(寬鬆): **3/5**
- TP 案例中同時多報非目標 flag: 8
- 目標被判 missing 但無 evidence(算漏報): 0
- 有 LLM 呼叫失敗的案例: 0

| case | class | target status | flags |
| --- | --- | --- | --- |
| V01 | TP | missing | [('REQ-002', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing'), ('-', 'out-of-spec')] |
| V02 | partial | covered | [('REQ-006', 'missing'), ('-', 'out-of-spec')] |
| V03 | partial | covered | [('REQ-001', 'missing'), ('REQ-006', 'missing'), ('-', 'out-of-spec')] |
| V04 | partial | covered | [('REQ-001', 'missing'), ('REQ-002', 'missing'), ('-', 'out-of-spec')] |
| V05 | partial | covered | [('REQ-003', 'missing'), ('REQ-005', 'missing'), ('REQ-006', 'missing'), ('-', 'out-of-spec')] |
| V06 | TP | missing | [('REQ-007', 'missing'), ('-', 'out-of-spec')] |
| V07 | partial | covered | [('REQ-010', 'missing'), ('REQ-011', 'missing'), ('-', 'out-of-spec')] |
| V08 | TP | missing | [('REQ-008', 'missing'), ('REQ-009', 'missing'), ('REQ-010', 'missing'), ('REQ-011', 'missing'), ('-', 'out-of-spec')] |
| V09 | partial | covered | [('REQ-008', 'missing'), ('REQ-009', 'missing'), ('REQ-011', 'missing'), ('-', 'out-of-spec')] |
| V10 | TP | missing | [('REQ-009', 'missing'), ('REQ-010', 'missing'), ('REQ-011', 'missing'), ('-', 'out-of-spec')] |
| V11 | TP | missing | [('REQ-013', 'missing'), ('REQ-014', 'missing'), ('REQ-015', 'missing'), ('REQ-017', 'missing'), ('REQ-019', 'missing'), ('-', 'out-of-spec')] |
| V12 | TP | missing | [('REQ-012', 'missing'), ('REQ-013', 'missing'), ('REQ-015', 'missing'), ('REQ-016', 'missing'), ('REQ-017', 'missing'), ('-', 'out-of-spec')] |
| V13 | partial | covered | [('REQ-012', 'missing'), ('-', 'out-of-spec')] |
| V14 | partial | covered | [('-', 'out-of-spec')] |
| V15 | partial | covered | [('-', 'out-of-spec')] |
| V16 | partial | covered | [('REQ-033', 'missing'), ('REQ-035', 'missing'), ('-', 'out-of-spec')] |
| V17 | partial | covered | [('REQ-031', 'missing'), ('REQ-032', 'missing'), ('REQ-033', 'missing'), ('-', 'out-of-spec')] |
| V18 | TP | missing | [('REQ-037', 'missing'), ('-', 'out-of-spec')] |
| V19 | partial | covered | [('-', 'out-of-spec')] |
| V20 | TP | missing | [('REQ-029', 'missing'), ('REQ-030', 'missing'), ('-', 'out-of-spec')] |
| B01 | false_alarm | - | [('REQ-001', 'missing'), ('REQ-003', 'missing'), ('REQ-005', 'missing'), ('-', 'out-of-spec')] |
| B02 | false_alarm | - | [('REQ-031', 'missing'), ('REQ-033', 'missing'), ('-', 'out-of-spec')] |
| B03 | false_alarm | - | [('-', 'out-of-spec')] |
| B04 | false_alarm | - | [('REQ-030', 'missing'), ('-', 'out-of-spec')] |
| B05 | false_alarm | - | [('-', 'out-of-spec')] |
