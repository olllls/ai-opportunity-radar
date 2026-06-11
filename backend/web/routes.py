"""Web 页面路由"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.reporter.service import ReportService
from backend.services.analyzer.service import AnalyzerService
from backend.services.collector.service import CollectorService
from backend.utils.helpers import parse_date
from backend.models.news import NewsItem
from backend.models.project import OpenSourceProject
from backend.models.opportunity import StartupOpportunity
from backend.models.job import JobTrend

router = APIRouter(tags=["Web页面"])
env = Environment(loader=FileSystemLoader("backend/templates"), autoescape=True)

report_service = ReportService()
analyzer_service = AnalyzerService()
collector_service = CollectorService()


def render(name: str, **context) -> str:
    """渲染模板"""
    template = env.get_template(name)
    return template.render(**context)


@router.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse('<html><head><meta http-equiv="refresh" content="0;url=/daily"></head></html>')


@router.get("/daily", response_class=HTMLResponse)
async def daily_list(request: Request, db: AsyncSession = Depends(get_db)):
    """日报列表"""
    data = await report_service.get_reports(db, page=1, page_size=30)
    html = render("reports.html", reports=data, title="AI机会雷达 - 日报列表")
    return HTMLResponse(html)


@router.get("/daily/{date_str}", response_class=HTMLResponse)
async def daily_detail(request: Request, date_str: str, db: AsyncSession = Depends(get_db)):
    """日报详情"""
    report_date = parse_date(date_str) or date.today()
    report = await report_service.get_by_date(db, report_date)

    if not report:
        html = render("report.html", report=None, date=date_str, title="日报不存在 - AI机会雷达")
    else:
        html = render("report.html", report=report, date=date_str, title=report["title"])
    return HTMLResponse(html)


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request, page: int = 1, db: AsyncSession = Depends(get_db)):
    """资讯列表"""
    from sqlalchemy import select, func, desc
    from sqlalchemy.orm import selectinload

    page_size = 20
    result = await db.execute(
        select(NewsItem)
        .options(selectinload(NewsItem.source), selectinload(NewsItem.analysis))
        .order_by(desc(NewsItem.published_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    total = await db.execute(select(func.count(NewsItem.id)))

    news_items = []
    for item in items:
        nd = {"id": item.id, "title": item.title, "summary": item.summary or "",
              "source_name": item.source.name if item.source else "",
              "published_at": str(item.published_at) if item.published_at else "",
              "status": item.status}
        if item.analysis:
            nd["analysis"] = {"attention_level": item.analysis.attention_level or "low",
                              "importance_score": item.analysis.importance_score}
        news_items.append(nd)

    total_count = total.scalar() or 0
    html = render("news.html", news_items=news_items, page=page,
                  total_pages=max(1, (total_count + page_size - 1) // page_size),
                  title="AI机会雷达 - 资讯列表")
    return HTMLResponse(html)


@router.get("/news/{news_id}", response_class=HTMLResponse)
async def news_detail(request: Request, news_id: int, db: AsyncSession = Depends(get_db)):
    """资讯详情"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(NewsItem).options(selectinload(NewsItem.source), selectinload(NewsItem.analysis)).where(NewsItem.id == news_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        return HTMLResponse(render("news_detail.html", news=None, analysis=None, title="资讯不存在"))

    news = {"id": item.id, "title": item.title, "url": item.url, "summary": item.summary or "",
            "source_name": item.source.name if item.source else "", "author": item.author or "",
            "published_at": str(item.published_at) if item.published_at else "", "status": item.status}
    analysis = None
    if item.analysis:
        analysis = {"attention_level": item.analysis.attention_level or "low",
                    "one_sentence": item.analysis.one_sentence or "",
                    "summary": item.analysis.summary or "",
                    "importance_score": item.analysis.importance_score,
                    "learning_score": item.analysis.learning_score,
                    "business_score": item.analysis.business_score,
                    "startup_score": item.analysis.startup_score,
                    "developer_impact": item.analysis.developer_impact or "",
                    "industry_impact": item.analysis.industry_impact or "",
                    "recommended_action": item.analysis.recommended_action or ""}

    html = render("news_detail.html", news=news, analysis=analysis, title=item.title)
    return HTMLResponse(html)


