"""日报服务编排"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.report import DailyReport
from backend.models.analysis import AnalysisResult
from backend.services.reporter.generator import ReportGenerator
from backend.utils.logger import log
from backend.utils.helpers import parse_date
from backend.models.news import NewsItem


class ReportService:
    """日报服务"""

    def __init__(self):
        self.generator = None

    def _ensure_generator(self):
        if self.generator is None:
            from backend.services.analyzer.llm_client import LLMClient
            llm = LLMClient()
            self.generator = ReportGenerator(llm)

    async def generate_report(self, session: AsyncSession, report_date: date | None = None) -> dict:
        """生成日报"""
        if report_date is None:
            report_date = date.today()

        # 检查是否有分析数据
        from datetime import datetime as dt
        today_start = dt.combine(report_date, dt.min.time())
        today_end = dt.combine(report_date, dt.max.time())
        result = await session.execute(
            select(AnalysisResult)
            .join(NewsItem, AnalysisResult.news_item_id == NewsItem.id)
            .where(NewsItem.published_at >= today_start, NewsItem.published_at <= today_end)
            .limit(1)
        )
        has_data = result.scalar_one_or_none() is not None

        if not has_data:
            log.warning(f"{report_date} 无分析数据，跳过日报生成")
            return {"success": False, "error": "当日无分析数据"}

        self._ensure_generator()
        report = await self.generator.generate(session, report_date)
        if report:
            return {"success": True, "report_id": report.id, "date": str(report_date)}
        return {"success": False, "error": "生成失败"}

    async def get_today(self, session: AsyncSession) -> dict | None:
        """获取今日日报"""
        return await self.get_by_date(session, date.today())

    async def get_by_date(self, session: AsyncSession, report_date: date) -> dict | None:
        """获取指定日期日报"""
        result = await session.execute(
            select(DailyReport)
            .options(selectinload(DailyReport.items))
            .where(DailyReport.report_date == report_date)
        )
        report = result.scalar_one_or_none()
        if not report:
            return None
        return self._format_report(report)

    async def get_reports(self, session: AsyncSession, page: int = 1, page_size: int = 10) -> dict:
        """获取日报列表"""
        from sqlalchemy import desc
        result = await session.execute(
            select(DailyReport)
            .order_by(desc(DailyReport.report_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        reports = result.scalars().all()

        total = await session.execute(select(DailyReport))
        total_count = len(total.scalars().all())

        return {
            "items": [self._format_list_item(r) for r in reports],
            "total": total_count,
            "page": page,
            "page_size": page_size,
        }

    def _format_report(self, report: DailyReport) -> dict:
        """格式化日报详情"""
        sections = {}
        for item in report.items:
            st = item.section_type
            if st not in sections:
                sections[st] = []
            sections[st].append(item.content)

        import json
        parsed_sections = {}
        for st, items in sections.items():
            parsed_sections[st] = []
            for content in items:
                try:
                    parsed_sections[st].append(json.loads(content))
                except json.JSONDecodeError:
                    parsed_sections[st].append(content)

        return {
            "id": report.id,
            "report_date": str(report.report_date),
            "title": report.title,
            "summary": report.summary or "",
            "total_news": report.total_news,
            "total_sources": report.total_sources,
            "status": report.status,
            "generated_at": report.generated_at.isoformat() if report.generated_at else "",
            "sections": parsed_sections,
        }

    def _format_list_item(self, report: DailyReport) -> dict:
        return {
            "id": report.id,
            "report_date": str(report.report_date),
            "title": report.title,
            "summary": report.summary or "",
            "total_news": report.total_news,
            "status": report.status,
            "generated_at": report.generated_at.isoformat() if report.generated_at else "",
        }
