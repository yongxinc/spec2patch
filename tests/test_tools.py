from pathlib import Path

from spec2patch import graph, tools
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
            {"requirement": "REQ-001", "status": "covered", "evidence": [{"file": "a.py", "lines": [1, 2]}], "reason": "ok"},
            {"requirement": "REQ-999", "status": "covered", "reason": "x"},
            {"requirement": "REQ-002", "status": "bogus", "reason": "x"},
        ],
    }
    rep = graph.report(state)["report"]
    by = {f.requirement: f for f in rep.findings}
    assert by["REQ-001"].evidence[0].lines == "1, 2"
    assert by["REQ-002"].status == "missing"
    assert "REQ-999" not in by and rep.warnings


def test_llm_down_does_not_crash(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("down")
    monkeypatch.setattr(graph.llm, "chat_json", boom)
    rep = graph.run(str(ROOT / "specs/sprint-retry.md"), str(ROOT / "diffs/01-full-compliance.diff"))
    assert {f.requirement for f in rep.findings} == {"REQ-003", "REQ-004"}
    assert rep.warnings