@router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, db: AsyncSession = Depends(get_db)):
    """项目列表"""
    from sqlalchemy import select, desc
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(OpenSourceProject).options(selectinload(OpenSourceProject.analysis))
        .order_by(desc(OpenSourceProject.stars_count)).limit(20)
    )
    projects = [{"id": p.id, "repo_name": p.repo_name, "repo_url": p.repo_url,
                 "description": p.description or "", "stars_count": p.stars_count,
                 "forks_count": p.forks_count, "primary_lang": p.primary_lang or "",
                 "analysis": {"recommendation_score": p.analysis.recommendation_score,
                              "difficulty_level": p.analysis.difficulty_level or "intermediate",
                              "summary": p.analysis.summary or ""} if p.analysis else None}
                for p in result.scalars().all()]

    html = render("projects.html", projects=projects, title="AI机会雷达 - 开源项目")
    return HTMLResponse(html)


@router.get("/opportunities", response_class=HTMLResponse)
async def opportunities_page(request: Request, db: AsyncSession = Depends(get_db)):
    """创业机会列表"""
    from sqlalchemy import select, desc
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(StartupOpportunity).options(selectinload(StartupOpportunity.analysis))
        .order_by(desc(StartupOpportunity.id)).limit(20)
    )
    opportunities = [{"id": o.id, "product_name": o.product_name, "description": o.description or "",
                      "source_type": o.source_type, "product_url": o.product_url or "",
                      "analysis": {"opportunity_score": o.analysis.opportunity_score,
                                   "personal_dev_friendly": o.analysis.personal_dev_friendly,
                                   "dev_difficulty": o.analysis.dev_difficulty or "medium",
                                   "improvement_suggestion": o.analysis.improvement_suggestion or ""}
                      if o.analysis else None}
                     for o in result.scalars().all()]

    html = render("opportunities.html", opportunities=opportunities, title="AI机会雷达 - 创业机会")
    return HTMLResponse(html)


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request, db: AsyncSession = Depends(get_db)):
    """岗位趋势列表"""
    from sqlalchemy import select, desc
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(JobTrend).options(selectinload(JobTrend.skills))
        .order_by(desc(JobTrend.analysis_date)).limit(20)
    )
    jobs = [{"id": j.id, "role_name": j.role_name, "sample_count": j.sample_count,
             "avg_salary_min": j.avg_salary_min, "avg_salary_max": j.avg_salary_max,
             "market_demand_level": j.market_demand_level or "", "salary_trend": j.salary_trend or "",
             "learning_recommendation": j.learning_recommendation or "",
             "skills": [{"skill_name": s.skill_name, "frequency": s.frequency, "is_new": s.is_new}
                        for s in j.skills]}
            for j in result.scalars().all()]

    html = render("jobs.html", jobs=jobs, title="AI机会雷达 - 岗位趋势")
    return HTMLResponse(html)


@router.get("/config", response_class=HTMLResponse)
async def config_page(db: AsyncSession = Depends(get_db)):
    """系统配置页"""
    from backend.models.config_model import SystemConfig
    from sqlalchemy import select, desc
    result = await db.execute(select(SystemConfig).order_by(SystemConfig.config_key))
    configs = result.scalars().all()
    html = render("config.html", configs=configs, title="AI机会雷达 - 系统配置")
    return HTMLResponse(html)


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    page: int = 1,
    level: str | None = None,
    module: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """系统日志页"""
    from backend.models.log import SystemLog
    from sqlalchemy import select, func, desc

    query = select(SystemLog).order_by(desc(SystemLog.created_at))
    count_query = select(func.count(SystemLog.id))

    if level:
        query = query.where(SystemLog.log_level == level.upper())
        count_query = count_query.where(SystemLog.log_level == level.upper())
    if module:
        query = query.where(SystemLog.module == module)
        count_query = count_query.where(SystemLog.module == module)

    page_size = 50
    total = await db.execute(count_query)
    total_count = total.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    db_logs = result.scalars().all()

    modules_result = await db.execute(
        select(SystemLog.module).distinct().order_by(SystemLog.module)
    )
    modules_list = [r[0] for r in modules_result.all() if r[0]]

    html = render("logs.html",
        db_logs=db_logs,
        page=page, total=total_count, page_size=page_size,
        current_level=level or "", current_module=module or "",
        modules=modules_list,
        title="AI机会雷达 - 系统日志")
    return HTMLResponse(html)
