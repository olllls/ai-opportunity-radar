"""资讯 API 路由"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.news import NewsItem
from backend.models.analysis import AnalysisResult
from backend.services.analyzer.service import AnalyzerService
from backend.schemas.news import NewsItemSchema, AnalyzeResponse, PendingCount
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/news", tags=["资讯"])
analyzer_service = AnalyzerService()


@router.get("")
async def list_news(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    status: str | None = Query(None, pattern="^(pending|analyzed|failed)$"),
    source_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """获取资讯列表（筛选+分页）"""
    query = (
        select(NewsItem)
        .options(selectinload(NewsItem.analysis))
        .order_by(NewsItem.published_at.desc().nullslast())
    )
    count_query = select(func.count(NewsItem.id))

    if status:
        query = query.where(NewsItem.status == status)
        count_query = count_query.where(NewsItem.status == status)
    if source_id:
        query = query.where(NewsItem.source_id == source_id)
        count_query = count_query.where(NewsItem.source_id == source_id)

    total = await db.execute(count_query)
    total_count = total.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    items = result.scalars().all()

    return SuccessResponse(data={
        "items": [NewsItemSchema.model_validate(n) for n in items],
        "total": total_count,
        "page": page,
        "page_size": page_size,
    })


@router.get("/pending-count")
async def get_pending_count(db: AsyncSession = Depends(get_db)):
    """获取待分析资讯统计"""
    total = await db.execute(select(func.count(NewsItem.id)))
    pending = await db.execute(
        select(func.count(NewsItem.id)).where(NewsItem.status == "pending")
    )
    analyzed = await db.execute(
        select(func.count(NewsItem.id)).where(NewsItem.status == "analyzed")
    )
    failed = await db.execute(
        select(func.count(NewsItem.id)).where(NewsItem.status == "failed")
    )
    return SuccessResponse(data=PendingCount(
        total=total.scalar() or 0,
        pending=pending.scalar() or 0,
        analyzed=analyzed.scalar() or 0,
        failed=failed.scalar() or 0,
    ).model_dump())


@router.get("/{news_id}")
async def get_news_detail(news_id: int, db: AsyncSession = Depends(get_db)):
    """获取资讯详情（含分析结果）"""
    result = await db.execute(
        select(NewsItem)
        .options(selectinload(NewsItem.analysis))
        .where(NewsItem.id == news_id)
    )
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail="资讯不存在")
    return SuccessResponse(data=NewsItemSchema.model_validate(news).model_dump())


@router.post("/analyze/{news_id}")
async def analyze_single(news_id: int, db: AsyncSession = Depends(get_db)):
    """手动分析单条资讯"""
    result = await analyzer_service.analyze_single(db, news_id)
    return SuccessResponse(data=result)
