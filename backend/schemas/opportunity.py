"""创业机会与机会分析 Schema"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class OpportunityAnalysisSchema(BaseModel):
    id: int
    category: str | None
    target_users: str | None
    business_model: str | None
    pricing_model: str | None
    estimated_mrr: str | None
    competition_level: str | None
    personal_dev_friendly: bool | None
    dev_difficulty: str | None
    development_time: str | None
    key_features: str | None
    improvement_suggestion: str | None
    opportunity_score: int | None
    analysis_date: date | None

    model_config = {"from_attributes": True}


class StartupOpportunitySchema(BaseModel):
    id: int
    product_name: str
    product_url: str | None
    source_type: str
    source_url: str | None
    description: str | None
    analysis: OpportunityAnalysisSchema | None = None

    model_config = {"from_attributes": True}


class OpportunityListData(BaseModel):
    items: list[StartupOpportunitySchema]
    total: int
    page: int
    page_size: int
