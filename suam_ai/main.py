"""FastAPI entry point for the Suam AI pipeline."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from suam_ai.core.analyzer import summarise_context
from suam_ai.core.context_builder import build_context
from suam_ai.core.llm_chain import ask_suam

app = FastAPI(title="Suam AI API", version="1.0.0")


class AskRequest(BaseModel):
    question: str = Field(..., description="사용자 질문")
    saju: Optional[Dict[str, Any]] = Field(default=None, description="사주 데이터")
    deterministic: bool = Field(
        default=False,
        description="True일 경우 LLM 대신 룰셋 기반 요약을 반환합니다.",
    )


class AskResponse(BaseModel):
    answer: str = Field(..., description="분석 결과")
    used_llm: bool = Field(..., description="LLM 호출 여부")


@app.get("/health", tags=["meta"])
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse, tags=["analysis"])
def ask_api(payload: AskRequest) -> AskResponse:
    if not payload.question:
        raise HTTPException(status_code=422, detail="question 필드는 비워둘 수 없습니다.")

    context = build_context(payload.question, payload.saju)

    if payload.deterministic:
        return AskResponse(answer=summarise_context(context), used_llm=False)

    answer = ask_suam(payload.question, payload.saju)
    used_llm = not answer.startswith("⚠️")
    return AskResponse(answer=answer, used_llm=used_llm)
