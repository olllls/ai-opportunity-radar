"""日报相关 Pydantic 模型"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import date, datetime


class ReportListItem(BaseModel):
    id: int
    report_date: str
    title: str
    summary: str
    total_news: int
    status: str
    generated_at: str

    model_config = {"from_attributes": True}


class ReportDetail(BaseModel):
    id: int
    report_date: str
    title: str
    summary: str
    total_news: int
    total_sources: int
    status: str
    generated_at: str
    sections: dict

    model_config = {"from_attributes": True}


class ReportListData(BaseModel):
    items: list[ReportListItem]
    total: int
    page: int
    page_size: int


class GenerateResponse(BaseModel):
    success: bool
    report_id: int | None = None
    date: str | None = None
    error: str | None = None
