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

## 變更紀錄

- **schema 修正(baseline 之後)**:原本 Spec2Patch 把「與任何需求無關的改動」標成 `out-of-spec`,導致重構、改名、註解也被當成違規。現在拆成兩個獨立狀態:`out-of-spec`(違反規格)與 `unrelated`(與需求無關,不是違規)。分析流程目前只會產生 `unrelated`;prompt 的判準沒有改。**評分規則沒有改**:flag 仍然只有 `out-of-spec` 與「有 evidence 的 missing」,所以 `unrelated` 不算 flag。`baseline-llama3.1-8b/` 是修正前的結果,`llama3.1-8b-split-schema/` 是修正後。

## v2:機械式範圍限縮 + 上下文不足(預先登記,先於結果)

**設計變更(Spec2Patch 本體)**
1. 規格每條需求可帶 `Code: 檔案::符號, ...; 檔案@起-迄` 錨點(「需求 → 實作位置」對照表,不送進 LLM)。新節點 `scope` 用程式判斷 diff 碰到哪些需求:變更行含錨點符號、或位於該 def/class 之內、或行號落在錨點範圍內(純空白、純註解行不算碰到)。沒碰到的需求直接標 `not_applicable`,**不呼叫 LLM**;沒有錨點的需求無法判斷,一律詢問(向下相容)。
2. 對被碰到的需求,問題改成「這個改動**違反**還是**滿足**這條需求」(`violated` / `covered`),不再問「有沒有實作」。
3. 新增獨立狀態 `insufficient_context`:判斷需要 diff 以外的程式碼時,輸出「需要什麼」(`needs`),不猜。
4. 所有需求都有錨點時,「與需求無關的改動」由程式判定(未歸屬任何需求的變更),不再問 LLM。
5. 為了讓機械判斷能知道變更行屬於哪個函式,案例的 `change.diff` 改用 git 預設的 hunk 標頭(`@@ ... @@ def foo(...)`)。**除了 `@@` 後面多了函式名,diff 內容與 v1 逐行相同**(已檢查),送給 LLM 的片段也不含這個標頭。

**錨點是我寫的**,依「每條需求由哪個函式/識別字負責」決定(`requirements/ts33501-subset.md` 的 `Code:` 行),寫在看任何 v2 結果之前,commit 之後不再改。範圍限縮的好處有一部分取決於錨點品質,這是此結果最大的內部效度風險。

**評分規則(相對於 v1 的唯一差異)**
- 「判定違反」同時接受舊狀態 `missing` 與新狀態 `violated`,所以 v1 的結果能用同一支腳本重新評分(結果與當時相同)。
- flag 的定義不變:`out-of-spec`,或「判定違反且 evidence 指到被改動的檔案」。`insufficient_context`、`not_applicable`、`unrelated`、`covered` 都不是 flag。
- 新分類 **abstain**(違規案例中,目標條文被標為 `insufficient_context`):不算 TP、不算漏報(沒有猜錯),單獨列出。`meta.json` 的 `needs_context` 標記「標準答案本來就需要 diff 以外的資訊」的案例(只有 V19:diff 看不到 `derive_hres_star` 的參數順序;此標記在 v1 Claude 結果出爐後、v2 執行前加入)。abstain 在這種案例是「該有的行為」,在其他案例是「不必要的棄權」。
- 無害案例上出現 `insufficient_context` 不算假警報,但另外列出(代表要人看的負擔)。
- **主要比較**:同一組 25 個案例、同一份每案例 `spec.md`、同一個模型(Ollama llama3.1:8b),比 `llama3.1-8b-split-schema`(v1)與 v2。補充執行:`--spec full` 把完整 38 條需求交給工具,範圍限縮完全由工具負責。

**修正的評分盲點:刪除型違規**
- 症狀:v1 的 Claude 在 V17(移除 separation bit 檢查)把目標條文判對(missing),但依規則被算成漏報。
- 原因:被刪掉的程式碼沒有新檔行號。v1 的 diff 片段把刪除行顯示為 `-: -code`,prompt 又要求引用「新檔行號」,所以模型只能給 `evidence: []`;規則要求 evidence 指到被改動的檔案,於是正確的判斷被判成沒指到。規則本身的意圖(判斷必須指向 diff 裡的程式碼)沒有錯,錯在 evidence 的座標系統無法表示「被刪除的程式碼」。
- 修法:(1) 刪除行改顯示變更前的行號(`65(old): -code`),`Evidence` 新增 `side: new|old`,刪除行用 `old`;(2) 評分規則明文接受 `old` 側 evidence(仍只檢查檔案是否在被改動的檔案內,沒有加嚴);(3) 單元測試涵蓋「只有舊側 evidence 的刪除型 TP」與「完全沒有 evidence 仍算漏報」。
- 沒做的事:v1 的 Claude V17 結果無法重新評分(它的 evidence 是空的),要驗證只能重跑;依指示這次沒有跑 Claude。
