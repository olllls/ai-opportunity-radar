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
        """分析单条资讯（LLM 不可用时使用规则分析）"""
        source_name = "unknown"
        if news.source:
            source_name = news.source.name

        if not self.llm.available:
            # 规则分析：根据标题关键词打分
            return self._rule_analyze(session, news, source_name)

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
        except Exception as e:
            log.error(f"分析失败 [{news.id}]: {e}")
            news.status = "failed"
            # 如果 LLM 不可用，切换到规则分析
            if not self.llm.available:
                return self._rule_analyze(session, news, source_name)
            return None

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

    def _rule_analyze(self, session, news, source_name) -> AnalysisResult:
        """规则分析：无需 LLM，根据标题关键词打分"""
        title_lower = (news.title or "").lower()

        ai_kw = ["ai", "machine learning", "deep learning", "llm", "gpt", "chatgpt",
                 "neural", "transformer", "rag", "agent", "language model",
                 "openai", "anthropic", "claude", "gemini", "deepseek"]
        dev_kw = ["open source", "github", "release", "api", "sdk", "framework",
                  "library", "tool", "code", "programming", "python", "javascript",
                  "docker", "kubernetes", "database"]
        biz_kw = ["funding", "startup", "launch", "product", "revenue", "series",
                  "million", "billion", "acquisition", "ipo"]

        ai_s = sum(2 for k in ai_kw if k in title_lower)
        dev_s = sum(1 for k in dev_kw if k in title_lower)
        biz_s = sum(2 for k in biz_kw if k in title_lower)
        start_s = sum(1 for k in biz_kw if k in title_lower)

        scores = {
            "importance_score": clamp(min(ai_s + dev_s + biz_s, 10), 1, 10),
            "learning_score": clamp(min(ai_s + dev_s, 10), 1, 10),
            "business_score": clamp(min(biz_s + ai_s, 10), 1, 10),
            "startup_score": clamp(min(start_s + ai_s, 10), 1, 10),
        }

        analysis = AnalysisResult(
            news_item_id=news.id,
            summary=f"[规则分析] {news.title}",
            categories='["AI"]' if ai_s > 0 else '["general"]',
            importance_score=scores["importance_score"],
            learning_score=scores["learning_score"],
            business_score=scores["business_score"],
            startup_score=scores["startup_score"],
            attention_level=calc_attention_level(scores),
            developer_impact="", industry_impact="",
            one_sentence=news.title[:200],
            model_used="rule-based",
            prompt_tokens=0, completion_tokens=0, analysis_time_ms=0,
        )
        session.add(analysis)
        news.status = "analyzed"
        log.info(f"规则分析完成: {news.title[:50]} → {analysis.attention_level} ({analysis.importance_score}/10)")
        return analysis

    async def analyze_batch(self, session: AsyncSession) -> dict:
        """批量分析所有待处理资讯（串行执行）"""
        from sqlalchemy.orm import selectinload

        # 先查出已有结果的 news_item_id 避免重复分析
        existing_ids = set()
        ids_result = await session.execute(
            select(AnalysisResult.news_item_id)
        )
        for row in ids_result.all():
            existing_ids.add(row[0])

        result = await session.execute(
            select(NewsItem)
            .where(NewsItem.status == "pending")
            .options(selectinload(NewsItem.source))
            .order_by(NewsItem.created_at.asc())
            .limit(50)
        )
        pending = result.scalars().all()
        pending = [n for n in pending if n.id not in existing_ids]

        if not pending:
            # 修复状态不一致：把有分析结果但标记为 pending 的改为 analyzed
            for n in result.scalars().all():
                if n.id in existing_ids:
                    n.status = "analyzed"
            await session.commit()
            return {"total": 0, "success": 0, "failed": 0}

        log.info(f"开始批量分析: {len(pending)} 条待处理")

        success = 0
        failed = 0
        for news in pending:
            r = await self.analyze_item(session, news)
            if isinstance(r, AnalysisResult):
                success += 1
            else:
                failed += 1

        await session.commit()
        log.info(f"批量分析完成: {success} 成功 / {failed} 失败")
        return {"total": len(pending), "success": success, "failed": failed}

    def _json_or_none(self, data) -> str | None:
        import json
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return None
