# Spec2Patch

讀一份規格 markdown 與一份 diff,輸出結構化的**落差分析**:這次改動涵蓋了哪些需求、漏了哪些、有沒有規格沒要求卻動到的地方。

**它不會改你的 code。** 沒有 `write_file` 工具,這是刻意的:自動產生的 patch 可靠度不足以放進真實流程,所以本工具定位成規格落差的審查輔助,把「規格說了什麼、改動做了什麼」攤開來對照,判斷留給人。

## 問題

Code review 時,reviewer 要自己在腦中對照「需求寫了 5 件事」與「diff 動了 8 個地方」。漏做一條(例如只做了重試、沒做退避)或夾帶規格外的改動,很容易看漏。

## 安裝與執行

需要 Python 3.10+,以及本機 [Ollama](https://ollama.com)(預設模型 `llama3.1:8b`)。

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.1:8b

python -m spec2patch demo-provisioning/specs/sprint-retry.md demo-provisioning/diffs/03-out-of-spec.diff
```

選項:`--format text|json|both`(預設 both)。環境變數:`SPEC2PATCH_MODEL`、`OLLAMA_URL`。

**實驗用後端(Claude)**:沒有 API key 也能用,改走本機 Claude Code CLI(使用 Claude 訂閱額度):

```bash
SPEC2PATCH_BACKEND=claude-cli SPEC2PATCH_MODEL=sonnet python -m spec2patch <規格> <diff>
```

這只是為了比較模型能力,不是正式的後端切換機制;需要本機已安裝並登入 `claude`,且每個 diff 會呼叫 (需求數 + 1) 次。
測試(不需要 Ollama):`pytest`。

## 完整範例

**規格**(`demo-provisioning/specs/sprint-retry.md`)

```markdown
## REQ-003 佈建重試
裝置在佈建階段無回應時,系統應重試最多三次,採指數退避（1s / 2s / 4s）。三次皆失敗則將狀態標記為 provision_failed 並寫入錯誤記錄。

## REQ-004 狀態轉換限制
已撤銷（revoked）的裝置不得直接轉為已佈建（provisioned）,須先回到待佈建（pending）。
```

**Diff**(`03-out-of-spec.diff` 節錄):`provisioning.py` 加入重試 + 退避 + log;`device_registry.py` 把 `REVOKED: {PENDING, PROVISIONED}` 改成 `{PENDING}`;**另外**新增 `metrics.py` 與 `api.list_devices`。

**實際輸出**(Claude Sonnet,文字部分;JSON 結構見下方 schema)

```text
✅ covered  REQ-003
    理由:diff 中明確實作了最多三次重試、1s/2s/4s 指數退避、失敗後轉換狀態至 provision_failed,以及 log.error 錯誤記錄。
✅ covered  REQ-004
    理由:diff 將 REVOKED 狀態的合法轉換目標從 {PENDING, PROVISIONED} 縮減為 {PENDING},完整實作了限制。
⚠️  out-of-spec  -
    理由:新增 list_devices 函式用於列出裝置清單,與兩項需求均無關。
⚠️  out-of-spec  -
    理由:新增計數統計模組,兩項需求均未要求。
```

同一個案例在本地 llama3.1:8b 上會把 REQ-004 誤判為 missing、漏掉 `list_devices`,見下方比較。

JSON schema(每一項):

```json
{"requirement": "REQ-003", "status": "covered | missing | out-of-spec",
 "evidence": [{"file": "src/provisioning.py", "lines": "1-23"}], "reason": "..."}
```

## 系統設計

LangGraph 四個節點,線性串接,全部唯讀:

```text
load_spec ──► load_diff ──► analyze ──► report
```

| 節點 | 做什麼 |
| --- | --- |
| `load_spec` | `read_file` + `list_requirements`,抓出 `## REQ-xxx` 條目 |
| `load_diff` | `read_file` + `parse_diff`,切出檔案、hunk 與新檔行號(行號直接標進 prompt,避免模型自己數) |
| `analyze` | 每條需求各呼叫一次 LLM(小模型一次判多條容易混淆),再一次找規格外改動 |
| `report` | 驗證 schema:丟棄未知編號、補上 LLM 漏回的需求(保守標 missing 並警告)、輸出 JSON 與文字 |

LLM 失敗(Ollama 沒開、回傳壞 JSON)時會重試一次,仍失敗則在 `warnings` 記錄,不會崩潰。

## 手動案例結果

規格 `sprint-retry.md`(REQ-003 重試退避、REQ-004 狀態限制),預期見 `demo-provisioning/cases.md`。以下為作者手動檢查,**沒有量化評估,只有 5 個案例,且 diff 與 prompt 都是同一人設計**,不能當作一般準確率:

| diff | 預期 | llama3.1:8b | Claude Sonnet |
| --- | --- | --- | --- |
| 01-full-compliance | 003 ✓ 004 ✓ | 003 ✓、**004 誤判 missing** | 符合 |
| 02-missing-backoff | 003 missing、004 ✓ | **003 判 covered(理由自己寫了「沒有時間間隔」)**、**004 誤判 missing** | 符合 |
| 03-out-of-spec | 兩條 ✓ + metrics/list_devices 規格外 | **004 誤判 missing**、漏 list_devices | 符合 |
| 04-violates-transition | 003 ✓、004 missing | 符合 | 符合 |
| 05-unrelated-change | 兩條 missing + 僅文件變更 | 符合 | 符合 |

結論:同一套流程與 prompt,換成較強的模型後 5 個案例都符合預期,8B 本地模型則約只有 2 個符合(04、05;其中 05 是因為兩條本來就沒被實作)。表示在這組案例上瓶頸主要是模型能力。8B 模型的典型錯誤是理由與結論自相矛盾,因此人工複核時要看理由,不能只看狀態。

過程中的一個發現:第一輪 Claude 判 REQ-003 為 missing,理由是「重試三次」應為首次 + 3 次重試共 4 次嘗試,而我的 demo 程式只嘗試 3 次——這是 demo 程式本身的 bug,不是誤判。已修正 demo 與 diff。

## 目前的限制

- 判斷完全依賴 LLM,對規格條目的理解可能出錯,如上表。
- 只處理單一規格文件對單一 diff,不掃整個 repo、不做多規格交叉比對。
- 沒有量化評估,所有案例都是手動檢查。
- 不處理跨檔案的隱含相依(diff 只呈現改動處,模型看不到未改動的相關程式碼)。
- 只支援本地 Ollama,沒有 API 後端與模型切換機制。
- 輸出的行號來自模型引用,可能不精確。
- 預設只給模型 diff,看不到修改後的完整檔案;Claude 版本在 demo 上夠用,但真實程式碼中容易因缺少上下文而誤判。
- 比較用的 Claude 後端依賴本機 `claude` CLI 與訂閱額度,不適合當作可重現的安裝方式。

## 未來可能的方向

- 在真實 repo 的 commit 上驗證。
- 提供改動檔案的完整上下文,並把需求拆到子要求層級逐項檢查。
- 加入量化評估與更多案例。

## 專案結構

```text
spec2patch/          CLI 與 LangGraph 流程(tools / graph / prompts / schema / llm / cli)
tests/               工具與容錯測試(不需 LLM)
demo-provisioning/   demo repo:規格、src、tests、5 個 diff 案例
```
