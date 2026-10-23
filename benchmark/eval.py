"""Run Spec2Patch on every benchmark case and score it. Scoring rules: benchmark/README.md."""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # repo root; paths written into the results are relative to it
sys.path.insert(0, str(HERE.parent))


def _norm(path: str) -> str:
    path = path.strip()
    for prefix in ("a/", "b/", "./"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path


# 舊 schema(missing)與新 schema(violated)都算「判定違反」,這樣修正前的結果可用同一支腳本重新評分。
VIOLATION_STATUSES = ("violated", "missing")


def flags(findings: list[dict], changed_files: list[str]) -> list[dict]:
    """A finding is a flag if it is out-of-spec, or a violation verdict with evidence inside the changed files.

    Evidence may point at the pre-change position (side = "old") for deleted code; only the file is checked.
    """
    changed = {_norm(f) for f in changed_files}
    out = []
    for f in findings:
        if f["status"] == "out-of-spec":
            out.append(f)
        elif f["status"] in VIOLATION_STATUSES and any(_norm(e["file"]) in changed for e in f.get("evidence", [])):
            out.append(f)
    return out


def classify(meta: dict, findings: list[dict], warnings: list[str] | None = None) -> dict:
    fl = flags(findings, meta["files"])
    abstained = [f["requirement"] for f in findings if f["status"] == "insufficient_context"]
    res = {"id": meta["id"], "kind": meta["kind"], "n_flags": len(fl),
           "flagged": [(f["requirement"], f["status"]) for f in fl],
           "abstained": abstained,
           "n_not_applicable": sum(f["status"] == "not_applicable" for f in findings),
           "llm_failures": sum("判斷失敗" in w for w in (warnings or []))}
    if meta["kind"] == "violation":
        target = meta["target_req"]
        tf = [f for f in findings if f["requirement"] == target]
        hit = any(f in fl for f in tf)
        res["target_status"] = tf[0]["status"] if tf else None
        res["target_missing_no_evidence"] = bool(tf) and tf[0]["status"] in VIOLATION_STATUSES and not hit
        res["extra_flags"] = len([f for f in fl if f["requirement"] != target])
        if hit:
            res["class"] = "TP"
        elif res["target_status"] == "insufficient_context":
            res["class"] = "abstain"  # 目標條文上宣告上下文不足:不是猜測,但也沒抓到
            res["abstain_expected"] = bool(meta.get("needs_context"))
        else:
            res["class"] = "partial" if fl else "miss"
    else:
        strict = bool(fl)
        lenient = any(f["status"] in VIOLATION_STATUSES for f in fl)
        res["class"] = "false_alarm" if strict else "clean"
        res["false_alarm_strict"], res["false_alarm_lenient"] = strict, lenient
    return res


def summarize(rows: list[dict]) -> dict:
    v = [r for r in rows if r["kind"] == "violation"]
    b = [r for r in rows if r["kind"] == "benign"]
    n = lambda rs, c: sum(r["class"] == c for r in rs)  # noqa: E731
    return {
        "violations": len(v), "TP": n(v, "TP"), "partial": n(v, "partial"), "miss": n(v, "miss"),
        "abstain": n(v, "abstain"),
        "abstain_expected": sum(1 for r in v if r["class"] == "abstain" and r.get("abstain_expected")),
        "benign": len(b), "false_alarm_strict": sum(r["false_alarm_strict"] for r in b),
        "false_alarm_lenient": sum(r["false_alarm_lenient"] for r in b),
        "benign_with_abstain": sum(1 for r in b if r["abstained"]),
        "tp_with_extra_flags": sum(1 for r in v if r["class"] == "TP" and r["extra_flags"]),
        "target_missing_no_evidence": sum(r.get("target_missing_no_evidence", False) for r in v),
        "cases_with_llm_failures": sum(1 for r in rows if r["llm_failures"]),
        "avg_not_applicable": round(sum(r["n_not_applicable"] for r in rows) / max(len(rows), 1), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="results/<name>/ output directory")
    ap.add_argument("--only", help="comma separated case ids, for debugging")
    ap.add_argument("--spec", choices=["case", "full"], default="case",
                    help="case: the per-case scoped spec.md (default); full: the whole 38-requirement spec, scoping done by the tool")
    args = ap.parse_args()

    os.chdir(ROOT)  # so that relative paths resolve and no absolute path leaks into results/
    from spec2patch import graph, llm  # imported late: backend env vars are read at import time

    manifest = json.loads((HERE / "cases" / "manifest.json").read_text())
    only = set(args.only.split(",")) if args.only else None
    out_dir = HERE / "results" / args.name
    out_dir.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True).stdout.strip()
    rows = []
    for meta in manifest:
        if only and meta["id"] not in only:
            continue
        d = next((HERE / "cases").glob(f"{meta['id']}-*"))
        t0 = time.time()
        spec_path = d / "spec.md" if args.spec == "case" else HERE / "requirements" / "ts33501-subset.md"
        report = graph.run(str(spec_path.relative_to(ROOT)), str((d / "change.diff").relative_to(ROOT)))
        findings = [f.model_dump() for f in report.findings]
        row = classify(meta, findings, report.warnings)
        row["seconds"] = round(time.time() - t0, 1)
        rows.append(row)
        (out_dir / f"{d.name}.json").write_text(json.dumps(
            {"meta": meta, "result": row, "report": report.model_dump()}, ensure_ascii=False, indent=2))
        print(f"{d.name:44s} {row['class']:11s} flags={row['flagged']} ({row['seconds']}s)", flush=True)

    summary = summarize(rows)
    summary["config"] = {"backend": llm.BACKEND, "model": llm.MODEL, "spec2patch_commit": commit}
    (out_dir / "summary.json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2))
    s = summary
    md = [f"# Benchmark: {args.name}", "",
          f"backend={llm.BACKEND} model={llm.MODEL} spec2patch@{commit} spec={args.spec}", "",
          f"- 真陽性 TP: **{s['TP']}/{s['violations']}**",
          f"- 部分正確: **{s['partial']}/{s['violations']}**",
          f"- 漏報: **{s['miss']}/{s['violations']}**",
          f"- 宣告上下文不足(abstain,目標條文): **{s['abstain']}/{s['violations']}**(其中標準答案本來就需要上下文: {s['abstain_expected']})",
          f"- 假警報(嚴格): **{s['false_alarm_strict']}/{s['benign']}**",
          f"- 假警報(寬鬆): **{s['false_alarm_lenient']}/{s['benign']}**",
          f"- 無害案例中出現上下文不足: {s['benign_with_abstain']}/{s['benign']}",
          f"- TP 案例中同時多報非目標 flag: {s['tp_with_extra_flags']}",
          f"- 目標被判違反但無 evidence(算漏報): {s['target_missing_no_evidence']}",
          f"- 有 LLM 呼叫失敗的案例: {s['cases_with_llm_failures']}",
          f"- 每案平均被機械式判為 not_applicable 的需求數: {s['avg_not_applicable']}", "",
          "| case | class | target status | flags | abstained |", "| --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['id']} | {r['class']} | {r.get('target_status', '-')} | {r['flagged']} | {r['abstained']} |")
    (out_dir / "summary.md").write_text("\n".join(md) + "\n")
    print("\n" + "\n".join(md[:17]))


if __name__ == "__main__":
    main()
