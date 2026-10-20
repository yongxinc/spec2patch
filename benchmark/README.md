# Spec2Patch benchmark: seeded spec violations in a 5G reference implementation

目的:量化 Spec2Patch 對「diff 違反規格」的判斷品質。**這份文件的評分規則在跑任何結果之前就定好了,不依結果調整。**

## 測試資料

- 被測程式:`5Gproject`(依 3GPP Rel-17 實作的 SUCI 與 5G-AKA 參考實作),commit `4f8f2b6`。
- 規格:`requirements/ts33501-subset.md`,38 條編號需求,由我依該專案原始碼所引用的條文改寫(**不是 3GPP 原文**,條次引用需對照 Rel-17 核對)。
- 25 個案例(`cases/`):
  - `V01`–`V20`:各在一處破壞一條規格(單一、明確、可對應到一條 REQ)。
  - `B01`–`B05`:行為不變的修改(改名、加註解、重構),不該被報出問題。
- 每個案例包含 `change.diff`(`git` 風格 unified diff,3 行上下文)、`spec.md`、`meta.json`(標準答案)。
- **規格範圍**:每個案例的 `spec.md` 只含「被改動檔案」所負責的需求(`scope.json`,機械式對應,非逐案手挑)。原因:Spec2Patch 的語意是「這份 diff 實作了哪些需求」,若把 38 條全給它,沒被碰到的需求一律會被標 missing,雜訊會淹沒訊號。這代表每個案例有 1–8 條需求,其中只有 `target_req` 是標準答案,其餘是同檔案的干擾項。V06 只有 1 條(無干擾項)。
- 標準答案的可信度:`build_cases.py` 對每個變更跑 5G 專案自己的 399 個測試。`meta.json` 的 `upstream_tests_failed` 記錄失敗數,**19/20 個違規被上游測試抓到,V15(SQN 與 MAC 檢查順序)沒有**,它的違規認定只靠 TS 33.102 6.3.3 的文字。5 個無害修改全部通過 399 個測試。

重建:`python benchmark/build_cases.py /path/to/5Gproject`(只用 `git archive` 讀取,不會改動該 repo)。

## 評分規則(預先定義)

Spec2Patch 對每條需求輸出 `covered / missing / out-of-spec`,並附 evidence(檔案與行號)。它的語意是「這份 diff 有沒有正確實作這條需求」,所以把「違規」對應成:**目標需求被判為 `missing`,且有指到被改動的程式碼**。

定義 **flag** = 一筆 finding 滿足下列之一:
- `status = missing` 且 `evidence` 至少一筆,其 `file` 是該案例 diff 改動的檔案;
- `status = out-of-spec`(不論 evidence)。

(`missing` 但沒有 evidence 視為「這份 diff 沒碰到這條」,不算 flag。)

**違規案例 V01–V20**
| 分類 | 條件 |
| --- | --- |
| 真陽性 TP | 目標 REQ 的 finding 是 `missing` 且有 evidence 指到被改動的檔案 |
| 部分正確 | 不是 TP,但至少有一個 flag(指到別條 REQ,或 out-of-spec) |
| 漏報 | 沒有任何 flag(含:目標被判 covered、目標被判 missing 但無 evidence、LLM 呼叫失敗) |

**無害案例 B01–B05**
| 分類 | 條件 |
| --- | --- |
| 假警報(嚴格) | 有任何 flag(含 out-of-spec) |
| 假警報(寬鬆) | 有任何 `missing` 且有 evidence 的 flag(不計 out-of-spec) |
| 正確沉默 | 無 flag |

另外記錄(不影響分類):TP 案例中同時多報了幾個非目標 flag(精準度);LLM 呼叫失敗次數;`missing` 無 evidence 的目標。

主要數字:**Recall = TP/20**、**部分正確 = x/20**、**漏報 = x/20**、**假警報率(嚴格/寬鬆)= x/5**。

## 已知限制

- 只有 25 個案例,且違規由同一人設計,不是隨機抽樣,不能外推到一般 PR。
- 違規都是單行/單區塊的「小而明確」修改,diff 的上下文只有 3 行;真實 PR 更大更雜。
- 標準答案只標一條 REQ;有些修改嚴格說也可能同時違反鄰近條目(例如 V14 的順序問題)。
- 規格是我改寫的,不是 3GPP 原文;若改寫有誤,錯在標準答案而非工具。
- 每個案例只跑一次(Ollama 溫度 0,但仍未驗證可重現性)。

## 執行

```bash
python benchmark/eval.py --name baseline-llama3.1-8b          # 預設後端(Ollama)
```

結果寫入 `results/<name>/`:每案例的原始 JSON、`summary.json`、`summary.md`。
