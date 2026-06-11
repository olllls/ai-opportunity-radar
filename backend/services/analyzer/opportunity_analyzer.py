"""创业机会分析器"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.opportunity import StartupOpportunity, OpportunityAnalysis
from backend.services.analyzer.llm_client import LLMClient
from backend.utils.logger import log


OPPORTUNITY_PROMPT = """你是一名AI领域创业顾问。请分析以下创业机会。

【产品名称】{product_name}
【来源】{source_type}
【描述】{description}

请输出以下JSON格式的分析结果（不要输出其他内容，严格JSON格式）：
{{
    "category": "产品分类（如 AI编程/内容生成/数据分析等）",
    "target_users": "目标用户群体",
    "business_model": "商业模式分析（30-50字）",
    "pricing_model": "免费/Freemium/订阅/一次性付费",
    "estimated_mrr": "预估月收入范围",
    "competition_level": "low/medium/high",
    "personal_dev_friendly": true,
    "dev_difficulty": "low/medium/high",
    "development_time": "预估开发周期",
    "key_features": ["核心功能1", "核心功能2", "核心功能3"],
    "improvement_suggestion": "改进建议（30-50字）",
    "opportunity_score": 0
}}

评分说明：
- opportunity_score 1-10：综合创业机会评分
- personal_dev_friendly：是否适合个人开发者
- dev_difficulty：开发难度"""


class OpportunityAnalyzer:
    """创业机会分析器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def analyze(self, session: AsyncSession, opportunity: StartupOpportunity) -> OpportunityAnalysis | None:
        """分析单个创业机会"""
        prompt = OPPORTUNITY_PROMPT.format(
            product_name=opportunity.product_name,
            source_type=opportunity.source_type,
            description=(opportunity.description or "")[:1000],
        )

        try:
            resp = await self.llm.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            data = resp["content"]

            from backend.utils.helpers import clamp

            analysis = OpportunityAnalysis(
                opportunity_id=opportunity.id,
                category=data.get("category", ""),
                target_users=data.get("target_users", ""),
                business_model=data.get("business_model", ""),
                pricing_model=data.get("pricing_model", ""),
                estimated_mrr=data.get("estimated_mrr", ""),
                competition_level=data.get("competition_level", "medium"),
                personal_dev_friendly=data.get("personal_dev_friendly", True),
                dev_difficulty=data.get("dev_difficulty", "medium"),
                development_time=data.get("development_time", ""),
                key_features=self._json_or_none(data.get("key_features", [])),
                improvement_suggestion=data.get("improvement_suggestion", ""),
                opportunity_score=clamp(int(data.get("opportunity_score", 5)), 1, 10),
                analysis_date=date.today(),
            )

            session.add(analysis)
            await session.flush()
            log.info(f"机会分析完成: {opportunity.product_name} → {analysis.opportunity_score}/10")
            return analysis

        except Exception as e:
            log.error(f"机会分析失败 [{opportunity.product_name}]: {e}")
            return None

    async def analyze_pending(self, session: AsyncSession) -> dict:
        """分析所有待处理机会"""
        result = await session.execute(
            select(StartupOpportunity)
            .outerjoin(OpportunityAnalysis)
            .where(OpportunityAnalysis.id.is_(None))
            .limit(20)
        )
        pending = result.scalars().all()

        if not pending:
            return {"total": 0, "success": 0, "failed": 0}

        log.info(f"开始批量机会分析: {len(pending)} 个待处理")

        success = 0
        failed = 0
        for opp in pending:
            r = await self.analyze(session, opp)
            if r:
                success += 1
            else:
                failed += 1

        await session.commit()
        log.info(f"批量机会分析完成: {success} 成功 / {failed} 失败")
        return {"total": len(pending), "success": success, "failed": failed}

    def _json_or_none(self, data) -> str | None:
        import json
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return None
