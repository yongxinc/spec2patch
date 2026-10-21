"""輸出 schema:每一項 = 需求編號、狀態、相關檔案與行號、理由。"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# covered:改動後需求仍然成立(滿足)。
# violated:改動違反這條需求。
# insufficient_context:要判斷必須看 diff 以外的程式碼;不猜,在 needs 說明需要什麼。
# not_applicable:diff 沒有碰到這條需求的程式碼(機械式判斷,未送進 LLM)。
# out-of-spec:改動違反規格但不屬於任何一條需求(目前流程不產生,保留給未來)。
# unrelated:改動不屬於任何一條需求(例如重構、改名、註解);不是違規。
Status = Literal["covered", "violated", "insufficient_context", "not_applicable", "out-of-spec", "unrelated"]


class Evidence(BaseModel):
    file: str
    lines: str = ""  # 例如 "12-20"
    side: Literal["new", "old"] = "new"  # 引用刪除行時為 "old",行號是變更前的位置

    @field_validator("side", mode="before")
    @classmethod
    def _side(cls, v):
        return "old" if isinstance(v, str) and v.strip().lower() == "old" else "new"

    @field_validator("file", "lines", mode="before")
    @classmethod
    def _to_str(cls, v):
        # 小模型常把 lines 回成陣列或數字
        if v is None:
            return ""
        if isinstance(v, (list, tuple)):
            return ", ".join(str(x) for x in v)
        return str(v)


class Finding(BaseModel):
    requirement: str  # REQ-003,或 out-of-spec / unrelated 時為 "-"
    status: Status
    evidence: list[Evidence] = Field(default_factory=list)
    reason: str = "(LLM 未提供理由)"
    needs: str = ""  # insufficient_context 時:需要看到什麼才能判斷

    @field_validator("reason", mode="before")
    @classmethod
    def _reason(cls, v):
        return v.strip() if isinstance(v, str) and v.strip() else "(LLM 未提供理由)"


class Report(BaseModel):
    spec: str
    diff: str
    findings: list[Finding]
    warnings: list[str] = Field(default_factory=list)
