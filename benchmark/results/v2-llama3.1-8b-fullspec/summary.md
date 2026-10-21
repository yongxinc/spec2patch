# Benchmark: v2-llama3.1-8b-fullspec

backend=ollama model=llama3.1:8b spec2patch@b9fed82 spec=full

- 真陽性 TP: **10/20**
- 部分正確: **1/20**
- 漏報: **9/20**
- 宣告上下文不足(abstain,目標條文): **0/20**(其中標準答案本來就需要上下文: 0)
- 假警報(嚴格): **1/5**
- 假警報(寬鬆): **1/5**
- 無害案例中出現上下文不足: 0/5
- TP 案例中同時多報非目標 flag: 3
- 目標被判違反但無 evidence(算漏報): 0
- 有 LLM 呼叫失敗的案例: 0
- 每案平均被機械式判為 not_applicable 的需求數: 36.5

| case | class | target status | flags | abstained |
| --- | --- | --- | --- | --- |
| V01 | miss | covered | [] | [] |
| V02 | TP | violated | [('REQ-005', 'violated')] | [] |
| V03 | partial | covered | [('REQ-001', 'violated')] | [] |
| V04 | miss | covered | [] | [] |
| V05 | TP | violated | [('REQ-001', 'violated'), ('REQ-002', 'violated')] | [] |
| V06 | TP | violated | [('REQ-007', 'violated')] | [] |
| V07 | miss | covered | [] | [] |
| V08 | miss | covered | [] | [] |
| V09 | TP | violated | [('REQ-010', 'violated')] | [] |
| V10 | TP | violated | [('REQ-011', 'violated')] | [] |
| V11 | TP | violated | [('REQ-013', 'violated'), ('REQ-018', 'violated')] | [] |
| V12 | miss | covered | [] | [] |
| V13 | TP | violated | [('REQ-014', 'violated'), ('REQ-015', 'violated')] | [] |
| V14 | TP | violated | [('REQ-019', 'violated')] | [] |
| V15 | TP | violated | [('REQ-033', 'violated')] | [] |
| V16 | miss | covered | [] | [] |
| V17 | miss | covered | [] | [] |
| V18 | miss | covered | [] | [] |
| V19 | TP | violated | [('REQ-038', 'violated')] | [] |
| V20 | miss | covered | [] | [] |
| B01 | clean | - | [] | [] |
| B02 | clean | - | [] | [] |
| B03 | clean | - | [] | [] |
| B04 | clean | - | [] | [] |
| B05 | false_alarm | - | [('REQ-007', 'violated')] | [] |
