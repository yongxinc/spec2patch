# Benchmark: v2-claude-sonnet-scoped

backend=claude-cli model=sonnet spec2patch@912dcfd spec=case

- 真陽性 TP: **18/20**
- 部分正確: **0/20**
- 漏報: **0/20**
- 宣告上下文不足(abstain,目標條文): **2/20**(其中標準答案本來就需要上下文: 1)
- 假警報(嚴格): **0/5**
- 假警報(寬鬆): **0/5**
- 無害案例中出現上下文不足: 2/5
- TP 案例中同時多報非目標 flag: 3
- 目標被判違反但無 evidence(算漏報): 0
- 有 LLM 呼叫失敗的案例: 0
- 每案平均被機械式判為 not_applicable 的需求數: 3.0

| case | class | target status | flags | abstained |
| --- | --- | --- | --- | --- |
| V01 | TP | violated | [('REQ-003', 'violated')] | [] |
| V02 | TP | violated | [('REQ-005', 'violated')] | [] |
| V03 | TP | violated | [('REQ-003', 'violated')] | ['REQ-001', 'REQ-006'] |
| V04 | TP | violated | [('REQ-004', 'violated')] | [] |
| V05 | TP | violated | [('REQ-002', 'violated')] | ['REQ-001', 'REQ-006'] |
| V06 | TP | violated | [('REQ-007', 'violated')] | [] |
| V07 | TP | violated | [('REQ-009', 'violated')] | [] |
| V08 | TP | violated | [('REQ-008', 'violated')] | [] |
| V09 | TP | violated | [('REQ-010', 'violated')] | [] |
| V10 | TP | violated | [('REQ-011', 'violated')] | [] |
| V11 | TP | violated | [('REQ-013', 'violated'), ('REQ-018', 'violated')] | [] |
| V12 | TP | violated | [('REQ-017', 'violated')] | [] |
| V13 | TP | violated | [('REQ-015', 'violated')] | [] |
| V14 | TP | violated | [('REQ-019', 'violated')] | [] |
| V15 | TP | violated | [('REQ-031', 'violated'), ('REQ-033', 'violated')] | [] |
| V16 | TP | violated | [('REQ-032', 'violated'), ('REQ-033', 'violated')] | [] |
| V17 | TP | violated | [('REQ-034', 'violated')] | [] |
| V18 | TP | violated | [('REQ-037', 'violated')] | [] |
| V19 | abstain | insufficient_context | [] | ['REQ-038'] |
| V20 | abstain | insufficient_context | [] | ['REQ-030'] |
| B01 | clean | - | [] | ['REQ-005'] |
| B02 | clean | - | [] | [] |
| B03 | clean | - | [] | [] |
| B04 | clean | - | [] | ['REQ-029'] |
| B05 | clean | - | [] | [] |
