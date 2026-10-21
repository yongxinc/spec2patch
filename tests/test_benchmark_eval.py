"""Scoring logic of benchmark/eval.py (the numbers are only as trustworthy as this)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmark"))
from eval import classify, summarize  # noqa: E402

V = {"id": "V01", "kind": "violation", "files": ["crypto/kdf.py"], "target_req": "REQ-003"}
B = {"id": "B01", "kind": "benign", "files": ["crypto/kdf.py"], "target_req": None}


def f(req, status, file=None, side="new"):
    return {"requirement": req, "status": status, "evidence": [{"file": file, "lines": "1", "side": side}] if file else [], "reason": ""}


def test_tp_requires_missing_with_evidence_in_changed_file():
    assert classify(V, [f("REQ-003", "missing", "b/crypto/kdf.py")])["class"] == "TP"
    assert classify(V, [f("REQ-003", "missing", "other.py")])["class"] == "miss"
    assert classify(V, [f("REQ-003", "missing")])["class"] == "miss"  # untouched, no location
    assert classify(V, [f("REQ-003", "covered", "crypto/kdf.py")])["class"] == "miss"


def test_partial_when_only_wrong_requirement_flagged():
    r = classify(V, [f("REQ-003", "covered", "crypto/kdf.py"), f("REQ-004", "missing", "crypto/kdf.py")])
    assert r["class"] == "partial"
    assert classify(V, [f("-", "out-of-spec", "crypto/kdf.py")])["class"] == "partial"


def test_tp_counts_extra_flags():
    r = classify(V, [f("REQ-003", "missing", "crypto/kdf.py"), f("REQ-004", "missing", "crypto/kdf.py")])
    assert r["class"] == "TP" and r["extra_flags"] == 1


def test_benign_strict_vs_lenient():
    clean = classify(B, [f("REQ-001", "covered", "crypto/kdf.py"), f("REQ-002", "missing")])
    assert clean["class"] == "clean"
    oos = classify(B, [f("-", "out-of-spec", "crypto/kdf.py")])
    assert oos["false_alarm_strict"] and not oos["false_alarm_lenient"]
    miss = classify(B, [f("REQ-001", "missing", "crypto/kdf.py")])
    assert miss["false_alarm_strict"] and miss["false_alarm_lenient"]


def test_summarize():
    rows = [classify(V, [f("REQ-003", "missing", "crypto/kdf.py")]), classify(V, []), classify(B, [])]
    s = summarize(rows)
    assert (s["TP"], s["miss"], s["partial"], s["false_alarm_strict"]) == (1, 1, 0, 0)


def test_unrelated_is_not_a_flag():
    assert classify(B, [f("-", "unrelated", "crypto/kdf.py")])["class"] == "clean"
    assert classify(V, [f("-", "unrelated", "crypto/kdf.py")])["class"] == "miss"


def test_violated_counts_like_legacy_missing_and_old_side_evidence_is_valid():
    # deletion-type violation: the only addressable position is the pre-change one
    r = classify(V, [f("REQ-003", "violated", "crypto/kdf.py", side="old")])
    assert r["class"] == "TP"
    assert classify(V, [f("REQ-003", "missing", "crypto/kdf.py")])["class"] == "TP"  # old results re-score identically
    assert classify(V, [f("REQ-003", "violated")])["class"] == "miss"                 # still needs a location


def test_insufficient_context_is_neither_hit_nor_false_alarm():
    r = classify({**V, "needs_context": True}, [{**f("REQ-003", "insufficient_context"), "needs": "foo"}])
    assert r["class"] == "abstain" and r["abstain_expected"]
    b = classify(B, [f("REQ-001", "insufficient_context"), f("REQ-002", "not_applicable")])
    assert b["class"] == "clean" and b["abstained"] == ["REQ-001"] and b["n_not_applicable"] == 1
    s = summarize([r, b])
    assert s["abstain"] == 1 and s["benign_with_abstain"] == 1
