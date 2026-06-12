"""开源项目分析器"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.project import OpenSourceProject, ProjectAnalysis
from backend.services.analyzer.llm_client import LLMClient
from backend.utils.logger import log
from backend.utils.helpers import clamp


PROJECT_PROMPT = """你是一名资深开源技术评估专家。请分析以下开源项目。

【仓库】{repo_name}
【描述】{description}
【Star数】{stars}
【Fork数】{forks}
【主要语言】{language}
【标签】{topics}

请输出以下JSON格式的分析结果（不要输出其他内容，严格JSON格式）：
{{
    "tech_stack": ["技术1", "技术2"],
    "function_analysis": "项目功能分析（50-100字）",
    "learning_value": 0,
    "clone_value": 0,
    "difficulty_level": "beginner/intermediate/advanced",
    "recommendation_score": 0.0,
    "summary": "中文摘要（50-100字）",
    "worth_learning_reason": "值得学习的理由（30-50字）",
    "worth_cloning_reason": "值得复刻的理由（30-50字）"
}}

评分说明：
- learning_value 1-10：从该项目能学到多少
- clone_value 1-10：复刻该项目做类似产品的价值
- recommendation_score 1.0-10.0：综合推荐指数"""


class ProjectAnalyzer:
    """开源项目分析器"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def analyze(self, session: AsyncSession, project: OpenSourceProject) -> ProjectAnalysis | None:
        """分析单个开源项目（LLM 不可用时使用规则分析）"""
        if not self.llm.available:
            return self._rule_analyze(session, project)

        prompt = PROJECT_PROMPT.format(
            repo_name=project.repo_name,
            description=(project.description or "")[:500],
            stars=project.stars_count,
            forks=project.forks_count,
            language=project.primary_lang or "unknown",
            topics=project.topics or "[]",
        )

        try:
            resp = await self.llm.chat_with_json(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            data = resp["content"]

            analysis = ProjectAnalysis(
                project_id=project.id,
                tech_stack=self._json_or_none(data.get("tech_stack", [])),
                function_analysis=data.get("function_analysis", ""),
                learning_value=clamp(int(data.get("learning_value", 5)), 1, 10),
                clone_value=clamp(int(data.get("clone_value", 5)), 1, 10),
                difficulty_level=data.get("difficulty_level", "intermediate"),
                recommendation_score=clamp(float(data.get("recommendation_score", 5.0)), 1.0, 10.0),
                summary=data.get("summary", ""),
                worth_learning_reason=data.get("worth_learning_reason", ""),
                worth_cloning_reason=data.get("worth_cloning_reason", ""),
                analysis_date=date.today(),
            )

            session.add(analysis)
            await session.flush()
            log.info(f"项目分析完成: {project.repo_name} → {analysis.recommendation_score}/10")
            return analysis

        except Exception as e:
            log.error(f"项目分析失败 [{project.repo_name}]: {e}")
            if not self.llm.available:
                return self._rule_analyze(session, project)
            return None

    def _rule_analyze(self, session, project) -> ProjectAnalysis:
        """规则分析：根据 Star 数和语言评分"""
        lang = project.primary_lang or ""
        score = clamp(project.stars_count / 1000 + 1, 1.0, 10.0)
        diff = "beginner" if score < 3 else "intermediate" if score < 7 else "advanced"
        analysis = ProjectAnalysis(
            project_id=project.id,
            tech_stack=f'["{lang}"]' if lang else "[]",
            function_analysis=project.description or "",
            learning_value=clamp(int(score), 1, 10),
            clone_value=clamp(int(score * 0.7), 1, 10),
            difficulty_level=diff,
            recommendation_score=score,
            summary=project.description or "",
            worth_learning_reason="基于 Star 数和描述的自动评估",
            worth_cloning_reason="基于 Star 数和描述的自动评估",
            analysis_date=date.today(),
        )
        session.add(analysis)
        log.info(f"规则项目分析完成: {project.repo_name} → {score}/10")
        return analysis

    async def analyze_pending(self, session: AsyncSession) -> dict:
        """分析所有待处理项目"""
        result = await session.execute(
            select(OpenSourceProject)
            .outerjoin(ProjectAnalysis)
            .where(ProjectAnalysis.id.is_(None))
            .limit(20)
        )
        pending = result.scalars().all()

        if not pending:
            return {"total": 0, "success": 0, "failed": 0}

        log.info(f"开始批量项目分析: {len(pending)} 个待处理")

        success = 0
        failed = 0
        for project in pending:
            r = await self.analyze(session, project)
            if r:
                success += 1
            else:
                failed += 1

        await session.commit()
        log.info(f"批量项目分析完成: {success} 成功 / {failed} 失败")
        return {"total": len(pending), "success": success, "failed": failed}

    def _json_or_none(self, data) -> str | None:
        import json
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return None
