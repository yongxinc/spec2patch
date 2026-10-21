"""LangGraph 流程:load_spec → load_diff → analyze → report。無任何寫入動作。"""
import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from . import llm, tools
from .prompts import EXTRA_SYSTEM, REQ_SYSTEM, extra_prompt, req_prompt
from .schema import Finding, Report


class State(TypedDict, total=False):
    spec_path: str
    diff_path: str
    requirements: list[dict]
    diff_files: list[dict]
    raw_findings: list[dict]
    warnings: list[str]
    report: Report


def load_spec(state: State) -> State:
    reqs = tools.list_requirements(tools.read_file(state["spec_path"]))
    warnings = [] if reqs else ["規格中找不到 `## REQ-xxx` 條目"]
    return {"requirements": reqs, "warnings": warnings}


def load_diff(state: State) -> State:
    files = tools.parse_diff(tools.read_file(state["diff_path"]))
    warnings = list(state.get("warnings", []))
    if not files:
        warnings.append("diff 中找不到任何檔案改動")
    return {"diff_files": files, "warnings": warnings}


def _json_call(system: str, user: str) -> dict:
    """呼叫 LLM 並解析 JSON,失敗重試一次。"""
    last = None
    for _ in (1, 2):
        try:
            text = llm.chat_json(system, user)
            start = text.find("{")
            data, _ = json.JSONDecoder().raw_decode(text[start:])  # 只取第一個 JSON 物件
            if isinstance(data, dict):
                return data
            last = ValueError("回應不是 JSON 物件")
        except Exception as e:  # 連線、JSON 格式錯誤都不應讓程式崩潰
            last = e
    raise RuntimeError(f"{type(last).__name__}: {last}")


def analyze(state: State) -> State:
    """每條需求一次呼叫(小模型一次判斷多條容易混淆),再一次找規格外改動。"""
    warnings = list(state.get("warnings", []))
    raw: list[dict] = []
    if not state["requirements"] or not state["diff_files"]:
        return {"raw_findings": raw, "warnings": warnings}
    view = tools.render_diff(state["diff_files"])
    for r in state["requirements"]:
        try:
            d = _json_call(REQ_SYSTEM, req_prompt(r, view))
            checks = d.get("checks")
            reason = d.get("reason") or (
                "; ".join(map(str, checks)) if isinstance(checks, list) else "")
            raw.append({"requirement": r["id"], "status": d.get("status"),
                        "evidence": d.get("evidence") or [], "reason": reason})
        except RuntimeError as e:
            warnings.append(f"{r['id']} 判斷失敗:{e}")
    try:
        d = _json_call(EXTRA_SYSTEM, extra_prompt(state["requirements"], view))
        for x in d.get("extras") or []:
            if isinstance(x, dict):
                raw.append({"requirement": "-", "status": "unrelated",
                            "evidence": [{"file": x.get("file", ""), "lines": x.get("lines", "")}],
                            "reason": x.get("reason", "")})
    except RuntimeError as e:
        warnings.append(f"規格外改動判斷失敗:{e}")
    return {"raw_findings": raw, "warnings": warnings}


def report(state: State) -> State:
    """驗證並正規化 LLM 輸出,確保每條需求都有結果。"""
    warnings = list(state.get("warnings", []))
    known = {r["id"] for r in state["requirements"]}
    findings: list[Finding] = []
    seen: set[str] = set()
    for item in state.get("raw_findings", []):
        try:
            f = Finding.model_validate(item)
        except ValidationError:
            warnings.append(f"丟棄格式不合的項目:{json.dumps(item, ensure_ascii=False)[:120]}")
            continue
        if f.status in ("out-of-spec", "unrelated"):
            f.requirement = "-"
        elif f.requirement not in known:
            warnings.append(f"丟棄未知需求編號:{f.requirement}")
            continue
        elif f.requirement in seen:
            warnings.append(f"{f.requirement} 重複出現,僅保留第一筆")
            continue
        else:
            seen.add(f.requirement)
        findings.append(f)
    for r in state["requirements"]:
        if r["id"] not in seen:
            findings.append(Finding(
                requirement=r["id"], status="missing",
                reason="LLM 未回覆此條需求,保守標為 missing(未經判斷)。",
            ))
            if state.get("raw_findings"):
                warnings.append(f"LLM 漏回 {r['id']}")
    order = {r["id"]: i for i, r in enumerate(state["requirements"])}
    findings.sort(key=lambda f: (f.status in ("out-of-spec", "unrelated"), order.get(f.requirement, 0)))
    return {"report": Report(spec=state["spec_path"], diff=state["diff_path"],
                             findings=findings, warnings=warnings)}


def build_graph():
    g = StateGraph(State)
    for name, fn in [("load_spec", load_spec), ("load_diff", load_diff),
                     ("analyze", analyze), ("report", report)]:
        g.add_node(name, fn)
    g.add_edge(START, "load_spec")
    g.add_edge("load_spec", "load_diff")
    g.add_edge("load_diff", "analyze")
    g.add_edge("analyze", "report")
    g.add_edge("report", END)
    return g.compile()


def run(spec_path: str, diff_path: str) -> Report:
    return build_graph().invoke({"spec_path": spec_path, "diff_path": diff_path})["report"]
