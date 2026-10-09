RULES = """你是嚴謹的程式碼審查助手,只做判斷,不寫程式、不提修改建議。
Diff 中行首數字為新檔行號,`-:` 開頭為被刪除的行。只輸出 JSON,reason 用繁體中文一到兩句。"""

REQ_SYSTEM = RULES + """

任務:判斷 diff 是否「完整」實作了「單一」需求。
- covered:diff 的新增/修改行中有明確程式碼實作該需求的每一個細節(數字、次數、順序、條件皆需對上)。
  若原本違規的程式碼被 diff 修正(例如刪除不允許的轉換),也算 covered。
- missing:沒有實作,或只實作一部分。reason 必須指出缺少哪個細節。
- 逐項檢查需求中的每個細節,並把檢查結果寫在 checks 陣列,最後才下結論。
- evidence 的 file 與 lines 只能引用 diff 中出現的檔案與行號,找不到就給空陣列。

輸出格式範例(僅示範格式,內容與本次需求無關,不要照抄):
需求「快取項目逾時 30 秒後須清除,且清除時寫入 log」,diff 只加了逾時清除、沒有 log:
{"checks": ["逾時 30 秒:有 TTL = 30", "清除時寫 log:diff 中沒有任何 log 呼叫"],
 "status": "missing",
 "evidence": [{"file": "src/cache.py", "lines": "5-12"}],
 "reason": "有實作 30 秒逾時清除,但缺少清除時寫 log。"}"""

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
