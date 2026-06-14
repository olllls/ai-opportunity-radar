"""日报生成器"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.analysis import AnalysisResult
from backend.models.news import NewsItem
from backend.models.report import DailyReport, ReportItem
from backend.models.project import OpenSourceProject, ProjectAnalysis
from backend.models.opportunity import StartupOpportunity, OpportunityAnalysis
from backend.models.job import JobTrend, JobSkill
from backend.services.analyzer.llm_client import LLMClient
from backend.utils.logger import log
from backend.utils.helpers import parse_date


ACTIONS_PROMPT = """你是AI机会顾问。根据今日AI领域资讯和项目分析，给出2-3条具体可执行的行动建议。

今日分析摘要：
{summary}

请输出JSON：
{{
    "actions": [
        "具体行动1（含预估时间）",
        "具体行动2（含预估时间）",
        "具体行动3（含预估时间）"
    ]
}}

要求：每条建议必须具体可执行，包含学习/开发方向、优先级和预估耗时。"""


class ReportGenerator:
    """日报生成器"""

    def __init__(self, llm: LLMClient = None):
        self.llm = llm

    def _ensure_llm(self):
        if self.llm is None:
            self.llm = LLMClient()

    async def generate(self, session: AsyncSession, report_date: date) -> DailyReport | None:
        """生成指定日期的日报"""
        # 检查是否已存在
        existing = await session.execute(
            select(DailyReport).where(DailyReport.report_date == report_date)
        )
        existing_report = existing.scalar_one_or_none()
        if existing_report and existing_report.status == "completed":
            log.info(f"日报已存在: {report_date}")
            return existing_report

        # 1. 获取分析数据
        news_analyses = await self._get_news_analyses(session, report_date)
        projects = await self._get_projects(session)
        opportunities = await self._get_opportunities(session)
        jobs = await self._get_jobs(session)

        # 2. 编排板块
        sections = {
            "news": self._format_news(news_analyses),
            "tools": self._format_tools(news_analyses),
            "projects": self._format_projects(projects),
            "opportunities": self._format_opportunities(opportunities),
            "jobs": self._format_jobs(jobs),
            "actions": [],
        }

        # 3. 生成行动建议
        self._ensure_llm()
        sections["actions"] = await self._generate_actions(news_analyses, projects, opportunities)

        # 4. 创建日报
        now = datetime.utcnow()
        report = DailyReport(
            report_date=report_date,
            title=f"AI机会雷达 · {report_date}",
            summary=f"覆盖 {len(news_analyses)} 条资讯",
            total_news=len(news_analyses),
            total_sources=self._count_sources(news_analyses),
            status="completed",
            generated_at=now,
        )
        session.add(report)
        await session.flush()

        # 5. 保存各板块
        for section_type, items in sections.items():
            for i, item in enumerate(items):
                ri = ReportItem(
                    report_id=report.id,
                    section_type=section_type,
                    sort_order=i,
                    content=json.dumps(item, ensure_ascii=False),
                )
                session.add(ri)

        await session.commit()
        log.info(f"日报生成完成: {report_date} ({len(news_analyses)} 条资讯)")
        return report

    async def _get_news_analyses(self, session: AsyncSession, report_date: date) -> list[dict]:
        """获取当日资讯分析"""
        today_start = datetime.combine(report_date, datetime.min.time()) - timedelta(hours=8)
        today_end = datetime.combine(report_date, datetime.max.time()) - timedelta(hours=8)

        result = await session.execute(
            select(NewsItem)
            .options(selectinload(NewsItem.analysis), selectinload(NewsItem.source))
            .join(AnalysisResult, NewsItem.id == AnalysisResult.news_item_id)
            .where(
                AnalysisResult.created_at >= today_start,
                AnalysisResult.created_at <= today_end,
            )
            .order_by(AnalysisResult.importance_score.desc().nullslast())
            .limit(30)
        )
        news_items = result.scalars().all()
        items = []
        for news in news_items:
            if news.analysis:
                items.append({
                    "id": news.id,
                    "title": news.title,
                    "url": news.url,
                    "source": news.source.name if news.source else "",
                    "summary": news.analysis.summary or "",
                    "one_sentence": news.analysis.one_sentence or "",
                    "importance_score": news.analysis.importance_score or 0,
                    "learning_score": news.analysis.learning_score or 0,
                    "business_score": news.analysis.business_score or 0,
                    "startup_score": news.analysis.startup_score or 0,
                    "attention_level": news.analysis.attention_level or "low",
                })
        return items

    def _format_news(self, items: list[dict]) -> list[dict]:
        """格式化重点新闻（取Top 5，urgent/high优先）"""
        def sort_key(item):
            level_map = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
            return (level_map.get(item.get("attention_level", "low"), 99), -item.get("importance_score", 0))
        sorted_items = sorted(items, key=sort_key)
        return sorted_items[:5]

    def _format_tools(self, items: list[dict]) -> list[dict]:
        """格式化工具推荐"""
        tools = [i for i in items if i.get("business_score", 0) >= 5]
        return sorted(tools, key=lambda x: -x.get("business_score", 0))[:3]

    async def _get_projects(self, session: AsyncSession) -> list[dict]:
        """获取项目分析"""
        result = await session.execute(
            select(ProjectAnalysis)
            .options(selectinload(ProjectAnalysis.project))
            .order_by(ProjectAnalysis.recommendation_score.desc().nullslast())
            .limit(5)
        )
        items = []
        for pa in result.scalars().all():
            if pa.project:
                items.append({
                    "repo_name": pa.project.repo_name,
                    "repo_url": pa.project.repo_url,
                    "stars_count": pa.project.stars_count,
                    "tech_stack": pa.tech_stack or "",
                    "recommendation_score": pa.recommendation_score or 0,
                    "summary": pa.summary or "",
                    "worth_learning": bool(pa.learning_value and pa.learning_value >= 6),
                    "worth_cloning": bool(pa.clone_value and pa.clone_value >= 6),
                })
        return items

    def _format_projects(self, items: list[dict]) -> list[dict]:
        return items[:5]

    async def _get_opportunities(self, session: AsyncSession) -> list[dict]:
        """获取创业机会"""
        result = await session.execute(
            select(OpportunityAnalysis)
            .options(selectinload(OpportunityAnalysis.opportunity))
            .order_by(OpportunityAnalysis.opportunity_score.desc().nullslast())
            .limit(5)
        )
        items = []
        for oa in result.scalars().all():
            if oa.opportunity:
                items.append({
                    "product_name": oa.opportunity.product_name,
                    "business_model": oa.business_model or "",
                    "personal_dev_friendly": bool(oa.personal_dev_friendly),
                    "opportunity_score": oa.opportunity_score or 0,
                    "dev_difficulty": oa.dev_difficulty or "",
                })
        return items

    def _format_opportunities(self, items: list[dict]) -> list[dict]:
        return items[:3]

    async def _get_jobs(self, session: AsyncSession) -> list[dict]:
        """获取岗位趋势"""
        result = await session.execute(
            select(JobTrend)
            .options(selectinload(JobTrend.skills))
            .order_by(JobTrend.analysis_date.desc().nullslast()).limit(5)
        )
        items = []
        for jt in result.scalars().all():
            skills = []
            for s in jt.skills:
                skills.append({"name": s.skill_name, "frequency": s.frequency or 0, "is_new": s.is_new})
            items.append({
                "role_name": jt.role_name,
                "market_demand_level": jt.market_demand_level or "",
                "skills": skills,
                "learning_recommendation": jt.learning_recommendation or "",
            })
        return items

    def _format_jobs(self, items: list[dict]) -> list[dict]:
        return items[:5]

    async def _generate_actions(self, news: list[dict], projects: list[dict], opportunities: list[dict]) -> list[str]:
        """生成行动建议"""
        if not self.llm:
            return ["重点阅读今日日报中的高评分资讯"]

        summary_parts = []
        for n in news[:3]:
            summary_parts.append(f"- {n.get('title')} ({n.get('one_sentence', '')})")
        for p in projects[:2]:
            summary_parts.append(f"- 开源项目: {p.get('repo_name', '')}")
        for o in opportunities[:2]:
            summary_parts.append(f"- 创业机会: {o.get('product_name', '')}")

        summary = "\n".join(summary_parts) if summary_parts else "今日分析数据较少"

        try:
            resp = await self.llm.chat_with_json(
                messages=[{"role": "user", "content": ACTIONS_PROMPT.format(summary=summary)}],
                max_tokens=1024,
            )
            return resp["content"].get("actions", [])
        except Exception as e:
            log.warning(f"行动建议生成失败: {e}")
            return ["关注今日重点新闻中的高评分资讯", "浏览GitHub热门项目寻找灵感"]

    def _count_sources(self, items: list[dict]) -> int:
        sources = set()
        for item in items:
            if item.get("source"):
                sources.add(item["source"])
        return len(sources)
