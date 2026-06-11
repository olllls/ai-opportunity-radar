"""开源项目与项目分析 Schema"""

from __future__ import annotations

from pydantic import BaseModel
from datetime import date


class ProjectAnalysisSchema(BaseModel):
    id: int
    tech_stack: str | None
    star_growth_rate: float | None
    star_growth_velocity: str | None
    function_analysis: str | None
    learning_value: int | None
    clone_value: int | None
    difficulty_level: str | None
    recommendation_score: float | None
    summary: str | None
    worth_learning_reason: str | None
    worth_cloning_reason: str | None
    similar_projects: str | None
    analysis_date: date | None

    model_config = {"from_attributes": True}


class OpenSourceProjectSchema(BaseModel):
    id: int
    repo_name: str
    repo_url: str
    description: str | None
    stars_count: int
    forks_count: int
    primary_lang: str | None
    topics: str | None
    analysis: ProjectAnalysisSchema | None = None

    model_config = {"from_attributes": True}


class ProjectListData(BaseModel):
    items: list[OpenSourceProjectSchema]
    total: int
    page: int
    page_size: int


class TrendingProject(BaseModel):
    id: int
    repo_name: str
    repo_url: str
    stars_count: int
    primary_lang: str | None
    recommendation_score: float | None
    summary: str | None
