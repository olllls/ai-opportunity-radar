"""创业机会 API 路由"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.opportunity import StartupOpportunity, OpportunityAnalysis
from backend.services.analyzer.service import AnalyzerService
from backend.schemas.opportunity import StartupOpportunitySchema
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/opportunities", tags=["创业机会"])
analyzer_service = AnalyzerService()


@router.get("")
async def list_opportunities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    source_type: str | None = Query(None, pattern="^(product_hunt|hacker_news|other)$"),
    db: AsyncSession = Depends(get_db),
):
    """获取创业机会列表"""
    query = (
        select(StartupOpportunity)
        .options(selectinload(StartupOpportunity.analysis))
        .order_by(desc(StartupOpportunity.id))
    )
    count_query = select(func.count(StartupOpportunity.id))

    if source_type:
        query = query.where(StartupOpportunity.source_type == source_type)
        count_query = count_query.where(StartupOpportunity.source_type == source_type)

    total = await db.execute(count_query)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return SuccessResponse(data={
        "items": [StartupOpportunitySchema.model_validate(o) for o in result.scalars().all()],
        "total": total.scalar() or 0,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{opportunity_id}")
async def get_opportunity_detail(opportunity_id: int, db: AsyncSession = Depends(get_db)):
    """获取创业机会详情"""
    result = await db.execute(
        select(StartupOpportunity)
        .options(selectinload(StartupOpportunity.analysis))
        .where(StartupOpportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="创业机会不存在")
    return SuccessResponse(data=StartupOpportunitySchema.model_validate(opp).model_dump())


@router.post("/analyze")
async def analyze_opportunities(db: AsyncSession = Depends(get_db)):
    """手动分析待处理创业机会"""
    result = await analyzer_service.analyze_opportunities(db)
    return SuccessResponse(data=result)
