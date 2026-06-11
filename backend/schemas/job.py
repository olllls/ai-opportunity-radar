"""岗位趋势与技能 Schema"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class JobSkillSchema(BaseModel):
    id: int
    skill_name: str
    frequency: float | None
    is_new: bool

    model_config = {"from_attributes": True}


class JobTrendSchema(BaseModel):
    id: int
    role_name: str
    sample_count: int | None
    avg_salary_min: float | None
    avg_salary_max: float | None
    salary_trend: str | None
    market_demand_level: str | None
    learning_recommendation: str | None
    analysis_date: date | None
    skills: list[JobSkillSchema] = []

    model_config = {"from_attributes": True}


class JobListData(BaseModel):
    items: list[JobTrendSchema]
    total: int
    page: int
    page_size: int
