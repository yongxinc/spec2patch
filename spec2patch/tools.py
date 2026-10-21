"""agent 可用的工具。刻意沒有 write_file。"""
import re
from pathlib import Path

REQ_HEADING = re.compile(r"^#{1,6}\s*(REQ-\d+)\s*(.*)$")
FILE_HEADER = re.compile(r"^\+\+\+ (?:b/)?(\S+)")
HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
CODE_LINE = re.compile(r"^Code:\s*(.*)$")
DEF_RE = re.compile(r"^(?:async\s+)?(?:def|class)\s+(\w+)")


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _parse_anchors(spec: str) -> list[dict]:
    """`Code: a.py::f, CONST; b.py@10-20` → [{file, symbols, ranges}]。

    `file::sym1, sym2`:變更行含該符號,或變更行位於該函式/類別內,即算碰到。
    `file@a-b`:變更行(舊檔或新檔行號)落在 a-b 內即算碰到。只寫 `file` = 該檔任何變更都算。
    """
    anchors = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        ranges, symbols = [], []
        if "::" in part:
            part, syms = part.split("::", 1)
            symbols = [x.strip() for x in syms.split(",") if x.strip()]
        if "@" in part:
            part, rng = part.split("@", 1)
            for r in rng.split(","):
                lo, _, hi = r.strip().partition("-")
                if lo.strip().isdigit():
                    ranges.append((int(lo), int(hi or lo)))
        anchors.append({"file": part.strip(), "symbols": symbols, "ranges": ranges})
    return anchors


def list_requirements(spec_text: str) -> list[dict]:
    """從規格抓出編號條目:[{id, title, text, anchors}]。

    anchors 來自條目內的 `Code:` 行(可省略;沒有就代表這條無法做機械式範圍判斷)。
    `Code:` 行不會出現在 text 裡,不送進 LLM。
    """
    reqs, cur = [], None
    for line in spec_text.splitlines():
        m = REQ_HEADING.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(), "body": [], "anchors": []}
            reqs.append(cur)
        elif cur is not None:
            if line.startswith("#"):
                cur = None
                continue
            c = CODE_LINE.match(line.strip())
            if c:
                cur["anchors"].extend(_parse_anchors(c.group(1)))
            else:
                cur["body"].append(line)
    return [
        {"id": r["id"], "title": r["title"], "text": "\n".join(r["body"]).strip(), "anchors": r["anchors"]}
        for r in reqs
    ]


def _def_after(text: str, current: str | None) -> str | None:
    """追蹤目前所在的第 0 欄 def/class;遇到其他第 0 欄敘述就離開函式。"""
    m = DEF_RE.match(text)
    if m:
        return m.group(1)
    if text and not text[0].isspace() and text[0] not in "#)]}":
        return None
    return current


def parse_diff(diff_text: str) -> list[dict]:
    """切出改動的檔案與行:[{file, hunks:[{old_start, old_end, new_start, new_end, header, lines, changes}]}]。

    lines:放進 prompt 的片段。新增行/上下文行用新檔行號("12: +code"),
          刪除行用舊檔行號("12(old): -code"),讓刪除也有可引用的位置。
    changes:每一行 +/- 的結構化資料 {sign, old, new, text, enclosing},供機械式範圍判斷。
    enclosing 由 hunk 標頭(git 放在 @@ 後面的函式名)與可見的 def/class 行推得。
    """
    files, cur, hunk = [], None, None
    old_ln = new_ln = 0
    old_def = new_def = None
    for line in diff_text.splitlines():
        m = FILE_HEADER.match(line)
        if m:
            cur = {"file": m.group(1), "hunks": []}
            files.append(cur)
            hunk = None
            continue
        if line.startswith("--- ") and not hunk:
            continue
        m = HUNK_HEADER.match(line)
        if m and cur is not None:
            old_ln, new_ln = int(m.group(1)), int(m.group(3))
            header = m.group(5).strip()
            hm = DEF_RE.match(header)
            old_def = new_def = hm.group(1) if hm else None
            hunk = {"old_start": old_ln, "old_end": old_ln, "new_start": new_ln, "new_end": new_ln,
                    "header": header, "lines": [], "changes": []}
            cur["hunks"].append(hunk)
            continue
        if hunk is None:
            continue
        text = line[1:]
        if line.startswith("+"):
            new_def = _def_after(text, new_def)
            hunk["lines"].append(f"{new_ln}: {line}")
            hunk["changes"].append({"sign": "+", "old": None, "new": new_ln, "text": text, "enclosing": new_def})
            hunk["new_end"] = new_ln
            new_ln += 1
        elif line.startswith("-"):
            old_def = _def_after(text, old_def)
            hunk["lines"].append(f"{old_ln}(old): {line}")
            hunk["changes"].append({"sign": "-", "old": old_ln, "new": None, "text": text, "enclosing": old_def})
            hunk["old_end"] = old_ln
            old_ln += 1
        elif line.startswith(" "):
            old_def, new_def = _def_after(text, old_def), _def_after(text, new_def)
            hunk["lines"].append(f"{new_ln}:  {text}")
            old_ln += 1
            new_ln += 1
    return files


def render_diff(files: list[dict]) -> str:
    out = []
    for f in files:
        out.append(f"### {f['file']}")
        for h in f["hunks"]:
            out.append(f"@@ new lines {h['new_start']}-{h['new_end']} @@")
            out.extend(h["lines"])
    return "\n".join(out)
