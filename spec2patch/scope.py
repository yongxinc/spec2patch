"""機械式範圍判斷:這份 diff 實際碰到哪些需求。不呼叫 LLM。

一條需求的 `Code:` 錨點是 (檔案, 符號, 行號範圍)。diff 的某一行變更「碰到」該需求,當且僅當:
  - 變更所在檔案 = 錨點檔案,且
  - (a) 變更行的文字含錨點符號(整字比對),或
    (b) 變更行位於名稱等於錨點符號的 def/class 之內,或
    (c) 變更行的舊檔或新檔行號落在錨點的行號範圍內。
純空白與純註解行不算碰到(它們不可能改變行為)。沒有 `Code:` 的需求無法判斷,一律視為被碰到。
"""
import re


def _norm(path: str) -> str:
    for prefix in ("a/", "b/", "./"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path


def _same_file(diff_file: str, anchor_file: str) -> bool:
    d, a = _norm(diff_file), _norm(anchor_file)
    return d == a or d.endswith("/" + a)


def is_trivial(text: str) -> bool:
    s = text.strip()
    return not s or s.startswith(("#", "//"))


def _hits(change: dict, anchor: dict) -> str | None:
    for sym in anchor["symbols"]:
        if re.search(rf"(?<![\w]){re.escape(sym)}(?![\w])", change["text"]):
            return f"符號 {sym} 出現在變更行"
        if change["enclosing"] == sym:
            return f"變更位於 {sym} 之內"
    for lo, hi in anchor["ranges"]:
        for n in (change["old"], change["new"]):
            if n is not None and lo <= n <= hi:
                return f"行號 {n} 在 {lo}-{hi} 內"
    if not anchor["symbols"] and not anchor["ranges"]:
        return "該檔有變更"
    return None


def scope(requirements: list[dict], diff_files: list[dict]) -> dict:
    """回傳 {touched: {REQ: [觸發位置]}, scoped: {REQ: 是否有錨點}, unattributed: [未歸屬任何需求的變更]}。"""
    touched = {r["id"]: [] for r in requirements}
    scoped = {r["id"]: bool(r.get("anchors")) for r in requirements}
    attributed: set[tuple] = set()
    for f in diff_files:
        for h in f["hunks"]:
            for c in h["changes"]:
                if is_trivial(c["text"]):
                    continue
                for r in requirements:
                    for a in r.get("anchors", []):
                        if not _same_file(f["file"], a["file"]):
                            continue
                        why = _hits(c, a)
                        if why:
                            touched[r["id"]].append({"file": _norm(f["file"]), "side": "old" if c["sign"] == "-" else "new",
                                                     "line": c["old"] if c["sign"] == "-" else c["new"], "why": why})
                            attributed.add((f["file"], c["sign"], c["old"], c["new"]))
    unattributed = []
    for f in diff_files:
        for h in f["hunks"]:
            # 純空白行的增減不報(沒有內容可言);註解行會列為「與需求無關」,僅供參考
            rest = [c for c in h["changes"] if c["text"].strip()
                    and (f["file"], c["sign"], c["old"], c["new"]) not in attributed]
            if rest:
                unattributed.append({"file": _norm(f["file"]), "changes": rest})
    return {"touched": touched, "scoped": scoped, "unattributed": unattributed}
