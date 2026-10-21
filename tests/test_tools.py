from pathlib import Path

from spec2patch import graph, scope, tools
from spec2patch.schema import Finding

ROOT = Path(__file__).resolve().parent.parent / "demo-provisioning"


def test_list_requirements():
    reqs = tools.list_requirements((ROOT / "specs/device-provisioning.md").read_text())
    assert [r["id"] for r in reqs] == [f"REQ-00{i}" for i in range(1, 6)]
    assert "三次" in reqs[2]["text"]


def test_parse_diff_line_numbers():
    files = tools.parse_diff((ROOT / "diffs/03-out-of-spec.diff").read_text())
    names = [f["file"] for f in files]
    assert "src/metrics.py" in names and "src/provisioning.py" in names
    m = next(f for f in files if f["file"] == "src/metrics.py")
    assert (m["hunks"][0]["new_start"], m["hunks"][0]["new_end"]) == (1, 8)


def test_garbage_diff_does_not_crash():
    assert tools.parse_diff("not a diff at all\n\x00\x01") == []


def test_report_fills_missing_and_drops_unknown():
    state = {
        "spec_path": "s", "diff_path": "d",
        "requirements": [{"id": "REQ-001", "title": "", "text": ""},
                         {"id": "REQ-002", "title": "", "text": ""}],
        "raw_findings": [
            {"requirement": "REQ-001", "status": "covered", "evidence": [{"file": "a.py", "lines": [1, 2], "side": "OLD"}], "reason": "ok"},
            {"requirement": "REQ-999", "status": "covered", "reason": "x"},
            {"requirement": "REQ-002", "status": "bogus", "reason": "x"},
        ],
    }
    rep = graph.report(state)["report"]
    by = {f.requirement: f for f in rep.findings}
    assert by["REQ-001"].evidence[0].lines == "1, 2" and by["REQ-001"].evidence[0].side == "old"
    assert by["REQ-002"].status == "insufficient_context" and by["REQ-002"].needs
    assert "REQ-999" not in by and rep.warnings


def test_llm_down_does_not_crash(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("down")
    monkeypatch.setattr(graph.llm, "chat_json", boom)
    rep = graph.run(str(ROOT / "specs/sprint-retry.md"), str(ROOT / "diffs/01-full-compliance.diff"))
    assert {f.requirement for f in rep.findings} - {"-"} == {"REQ-003", "REQ-004"}  # "-": unrelated changes (imports)
    assert all(f.status == "insufficient_context" for f in rep.findings if f.requirement != "-")
    assert rep.warnings


DELETION = """diff --git a/ue/auth.py b/ue/auth.py
--- a/ue/auth.py
+++ b/ue/auth.py
@@ -64,7 +64,3 @@ def authenticate(k, opc, rand, autn):
     sqn = 1
-    if separation_bit(amf) != 1:
-        raise AmfSeparationBitNotSet("x")
-
     res = 2
"""


def test_parse_diff_gives_deleted_lines_old_positions_and_enclosing_function():
    (f,) = tools.parse_diff(DELETION)
    h = f["hunks"][0]
    assert [c["old"] for c in h["changes"] if c["sign"] == "-"] == [65, 66, 67]
    assert all(c["enclosing"] == "authenticate" for c in h["changes"])
    assert "65(old): -    if separation_bit(amf) != 1:" in h["lines"]
    assert h["new_end"] >= h["new_start"]


def test_requirement_code_anchors_are_parsed_and_hidden_from_the_prompt_text():
    reqs = tools.list_requirements("## REQ-001 t\nbody\nCode: a.py::f, G; b.py@3-9; c.py\n")
    assert "Code:" not in reqs[0]["text"]
    assert reqs[0]["anchors"] == [{"file": "a.py", "symbols": ["f", "G"], "ranges": []},
                                  {"file": "b.py", "symbols": [], "ranges": [(3, 9)]},
                                  {"file": "c.py", "symbols": [], "ranges": []}]


def test_scope_by_symbol_enclosing_function_and_line_range():
    reqs = tools.list_requirements(
        "## REQ-001 a\nx\nCode: ue/auth.py::separation_bit\n"
        "## REQ-002 b\nx\nCode: ue/auth.py::authenticate\n"
        "## REQ-003 c\nx\nCode: ue/auth.py@66-66\n"
        "## REQ-004 d\nx\nCode: other.py::authenticate\n"
        "## REQ-005 e\nx\nCode: ue/auth.py::unrelated_symbol\n")
    t = scope.scope(reqs, tools.parse_diff(DELETION))["touched"]
    assert t["REQ-001"] and t["REQ-002"] and t["REQ-003"]   # symbol in line / enclosing def / old line number
    assert not t["REQ-004"] and not t["REQ-005"]            # other file / untouched symbol
    assert t["REQ-001"][0]["side"] == "old"


def test_comment_only_change_touches_nothing():
    d = DELETION.replace("-    if separation_bit(amf) != 1:", "+    # explain").replace("-        raise AmfSeparationBitNotSet(\"x\")\n", "").replace("-\n", "")
    reqs = tools.list_requirements("## REQ-001 a\nx\nCode: ue/auth.py::authenticate\n")
    sc = scope.scope(reqs, tools.parse_diff(d))
    assert not sc["touched"]["REQ-001"] and sc["unattributed"]


def test_untouched_requirements_never_reach_the_llm(monkeypatch, tmp_path):
    spec = tmp_path / "s.md"
    spec.write_text("## REQ-001 a\nx\nCode: ue/auth.py::separation_bit\n## REQ-002 b\nx\nCode: elsewhere.py::g\n")
    diff = tmp_path / "d.diff"
    diff.write_text(DELETION)
    asked = []

    def fake(system, user):
        asked.append(user)
        return '{"verdict": "violates", "evidence": [{"file": "ue/auth.py", "lines": "65", "side": "old"}], "reason": "removed", "needs": ""}'
    monkeypatch.setattr(graph.llm, "chat_json", fake)
    rep = graph.run(str(spec), str(diff))
    by = {f.requirement: f for f in rep.findings}
    assert len(asked) == 1 and "REQ-001" in asked[0]
    assert by["REQ-001"].status == "violated" and by["REQ-001"].evidence[0].side == "old"
    assert by["REQ-002"].status == "not_applicable"


def test_insufficient_context_verdict_is_kept_not_guessed(monkeypatch, tmp_path):
    spec = tmp_path / "s.md"
    spec.write_text("## REQ-001 a\nx\nCode: ue/auth.py::authenticate\n")
    diff = tmp_path / "d.diff"
    diff.write_text(DELETION)
    monkeypatch.setattr(graph.llm, "chat_json", lambda s, u: '{"verdict": "insufficient_context", "needs": "definition of foo", "reason": "r"}')
    (f,) = graph.run(str(spec), str(diff)).findings
    assert f.status == "insufficient_context" and f.needs == "definition of foo"
