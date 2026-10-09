"""agent 可用的工具。刻意沒有 write_file。"""
import re
from pathlib import Path

REQ_HEADING = re.compile(r"^#{1,6}\s*(REQ-\d+)\s*(.*)$")
FILE_HEADER = re.compile(r"^\+\+\+ (?:b/)?(\S+)")
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def read_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def list_requirements(spec_text: str) -> list[dict]:
    """從規格抓出編號條目:[{id, title, text}]。"""
    reqs, cur = [], None
    for line in spec_text.splitlines():
        m = REQ_HEADING.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2).strip(), "body": []}
            reqs.append(cur)
        elif cur is not None:
            if line.startswith("#"):
                cur = None
            else:
                cur["body"].append(line)
    return [
        {"id": r["id"], "title": r["title"], "text": "\n".join(r["body"]).strip()}
        for r in reqs
    ]


def parse_diff(diff_text: str) -> list[dict]:
    """切出改動的檔案與行:[{file, hunks:[{new_start, new_end, lines}]}]。

    lines 是帶新檔行號的片段("12: +code" / "- : -code"),直接放進 prompt。
    """
    files, cur, hunk, new_ln = [], None, None, 0
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
            new_ln = int(m.group(1))
            hunk = {"new_start": new_ln, "new_end": new_ln, "lines": []}
            cur["hunks"].append(hunk)
            continue
        if hunk is None:
            continue
        if line.startswith("+"):
            hunk["lines"].append(f"{new_ln}: {line}")
            hunk["new_end"] = new_ln
            new_ln += 1
        elif line.startswith("-"):
            hunk["lines"].append(f"-: {line}")
        elif line.startswith(" "):
            hunk["lines"].append(f"{new_ln}:  {line[1:]}")
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
