"""系统相关 Pydantic 模型"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import datetime


class SystemConfigSchema(BaseModel):
    config_key: str
    config_value: str
    description: str | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ConfigUpdate(BaseModel):
    config_value: str


class LogEntry(BaseModel):
    id: int
    log_level: str
    module: str
    message: str
    detail: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class LogListData(BaseModel):
    items: list[LogEntry]
    total: int
    page: int
    page_size: int


class CollectResponse(BaseModel):
    total: int
    new: int
    failed: int
    sources: list


class PushResult(BaseModel):
    channel: str
    success: bool


class PushResponse(BaseModel):
    success: bool
    results: list[PushResult] | None = None
    error: str | None = None


class DashboardStats(BaseModel):
    total_news_today: int
    pending_analysis: int
    reports_count: int
    sources_active: int
    sources_total: int
    last_collect_time: str | None = None
    last_report_date: str | None = None
