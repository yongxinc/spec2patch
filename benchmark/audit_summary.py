"""Combine eval results with the manual reason audit: 'verdict correct AND reason holds'.

    python benchmark/audit_summary.py v2-llama3.1-8b-scoped v2-claude-sonnet-scoped
Fails if a true positive has no label, so the audit cannot silently go stale.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
audit = json.loads((HERE / "audit" / "reason_audit.json").read_text())

for run in sys.argv[1:]:
    rows = json.loads((HERE / "results" / run / "summary.json").read_text())["rows"]
    v = [r for r in rows if r["kind"] == "violation"]
    tps = [r["id"] for r in v if r["class"] == "TP"]
    labels = audit[run]
    missing = [t for t in tps if t not in labels]
    if missing:
        raise SystemExit(f"{run}: unlabeled true positives {missing}")
    n = {k: sum(labels[t][0] == k for t in tps) for k in ("holds", "partial", "unsupported")}
    extras = [r for r in v if r["class"] == "TP" and r["extra_flags"]]
    print(f"{run}: verdict-correct TP {len(tps)}/{len(v)} -> reason holds {n['holds']}, partial {n['partial']}, "
          f"unsupported {n['unsupported']}  =>  real TP {n['holds']}/{len(v)}")
    for t in tps:
        if labels[t][0] != "holds":
            print(f"    {t}: {labels[t][0]} - {labels[t][1]}")
