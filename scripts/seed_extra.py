#!/usr/bin/env python3
"""种子数据：创业机会 + 岗位数据"""

import asyncio, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from sqlalchemy import select
from backend.database import get_session_maker
from backend.models.opportunity import StartupOpportunity, OpportunityAnalysis
from backend.models.job import JobTrend, JobSkill

OPPORTUNITIES = [
    {
        "product_name": "AI Code Review Assistant",
        "product_url": "https://example.com/ai-code-review",
        "source_type": "other",
        "description": "Automated code review tool powered by LLM that provides contextual suggestions, security vulnerability detection, and best practice enforcement.",
        "analysis": {"category": "developer-tools", "business_model": "SaaS 订阅", "personal_dev_friendly": True, "dev_difficulty": "medium", "opportunity_score": 8, "improvement_suggestion": "可增加团队协作分析和代码健康度仪表盘"},
    },
    {
        "product_name": "Personal AI Learning Tutor",
        "product_url": "https://example.com/ai-tutor",
        "source_type": "other",
        "description": "Adaptive learning platform with personalized study plans, practice problems, and real-time AI feedback.",
        "analysis": {"category": "education", "business_model": "免费增值", "personal_dev_friendly": True, "dev_difficulty": "medium", "opportunity_score": 9, "improvement_suggestion": "集成 Anki 间隔重复算法提升学习效率"},
    },
    {
        "product_name": "AI Workflow Automation Agent",
        "product_url": "https://example.com/ai-workflow",
        "source_type": "other",
        "description": "AI agent automating repetitive workflows across SaaS tools: web research, data entry, email drafting, report generation.",
        "analysis": {"category": "productivity", "business_model": "按用量计费", "personal_dev_friendly": True, "dev_difficulty": "medium", "opportunity_score": 8, "improvement_suggestion": "增加自定义工作流模板市场和第三方API集成"},
    },
    {
        "product_name": "AI Content Localization Platform",
        "product_url": "https://example.com/ai-l10n",
        "source_type": "other",
        "description": "AI-powered content localization that translates marketing content, documentation, and UI while preserving brand voice.",
        "analysis": {"category": "content-creation", "business_model": "SaaS 订阅", "personal_dev_friendly": True, "dev_difficulty": "low", "opportunity_score": 7, "improvement_suggestion": "提供 API 方便集成到 CI/CD 流程"},
    },
    {
        "product_name": "AI-Powered Data Dashboard",
        "product_url": "https://example.com/ai-dashboard",
        "source_type": "other",
        "description": "Natural language interface for BI that lets non-technical users query data and generate visualizations in plain English.",
        "analysis": {"category": "business-intelligence", "business_model": "SaaS 订阅", "personal_dev_friendly": False, "dev_difficulty": "high", "opportunity_score": 7, "improvement_suggestion": "先聚焦单一垂直领域（如电商）降低复杂度"},
    },
]

JOBS = [
    {
        "role_name": "AI/ML Engineer",
        "sample_count": 150, "avg_salary_min": 40.0, "avg_salary_max": 90.0,
        "salary_trend": "up", "market_demand_level": "high",
        "learning_recommendation": "重点掌握 PyTorch、Transformers、RAG 架构。学习 HuggingFace 生态和 LangChain 框架。",
        "skills": [("PyTorch", 85), ("Python", 90), ("LangChain", 65), ("RAG", 55), ("Transformers", 70), ("Docker", 60), ("AWS", 55)],
    },
    {
        "role_name": "LLM Application Developer",
        "sample_count": 120, "avg_salary_min": 35.0, "avg_salary_max": 80.0,
        "salary_trend": "up", "market_demand_level": "high",
        "learning_recommendation": "掌握 Prompt Engineering、Function Calling、RAG 模式。学习 OpenAI SDK 和 Anthropic SDK。",
        "skills": [("Python", 85), ("Prompt Engineering", 75), ("RAG", 60), ("FastAPI", 55), ("Vector Database", 50), ("TypeScript", 45), ("React", 40)],
    },
    {
        "role_name": "MLOps Engineer",
        "sample_count": 80, "avg_salary_min": 45.0, "avg_salary_max": 95.0,
        "salary_trend": "up", "market_demand_level": "high",
        "learning_recommendation": "学习 MLflow、Kubeflow、模型监控。掌握 CI/CD for ML、模型版本管理。",
        "skills": [("Docker", 80), ("Kubernetes", 75), ("MLflow", 60), ("Python", 70), ("AWS SageMaker", 55), ("CI/CD", 65), ("Terraform", 50)],
    },
    {
        "role_name": "AI Product Manager",
        "sample_count": 100, "avg_salary_min": 35.0, "avg_salary_max": 75.0,
        "salary_trend": "up", "market_demand_level": "medium",
        "learning_recommendation": "理解 AI 能力边界，掌握 Prompt Engineering 基础，学习 AI 产品评估方法论。",
        "skills": [("Product Strategy", 80), ("AI/ML Fundamentals", 70), ("Data Analysis", 65), ("Prompt Engineering", 50), ("A/B Testing", 60), ("User Research", 55)],
    },
    {
        "role_name": "Computer Vision Engineer",
        "sample_count": 70, "avg_salary_min": 38.0, "avg_salary_max": 85.0,
        "salary_trend": "stable", "market_demand_level": "medium",
        "learning_recommendation": "掌握 OpenCV、YOLO、Stable Diffusion。学习多模态模型和视频理解技术。",
        "skills": [("PyTorch", 80), ("OpenCV", 75), ("Python", 75), ("YOLO", 60), ("Stable Diffusion", 55), ("ONNX", 45), ("C++", 50)],
    },
]

async def seed():
    session_maker = get_session_maker()
    async with session_maker() as session:
        existing = await session.execute(select(JobTrend).limit(1))
        if existing.scalar_one_or_none():
            print("Jobs already seeded, skipping")
            return

        for data in OPPORTUNITIES:
            analysis_cfg = data.pop("analysis")
            opp = StartupOpportunity(**data)
            session.add(opp)
            await session.flush()
            analysis = OpportunityAnalysis(opportunity_id=opp.id, analysis_date=date.today(), **analysis_cfg)
            session.add(analysis)
        print(f"Seeded {len(OPPORTUNITIES)} opportunities")

        for data in JOBS:
            skills_list = data.pop("skills")
            job = JobTrend(**data, analysis_date=date.today())
            session.add(job)
            await session.flush()
            for skill_name, freq in skills_list:
                session.add(JobSkill(trend_id=job.id, skill_name=skill_name, frequency=freq, is_new=freq >= 50))
        print(f"Seeded {len(JOBS)} job roles")

        await session.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(seed())
