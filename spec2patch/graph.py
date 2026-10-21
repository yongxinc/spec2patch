"""LangGraph 流程:load_spec → load_diff → scope → analyze → report。無任何寫入動作。"""
import json
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from . import llm, scope as scope_mod, tools
from .prompts import EXTRA_SYSTEM, REQ_SYSTEM, extra_prompt, req_prompt
from .schema import Finding, Report


class State(TypedDict, total=False):
    spec_path: str
    diff_path: str
    requirements: list[dict]
    diff_files: list[dict]
    scope: dict
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


VERDICT_STATUS = {"violates": "violated", "satisfies": "covered", "insufficient_context": "insufficient_context"}


def scope_node(state: State) -> State:
    """機械式範圍限縮:哪些需求被這份 diff 碰到。沒碰到的直接 not_applicable,不問 LLM。"""
    sc = scope_mod.scope(state["requirements"], state["diff_files"])
    return {"scope": sc}


def analyze(state: State) -> State:
    """只對被碰到的需求問 LLM(違反或滿足?);沒有錨點的需求無法判斷範圍,一律詢問。"""
    warnings = list(state.get("warnings", []))
    raw: list[dict] = []
    if not state["requirements"] or not state["diff_files"]:
        return {"raw_findings": raw, "warnings": warnings}
    sc = state["scope"]
    view = tools.render_diff(state["diff_files"])
    for r in state["requirements"]:
        rid = r["id"]
        if sc["scoped"][rid] and not sc["touched"][rid]:
            raw.append({"requirement": rid, "status": "not_applicable",
                        "reason": "diff 沒有碰到此需求的程式碼(檔案、符號、行號皆未交集),未送入 LLM 判斷。"})
            continue
        try:
            d = _json_call(REQ_SYSTEM, req_prompt(r, view))
            checks = d.get("checks")
            reason = d.get("reason") or (
                "; ".join(map(str, checks)) if isinstance(checks, list) else "")
            raw.append({"requirement": rid, "status": VERDICT_STATUS.get(str(d.get("verdict")).strip().lower()),
                        "evidence": d.get("evidence") or [], "reason": reason, "needs": d.get("needs") or ""})
        except RuntimeError as e:
            warnings.append(f"{rid} 判斷失敗:{e}")
    if all(sc["scoped"].values()):
        # 每條需求都有錨點:沒歸屬到任何需求的變更就是「與需求無關」,不需要 LLM
        for u in sc["unattributed"]:
            nums = [c["new"] if c["sign"] == "+" else c["old"] for c in u["changes"]]
            side = "new" if any(c["sign"] == "+" for c in u["changes"]) else "old"
            raw.append({"requirement": "-", "status": "unrelated",
                        "evidence": [{"file": u["file"], "lines": f"{min(nums)}-{max(nums)}", "side": side}],
                        "reason": "這段改動未落在任何需求的程式碼錨點內。"})
    else:
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
                requirement=r["id"], status="insufficient_context",
                needs="模型未給出有效判定(呼叫失敗或格式無效),未經判斷。",
                reason="LLM 未回覆此條需求,不猜測。",
            ))
            if state.get("raw_findings"):
                warnings.append(f"LLM 漏回 {r['id']}")
    order = {r["id"]: i for i, r in enumerate(state["requirements"])}
    findings.sort(key=lambda f: (f.status in ("out-of-spec", "unrelated"), order.get(f.requirement, 0)))
    return {"report": Report(spec=state["spec_path"], diff=state["diff_path"],
                             findings=findings, warnings=warnings)}


def build_graph():
    g = StateGraph(State)
    for name, fn in [("load_spec", load_spec), ("load_diff", load_diff), ("scope", scope_node),
                     ("analyze", analyze), ("report", report)]:
        g.add_node(name, fn)
    g.add_edge(START, "load_spec")
    g.add_edge("load_spec", "load_diff")
    g.add_edge("load_diff", "scope")
    g.add_edge("scope", "analyze")
    g.add_edge("analyze", "report")
    g.add_edge("report", END)
    return g.compile()


def run(spec_path: str, diff_path: str) -> Report:
    return build_graph().invoke({"spec_path": spec_path, "diff_path": diff_path})["report"]
