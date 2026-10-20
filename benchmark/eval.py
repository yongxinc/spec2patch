"""Run Spec2Patch on every benchmark case and score it. Scoring rules: benchmark/README.md."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))


def _norm(path: str) -> str:
    path = path.strip()
    for prefix in ("a/", "b/", "./"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path


def flags(findings: list[dict], changed_files: list[str]) -> list[dict]:
    """A finding is a flag if it is out-of-spec, or missing with evidence inside the changed files."""
    changed = {_norm(f) for f in changed_files}
    out = []
    for f in findings:
        if f["status"] == "out-of-spec":
            out.append(f)
        elif f["status"] == "missing" and any(_norm(e["file"]) in changed for e in f.get("evidence", [])):
            out.append(f)
    return out


def classify(meta: dict, findings: list[dict], warnings: list[str] | None = None) -> dict:
    fl = flags(findings, meta["files"])
    res = {"id": meta["id"], "kind": meta["kind"], "n_flags": len(fl),
           "flagged": [(f["requirement"], f["status"]) for f in fl],
           "llm_failures": sum("判斷失敗" in w for w in (warnings or []))}
    if meta["kind"] == "violation":
        target = meta["target_req"]
        tf = [f for f in findings if f["requirement"] == target]
        hit = any(f in fl for f in tf)
        res["target_status"] = tf[0]["status"] if tf else None
        res["target_missing_no_evidence"] = bool(tf) and tf[0]["status"] == "missing" and not hit
        res["extra_flags"] = len([f for f in fl if f["requirement"] != target])
        res["class"] = "TP" if hit else ("partial" if fl else "miss")
    else:
        strict = bool(fl)
        lenient = any(f["status"] == "missing" for f in fl)
        res["class"] = "false_alarm" if strict else "clean"
        res["false_alarm_strict"], res["false_alarm_lenient"] = strict, lenient
    return res


def summarize(rows: list[dict]) -> dict:
    v = [r for r in rows if r["kind"] == "violation"]
    b = [r for r in rows if r["kind"] == "benign"]
    n = lambda rs, c: sum(r["class"] == c for r in rs)  # noqa: E731
    return {
        "violations": len(v), "TP": n(v, "TP"), "partial": n(v, "partial"), "miss": n(v, "miss"),
        "benign": len(b), "false_alarm_strict": sum(r["false_alarm_strict"] for r in b),
        "false_alarm_lenient": sum(r["false_alarm_lenient"] for r in b),
        "tp_with_extra_flags": sum(1 for r in v if r["class"] == "TP" and r["extra_flags"]),
        "target_missing_no_evidence": sum(r.get("target_missing_no_evidence", False) for r in v),
        "cases_with_llm_failures": sum(1 for r in rows if r["llm_failures"]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="results/<name>/ output directory")
    ap.add_argument("--only", help="comma separated case ids, for debugging")
    args = ap.parse_args()

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
        report = graph.run(str(d / "spec.md"), str(d / "change.diff"))
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
          f"backend={llm.BACKEND} model={llm.MODEL} spec2patch@{commit}", "",
          f"- 真陽性 TP: **{s['TP']}/{s['violations']}**",
          f"- 部分正確: **{s['partial']}/{s['violations']}**",
          f"- 漏報: **{s['miss']}/{s['violations']}**",
          f"- 假警報(嚴格): **{s['false_alarm_strict']}/{s['benign']}**",
          f"- 假警報(寬鬆): **{s['false_alarm_lenient']}/{s['benign']}**",
          f"- TP 案例中同時多報非目標 flag: {s['tp_with_extra_flags']}",
          f"- 目標被判 missing 但無 evidence(算漏報): {s['target_missing_no_evidence']}",
          f"- 有 LLM 呼叫失敗的案例: {s['cases_with_llm_failures']}", "",
          "| case | class | target status | flags |", "| --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['id']} | {r['class']} | {r.get('target_status', '-')} | {r['flagged']} |")
    (out_dir / "summary.md").write_text("\n".join(md) + "\n")
    print("\n" + "\n".join(md[:14]))


if __name__ == "__main__":
    main()
