"""Rebuild benchmark/cases/ from the pristine 5G project.

    python benchmark/build_cases.py /path/to/5Gproject

Reads the pristine sources with `git archive` (the 5G repo is never modified), applies each
mutation in a temp copy, runs the 5G project's own pytest suite on it, and writes
cases/<id>-<slug>/{change.diff, spec.md, meta.json}. Aborts if a benign change breaks any test.
"""
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spec2patch import tools  # noqa: E402

from mutations import BENIGN, VIOLATIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE_COMMIT = "4f8f2b6"
REQ_FILE = HERE / "requirements" / "ts33501-subset.md"


def archive(repo: Path, dest: Path):
    tar = subprocess.run(["git", "-C", str(repo), "archive", SOURCE_COMMIT], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar, check=True)


def apply(text: str, edits, label: str) -> str:
    for old, new, count in edits:
        n = text.count(old)
        if n != count:
            raise SystemExit(f"{label}: expected {count} occurrence(s) of {old!r}, found {n}")
        text = text.replace(old, new)
    return text


def run_tests(tree: Path) -> tuple[int, list[str]]:
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no"],
                       cwd=tree, capture_output=True, text=True)
    failed = sorted({l.split()[1].split("::")[0] for l in p.stdout.splitlines() if l.startswith("FAILED")})
    n = sum(1 for l in p.stdout.splitlines() if l.startswith("FAILED"))
    return n, failed


def scoped_spec(files: list[str], scope: dict) -> str:
    wanted = {r for f in files for r in scope.get(f, [])}
    reqs = tools.list_requirements(REQ_FILE.read_text())
    out = ["# 5G SUCI / 5G-AKA requirements (scoped to the files touched by the change)\n"]
    for r in reqs:
        if r["id"] in wanted:
            out.append(f"## {r['id']} {r['title']}\n{r['text']}\n")
    return "\n".join(out)


def main(repo: Path):
    scope = json.loads((HERE / "scope.json").read_text())
    pristine = Path(tempfile.mkdtemp())
    archive(repo, pristine)
    base_fail, _ = run_tests(pristine)
    if base_fail:
        raise SystemExit(f"pristine tree already fails {base_fail} tests")
    manifest = []
    for kind, items in (("violation", VIOLATIONS), ("benign", BENIGN)):
        for m in items:
            label = f"{m['id']}-{m['slug']}"
            old_text = (pristine / m["file"]).read_text()
            new_text = apply(old_text, m["edits"], label)
            tree = Path(tempfile.mkdtemp())
            archive(repo, tree)
            (tree / m["file"]).write_text(new_text)
            n_fail, failed_files = run_tests(tree)
            if kind == "benign" and n_fail:
                raise SystemExit(f"{label} is supposed to be harmless but breaks {n_fail} tests")
            diff = "".join(difflib.unified_diff(
                old_text.splitlines(True), new_text.splitlines(True),
                fromfile=f"a/{m['file']}", tofile=f"b/{m['file']}", n=3))
            diff = f"diff --git a/{m['file']} b/{m['file']}\n" + diff
            d = HERE / "cases" / label
            d.mkdir(parents=True, exist_ok=True)
            (d / "change.diff").write_text(diff)
            (d / "spec.md").write_text(scoped_spec([m["file"]], scope))
            meta = {
                "id": m["id"], "kind": kind, "files": [m["file"]], "summary": m["summary"],
                "target_req": m.get("target"), "expected": m.get("expected"),
                "upstream_tests_failed": n_fail, "upstream_failing_test_files": failed_files,
                "source_commit": SOURCE_COMMIT,
            }
            (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
            manifest.append(meta)
            print(f"{label:48s} {kind:9s} upstream tests failed: {n_fail}")
    (HERE / "cases" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
