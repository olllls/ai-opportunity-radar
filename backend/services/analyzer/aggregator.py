"""聚合分析器 - 生成当日趋势总结"""

from datetime import date, datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.analysis import AnalysisResult
from backend.models.news import NewsItem
from backend.services.analyzer.llm_client import LLMClient
from backend.utils.logger import log


AGGREGATE_PROMPT = """你是AI行业分析师。以下是今日AI领域的重要资讯分析结果汇总。

请总结今日的关键趋势和热点。

分析数据：
{analysis_data}

请输出JSON格式：
{{
    "trend_summary": "今日趋势总结（100-200字）",
    "hot_topics": ["热点1", "热点2", "热点3"],
    "key_insight": "今日最重要的一个洞察（一句话）"
}}"""


class Aggregator:
    """聚合分析器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def aggregate(self, session: AsyncSession, report_date: date) -> dict:
        """聚合当日分析结果"""
        today = datetime.combine(report_date, datetime.min.time())
        tomorrow = datetime.combine(report_date, datetime.max.time())

        result = await session.execute(
            select(AnalysisResult)
            .join(NewsItem, AnalysisResult.news_item_id == NewsItem.id)
            .where(
                NewsItem.published_at >= today,
                NewsItem.published_at <= tomorrow,
                AnalysisResult.attention_level.in_(["urgent", "high", "normal"]),
            )
            .order_by(AnalysisResult.importance_score.desc())
            .limit(20)
        )
        analyses = result.scalars().all()

        if not analyses:
            # fallback: 最近的分析结果
            result = await session.execute(
                select(AnalysisResult)
                .order_by(AnalysisResult.created_at.desc())
                .limit(20)
            )
            analyses = result.scalars().all()

        summary_list = []
        for a in analyses:
            summary_list.append(
                f"- [{a.attention_level}] 评分{ a.importance_score}/10 | "
                f"{a.one_sentence or '无摘要'} (ID:{a.news_item_id})"
            )

        data_text = "\n".join(summary_list) if summary_list else "今日无分析数据"

        prompt = AGGREGATE_PROMPT.format(analysis_data=data_text)

        try:
            resp = await self.llm.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            result = resp["content"]
            log.info(f"聚合分析完成: {result.get('key_insight', '')[:50]}")
            return result
        except Exception as e:
            log.error(f"聚合分析失败: {e}")
            return {
                "trend_summary": "今日聚合分析暂不可用",
                "hot_topics": [],
                "key_insight": "",
            }
