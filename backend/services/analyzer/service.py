"""分析服务编排"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.analyzer.llm_client import LLMClient
from backend.services.analyzer.news_analyzer import NewsAnalyzer
from backend.services.analyzer.project_analyzer import ProjectAnalyzer
from backend.services.analyzer.opportunity_analyzer import OpportunityAnalyzer
from backend.services.analyzer.aggregator import Aggregator
from backend.utils.logger import log


class AnalyzerService:
    """分析服务编排"""

    def __init__(self):
        self.llm = None
        self.news_analyzer = None
        self.project_analyzer = None
        self.opportunity_analyzer = None
        self.aggregator = None

    def _ensure_llm(self):
        if self.llm is None:
            self.llm = LLMClient()
            self.news_analyzer = NewsAnalyzer(self.llm)
            self.project_analyzer = ProjectAnalyzer(self.llm)
            self.opportunity_analyzer = OpportunityAnalyzer(self.llm)
            self.aggregator = Aggregator(self.llm)

    async def analyze_pending(self, session: AsyncSession) -> dict:
        """分析所有待处理资讯"""
        self._ensure_llm()
        return await self.news_analyzer.analyze_batch(session)

    async def analyze_single(self, session: AsyncSession, news_id: int) -> dict:
        """分析单条资讯"""
        self._ensure_llm()
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from backend.models.news import NewsItem
        result = await session.execute(
            select(NewsItem)
            .options(selectinload(NewsItem.source))
            .where(NewsItem.id == news_id)
        )
        news = result.scalar_one_or_none()
        if not news:
            return {"success": False, "error": "资讯不存在"}
        if news.status == "analyzed":
            return {"success": False, "error": "已经分析过"}

        analysis = await self.news_analyzer.analyze_item(session, news)
        await session.commit()
        return {"success": analysis is not None, "analysis_id": analysis.id if analysis else None}

    async def analyze_projects(self, session: AsyncSession) -> dict:
        """分析所有待处理开源项目"""
        self._ensure_llm()
        return await self.project_analyzer.analyze_pending(session)

    async def analyze_opportunities(self, session: AsyncSession) -> dict:
        """分析所有待处理创业机会"""
        self._ensure_llm()
        return await self.opportunity_analyzer.analyze_pending(session)

    async def aggregate(self, session: AsyncSession, report_date: date) -> dict:
        """聚合分析"""
        self._ensure_llm()
        return await self.aggregator.aggregate(session, report_date)
