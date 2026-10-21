import argparse
import sys

from .graph import run

ICON = {"covered": "✅ covered", "violated": "❌ violated", "insufficient_context": "❓ insufficient_context",
        "not_applicable": "➖ not_applicable", "out-of-spec": "🚫 out-of-spec", "unrelated": "⚠️  unrelated"}


def format_text(report) -> str:
    out = [f"規格:{report.spec}", f"Diff:{report.diff}", ""]
    by = lambda st: [f.requirement for f in report.findings if f.status == st]  # noqa: E731
    out.append(f"滿足:{', '.join(by('covered')) or '無'}")
    out.append(f"違反:{', '.join(by('violated')) or '無'}")
    out.append(f"上下文不足:{', '.join(by('insufficient_context')) or '無'}")
    out.append(f"未碰到(不適用):{len(by('not_applicable'))} 條")
    out.append(f"與需求無關的改動:{len(by('unrelated'))} 處")
    out.append("")
    for f in report.findings:
        if f.status == "not_applicable":
            continue
        out.append(f"{ICON[f.status]}  {f.requirement}")
        for e in f.evidence:
            out.append(f"    · {e.file}" + (f":{e.lines}" if e.lines else "") + (" (變更前)" if e.side == "old" else ""))
        if f.needs:
            out.append(f"    需要:{f.needs}")
        out.append(f"    理由:{f.reason}")
    if report.warnings:
        out.append("")
        out.append("警告:")
        out.extend(f"  - {w}" for w in report.warnings)
    out.append("")
    out.append("※ 結果由 LLM 判斷,可能有誤,請人工複核。")
    return "\n".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="spec2patch", description="規格 vs diff 落差分析(唯讀)")
    p.add_argument("spec", help="規格 markdown 路徑")
    p.add_argument("diff", help="unified diff 路徑")
    p.add_argument("--format", choices=["both", "text", "json"], default="both")
    args = p.parse_args(argv)
    try:
        report = run(args.spec, args.diff)
    except OSError as e:
        print(f"錯誤:{e}", file=sys.stderr)
        return 2
    if args.format in ("both", "text"):
        print(format_text(report))
    if args.format == "both":
        print("\n--- JSON ---")
    if args.format in ("both", "json"):
        print(report.model_dump_json(indent=2))
    return 0
