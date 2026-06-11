"""开源项目 API 路由"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.project import OpenSourceProject, ProjectAnalysis
from backend.services.analyzer.service import AnalyzerService
from backend.schemas.project import OpenSourceProjectSchema, TrendingProject
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/projects", tags=["开源项目"])
analyzer_service = AnalyzerService()


@router.get("")
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    lang: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取项目列表"""
    query = (
        select(OpenSourceProject)
        .options(selectinload(OpenSourceProject.analysis))
        .order_by(desc(OpenSourceProject.stars_count))
    )
    count_query = select(func.count(OpenSourceProject.id))

    if lang:
        query = query.where(OpenSourceProject.primary_lang == lang)
        count_query = count_query.where(OpenSourceProject.primary_lang == lang)

    total = await db.execute(count_query)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return SuccessResponse(data={
        "items": [OpenSourceProjectSchema.model_validate(p) for p in result.scalars().all()],
        "total": total.scalar() or 0,
        "page": page,
        "page_size": page_size,
    })


@router.get("/trending")
async def get_trending(db: AsyncSession = Depends(get_db)):
    """获取热门推荐项目"""
    result = await db.execute(
        select(OpenSourceProject)
        .options(selectinload(OpenSourceProject.analysis))
        .order_by(desc(OpenSourceProject.stars_count))
        .limit(10)
    )
    projects = result.scalars().all()

    trending = []
    for p in projects:
        score = p.analysis.recommendation_score if p.analysis else None
        trending.append(TrendingProject(
            id=p.id, repo_name=p.repo_name, repo_url=p.repo_url,
            stars_count=p.stars_count, primary_lang=p.primary_lang,
            recommendation_score=score, summary=p.analysis.summary if p.analysis else None,
        ))

    return SuccessResponse(data=[t.model_dump() for t in trending])


@router.get("/{project_id}")
async def get_project_detail(project_id: int, db: AsyncSession = Depends(get_db)):
    """获取项目详情"""
    result = await db.execute(
        select(OpenSourceProject)
        .options(selectinload(OpenSourceProject.analysis))
        .where(OpenSourceProject.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return SuccessResponse(data=OpenSourceProjectSchema.model_validate(project).model_dump())


@router.post("/analyze")
async def analyze_projects(db: AsyncSession = Depends(get_db)):
    """手动分析待处理项目"""
    result = await analyzer_service.analyze_projects(db)
    return SuccessResponse(data=result)
