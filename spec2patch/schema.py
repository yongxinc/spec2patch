"""輸出 schema:每一項 = 需求編號、狀態、相關檔案與行號、理由。"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Status = Literal["covered", "missing", "out-of-spec"]


class Evidence(BaseModel):
    file: str
    lines: str = ""  # 例如 "12-20"

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
    requirement: str  # REQ-003,或 out-of-spec 時為 "-"
    status: Status
    evidence: list[Evidence] = Field(default_factory=list)
    reason: str = "(LLM 未提供理由)"

    @field_validator("reason", mode="before")
    @classmethod
    def _reason(cls, v):
        return v.strip() if isinstance(v, str) and v.strip() else "(LLM 未提供理由)"


class Report(BaseModel):
    spec: str
    diff: str
    findings: list[Finding]
    warnings: list[str] = Field(default_factory=list)
