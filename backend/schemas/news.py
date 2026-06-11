"""资讯相关 Pydantic 模型"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class AnalysisResultSchema(BaseModel):
    id: int
    summary: str | None
    categories: str | None
    importance_score: int | None
    learning_score: int | None
    business_score: int | None
    startup_score: int | None
    attention_level: str | None
    developer_impact: str | None
    industry_impact: str | None
    one_sentence: str | None
    recommended_action: str | None

    model_config = {"from_attributes": True}


class NewsItemSchema(BaseModel):
    id: int
    source_id: int
    title: str
    url: str
    author: str | None
    published_at: datetime | None
    summary: str | None
    content: str | None
    language: str
    status: str
    analysis: AnalysisResultSchema | None = None

    model_config = {"from_attributes": True}


class NewsListData(BaseModel):
    items: list[NewsItemSchema]
    total: int
    page: int
    page_size: int


class AnalyzeResponse(BaseModel):
    success: bool
    analysis_id: int | None = None
    error: str | None = None


class PendingCount(BaseModel):
    total: int
    pending: int
    analyzed: int
    failed: int
