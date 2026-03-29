"""Standard API envelope for versioned JSON responses."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    latency_ms: Optional[float] = None
    engine: Optional[str] = None
    strategy: Optional[str] = None


class ApiResponse(BaseModel):
    request_id: str
    status: Literal["success", "error"] = "success"
    data: Optional[dict] = None
    error: Optional[dict] = None
    meta: ApiMeta = Field(default_factory=ApiMeta)

    @classmethod
    def ok(cls, request_id: str, data: dict, **meta: Any) -> "ApiResponse":
        return cls(request_id=request_id, status="success", data=data, meta=ApiMeta(**meta))

    @classmethod
    def fail(cls, request_id: str, code: str, message: str) -> "ApiResponse":
        return cls(
            request_id=request_id,
            status="error",
            error={"code": code, "message": message},
        )
