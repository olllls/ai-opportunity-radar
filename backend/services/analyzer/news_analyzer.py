"""资讯分析器"""

from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.news import NewsItem
from backend.models.analysis import AnalysisResult
from backend.services.analyzer.llm_client import LLMClient
from backend.utils.logger import log
from backend.utils.helpers import clamp


ANALYSIS_PROMPT = """你是一名资深AI行业分析师。请分析以下AI资讯。

【标题】{title}
【来源】{source}
【内容】{content}

请输出以下JSON格式的分析结果（不要输出其他内容）：
{{
    "summary": "中文摘要（100-200字）",
    "categories": ["分类1", "分类2"],
    "importance_score": 0,
    "learning_score": 0,
    "business_score": 0,
    "startup_score": 0,
    "developer_impact": "对AI开发者影响",
    "industry_impact": "对AI行业影响",
    "one_sentence": "一句话总结（20字以内）"
}}

评分说明（严格遵循）：
1-3分 = 低价值（日常更新）
4-6分 = 中等价值（值得关注）
7-8分 = 高价值（重要动态）
9-10分 = 极高价值（里程碑事件）"""


def calc_attention_level(scores: dict) -> str:
    """根据评分计算关注等级"""
    importance = scores.get("importance_score", 0)
    learning = scores.get("learning_score", 0)
    business = scores.get("business_score", 0)
    startup = scores.get("startup_score", 0)

    max_score = max(importance, learning, business, startup)
    if max_score >= 9:
        return "urgent"
    high_count = sum(1 for s in [importance, learning, business, startup] if s >= 7)
    if max_score >= 7 or high_count >= 2:
        return "high"
    if max_score >= 4:
        return "normal"
    return "low"


class NewsAnalyzer:
    """资讯分析器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def analyze_item(self, session: AsyncSession, news: NewsItem) -> AnalysisResult | None:
        """分析单条资讯"""
        source_name = "unknown"
        if news.source:
            source_name = news.source.name

        prompt = ANALYSIS_PROMPT.format(
            title=news.title,
            source=source_name,
            content=(news.content or news.summary or news.title)[:3000],
        )

        try:
            resp = await self.llm.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            data = resp["content"]

            # 验证评分范围
            analysis = AnalysisResult(
                news_item_id=news.id,
                summary=data.get("summary", ""),
                categories=self._json_or_none(data.get("categories", [])),
                importance_score=clamp(int(data.get("importance_score", 5)), 1, 10),
                learning_score=clamp(int(data.get("learning_score", 5)), 1, 10),
                business_score=clamp(int(data.get("business_score", 5)), 1, 10),
                startup_score=clamp(int(data.get("startup_score", 5)), 1, 10),
                attention_level=calc_attention_level(data),
                developer_impact=data.get("developer_impact", ""),
                industry_impact=data.get("industry_impact", ""),
                one_sentence=data.get("one_sentence", "")[:200],
                model_used=resp.get("model", ""),
                prompt_tokens=resp.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=resp.get("usage", {}).get("completion_tokens", 0),
                analysis_time_ms=resp.get("elapsed_ms", 0),
            )

            session.add(analysis)
            await session.flush()

            news.status = "analyzed"
            log.info(f"分析完成: {news.title[:50]} → {analysis.attention_level} ({analysis.importance_score}/10)")
            return analysis

        except Exception as e:
            log.error(f"分析失败 [{news.id}]: {e}")
            news.status = "failed"
            return None

    async def analyze_batch(self, session: AsyncSession, concurrency: int = 3) -> dict:
        """批量分析所有待处理资讯"""
        from sqlalchemy.orm import selectinload
        result = await session.execute(
            select(NewsItem).where(NewsItem.status == "pending")
            .options(selectinload(NewsItem.source))
            .order_by(NewsItem.created_at.asc())
            .limit(50)
        )
        pending = result.scalars().all()

        if not pending:
            return {"total": 0, "success": 0, "failed": 0}

        log.info(f"开始批量分析: {len(pending)} 条待处理")

        sem = asyncio.Semaphore(concurrency)

        async def _analyze(news: NewsItem):
            async with sem:
                return await self.analyze_item(session, news)

        results = await asyncio.gather(*[_analyze(n) for n in pending], return_exceptions=True)

        success = sum(1 for r in results if isinstance(r, AnalysisResult))
        failed = sum(1 for r in results if isinstance(r, Exception) or r is None)

        await session.commit()
        log.info(f"批量分析完成: {success} 成功 / {failed} 失败")
        return {"total": len(pending), "success": success, "failed": failed}

    def _json_or_none(self, data) -> str | None:
        import json
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return None
