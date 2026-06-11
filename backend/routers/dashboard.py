"""仪表盘 API 路由"""

from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.news import NewsItem
from backend.models.collection_source import CollectionSource
from backend.models.report import DailyReport
from backend.schemas.system import DashboardStats
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘"])


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """获取仪表盘统计数据"""
    today = date.today()

    # 今日资讯数
    today_news = await db.execute(
        select(func.count(NewsItem.id))
        .where(func.date(NewsItem.published_at) == today)
    )

    # 待分析数
    pending = await db.execute(
        select(func.count(NewsItem.id)).where(NewsItem.status == "pending")
    )

    # 日报总数
    reports = await db.execute(select(func.count(DailyReport.id)))

    # 采集源统计
    active_sources = await db.execute(
        select(func.count(CollectionSource.id))
        .where(CollectionSource.is_active.is_(True))
    )
    total_sources = await db.execute(select(func.count(CollectionSource.id)))

    # 最近采集时间
    last_collect = await db.execute(
        select(CollectionSource.last_collected)
        .where(CollectionSource.last_collected.isnot(None))
        .order_by(CollectionSource.last_collected.desc())
        .limit(1)
    )
    last_collect_time = last_collect.scalar_one_or_none()

    # 最近日报
    last_report = await db.execute(
        select(DailyReport.report_date)
        .order_by(DailyReport.report_date.desc())
        .limit(1)
    )
    last_report_date = last_report.scalar_one_or_none()

    stats = DashboardStats(
        total_news_today=today_news.scalar() or 0,
        pending_analysis=pending.scalar() or 0,
        reports_count=reports.scalar() or 0,
        sources_active=active_sources.scalar() or 0,
        sources_total=total_sources.scalar() or 0,
        last_collect_time=str(last_collect_time) if last_collect_time else None,
        last_report_date=str(last_report_date) if last_report_date else None,
    )
    return SuccessResponse(data=stats.model_dump())
