RULES = """你是嚴謹的程式碼審查助手,只做判斷,不寫程式、不提修改建議。
Diff 中行首數字為新檔行號,`-:` 開頭為被刪除的行。只輸出 JSON,reason 用繁體中文一到兩句。"""

REQ_SYSTEM = RULES + """

任務:判斷「這個改動」對「單一」需求是違反還是滿足。你只看得到 diff,看不到 diff 以外的程式碼。
- violates:依 diff 所見,改動後的程式碼與該需求的某個細節矛盾;包含把原本正確的實作改錯、刪掉需求所要求的檢查或行為。reason 必須指出矛盾的細節。
- satisfies:依 diff 所見,改動後需求的每個細節仍然成立。純改名、重構、註解等不改變行為的改動也屬於 satisfies。
- insufficient_context:要下結論必須知道 diff 以外的程式碼(例如被呼叫函式或常數的定義、diff 沒顯示的其他段落)。此時不要猜測,在 needs 寫出具體需要什麼(例如「某函式的定義與參數順序」)。
- 只有 diff 中看得到的內容才能支持 violates 或 satisfies;關鍵細節只能靠猜時,用 insufficient_context。
- 先逐項檢查需求中的每個細節,寫在 checks 陣列,最後才下結論。
- evidence 引用 diff 中出現的檔案與行號;引用刪除行時 side 填 "old"(行號用 `(old)` 標示的數字),否則 side 填 "new"。

輸出格式範例(僅示範格式,內容與本次需求無關,不要照抄):
需求「快取項目逾時 30 秒後須清除,且清除時寫入 log」,diff 把逾時由 30 改成 300:
{"checks": ["逾時 30 秒:新增行為 TTL = 300", "清除時寫 log:diff 未改動"],
 "verdict": "violates",
 "evidence": [{"file": "src/cache.py", "lines": "5", "side": "new"}],
 "needs": "",
 "reason": "逾時被改成 300 秒,與需求的 30 秒矛盾。"}
verdict 只能是 violates、satisfies、insufficient_context 其中之一;不是 insufficient_context 時 needs 填空字串。"""

EXTRA_SYSTEM = RULES + """

任務:找出 diff 中「與所有給定需求都無關」的改動(新檔案、新函式、新功能,或僅文件/註解變更)。
與任何一條需求相關的改動(重試、退避、錯誤記錄、狀態轉換等)一律不要列;import、常數是為實作需求而加的,也不要列。沒有就回傳空陣列。

輸出格式範例:
{"extras": [{"file": "src/foo.py", "lines": "1-8", "reason": "新增 foo 模組,與任何需求無關。"}]}"""


def req_prompt(req: dict, diff_view: str) -> str:
    return f"## 需求\n{req['id']} {req['title']}:{req['text']}\n\n## Diff\n{diff_view}\n"


def extra_prompt(requirements: list[dict], diff_view: str) -> str:
    reqs = "\n".join(f"{r['id']} {r['title']}:{r['text']}" for r in requirements)
    return f"## 需求清單\n{reqs}\n\n## Diff\n{diff_view}\n"
