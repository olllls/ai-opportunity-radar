#!/usr/bin/env python3
"""种子数据导入脚本

插入默认配置和采集源数据。
用法：python scripts/seed_data.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logger import setup_logger, log
from sqlalchemy import select

from backend.database import get_session_maker, init_db
from backend.models.collection_source import CollectionSource
from backend.models.config_model import SystemConfig
from backend.models.job import JobTrend, JobSkill
from datetime import date


# 默认采集源
DEFAULT_SOURCES = [
    {
        "name": "OpenAI Blog",
        "source_type": "blog",
        "feed_url": "https://openai.com/blog/rss.xml",
        "web_url": "https://openai.com/blog",
        "collect_type": "rss",
        "collect_interval": 120,
        "is_active": True,
    },
    {
        "name": "Anthropic Blog",
        "source_type": "blog",
        "feed_url": "https://www.anthropic.com/blog/rss.xml",
        "web_url": "https://www.anthropic.com/blog",
        "collect_type": "rss",
        "collect_interval": 120,
        "is_active": True,
    },
    {
        "name": "Google AI Blog",
        "source_type": "blog",
        "feed_url": "https://ai.googleblog.com/feeds/posts/default",
        "web_url": "https://ai.googleblog.com",
        "collect_type": "rss",
        "collect_interval": 120,
        "is_active": True,
    },
    {
        "name": "DeepSeek Blog",
        "source_type": "blog",
        "feed_url": "https://api-docs.deepseek.com/feed.xml",
        "web_url": "https://api-docs.deepseek.com",
        "collect_type": "rss",
        "collect_interval": 120,
        "is_active": True,
    },
    {
        "name": "Hacker News",
        "source_type": "community",
        "api_url": "https://hacker-news.firebaseio.com/v0/",
        "web_url": "https://news.ycombinator.com",
        "collect_type": "api",
        "collect_interval": 60,
        "is_active": True,
    },
    {
        "name": "GitHub Trending",
        "source_type": "trending",
        "web_url": "https://github.com/trending",
        "collect_type": "web_scrape",
        "collect_interval": 360,
        "is_active": True,
    },
    {
        "name": "Product Hunt",
        "source_type": "community",
        "web_url": "https://www.producthunt.com",
        "collect_type": "web_scrape",
        "collect_interval": 360,
        "is_active": True,
    },
]

# 默认系统配置
DEFAULT_CONFIGS = [
    {
        "config_key": "llm_provider",
        "config_value": json.dumps({
            "provider": "deepseek",
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
        }),
        "description": "LLM 服务商配置",
    },
    {
        "config_key": "schedule_time",
        "config_value": json.dumps({
            "collect_start": "06:00",
            "collect_end": "23:00",
            "report_time": "07:30",
            "push_time": "08:00",
        }),
        "description": "定时任务时间配置",
    },
    {
        "config_key": "push_config",
        "config_value": json.dumps({
            "wechat_webhook": "",
            "email_smtp": "",
            "email_from": "",
            "email_to": "",
        }),
        "description": "推送渠道配置",
    },
    {
        "config_key": "app_settings",
        "config_value": json.dumps({
            "site_name": "AI机会雷达",
            "site_url": "http://localhost:8000",
        }),
        "description": "应用设置",
    },
    {
        "config_key": "system_status",
        "config_value": json.dumps({
            "last_report_date": "",
            "last_collect_time": "",
            "total_errors": 0,
        }),
        "description": "系统运行状态",
    },
]

# 默认岗位趋势数据
DEFAULT_JOBS = [
    {
        "role_name": "AI 应用工程师",
        "sample_count": 120,
        "avg_salary_min": 30,
        "avg_salary_max": 60,
        "salary_trend": "up",
        "market_demand_level": "high",
        "learning_recommendation": "掌握 LLM  API 调用、Prompt Engineering、RAG 架构",
        "analysis_date": date(2026, 6, 12),
        "skills": [{"skill_name": "Python", "frequency": 85}, {"skill_name": "LangChain/LlamaIndex", "frequency": 72}, {"skill_name": "RAG 架构", "frequency": 68}, {"skill_name": "Prompt Engineering", "frequency": 80}, {"skill_name": "FastAPI", "frequency": 55}],
    },
    {
        "role_name": "大模型训练/微调工程师",
        "sample_count": 85,
        "avg_salary_min": 40,
        "avg_salary_max": 80,
        "salary_trend": "up",
        "market_demand_level": "high",
        "learning_recommendation": "深入理解 Transformer、LoRA/QLoRA 微调、分布式训练",
        "analysis_date": date(2026, 6, 12),
        "skills": [{"skill_name": "PyTorch", "frequency": 90}, {"skill_name": "DeepSpeed", "frequency": 65}, {"skill_name": "LoRA/QLoRA", "frequency": 78}, {"skill_name": "CUDA", "frequency": 60}, {"skill_name": "分布式训练", "frequency": 70}],
    },
    {
        "role_name": "AI 产品经理",
        "sample_count": 95,
        "avg_salary_min": 25,
        "avg_salary_max": 50,
        "salary_trend": "up",
        "market_demand_level": "high",
        "learning_recommendation": "理解 AI 能力边界、产品化思维、数据分析",
        "analysis_date": date(2026, 6, 12),
        "skills": [{"skill_name": "需求分析", "frequency": 85}, {"skill_name": "数据分析", "frequency": 72}, {"skill_name": "A/B 测试", "frequency": 60}, {"skill_name": "AI 产品设计", "frequency": 78}],
    },
    {
        "role_name": "MLOps / AI 运维工程师",
        "sample_count": 60,
        "avg_salary_min": 30,
        "avg_salary_max": 55,
        "salary_trend": "up",
        "market_demand_level": "medium",
        "learning_recommendation": "掌握 Docker/K8s、模型部署、CI/CD、GPU 运维",
        "analysis_date": date(2026, 6, 12),
        "skills": [{"skill_name": "Docker/K8s", "frequency": 85}, {"skill_name": "CI/CD", "frequency": 70}, {"skill_name": "GPU 运维", "frequency": 55}, {"skill_name": "模型部署", "frequency": 78}, {"skill_name": "Python", "frequency": 75}],
    },
    {
        "role_name": "计算机视觉工程师",
        "sample_count": 70,
        "avg_salary_min": 28,
        "avg_salary_max": 55,
        "salary_trend": "stable",
        "market_demand_level": "medium",
        "learning_recommendation": "掌握 CNN/ViT、目标检测、图像生成技术",
        "analysis_date": date(2026, 6, 12),
        "skills": [{"skill_name": "PyTorch", "frequency": 85}, {"skill_name": "OpenCV", "frequency": 75}, {"skill_name": "目标检测", "frequency": 70}, {"skill_name": "图像生成", "frequency": 55}, {"skill_name": "ONNX/TensorRT", "frequency": 50}],
    },
]


async def seed_data():
    """导入种子数据"""
    Session = get_session_maker()

    async with Session() as session:
        # 检查是否已有数据
        result = await session.execute(select(SystemConfig).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            log.warning("数据库已有初始数据，跳过采集源和配置")
        else:
            # 导入采集源
            for src in DEFAULT_SOURCES:
                source = CollectionSource(**src)
                session.add(source)
            log.info(f"已添加 {len(DEFAULT_SOURCES)} 个采集源")

            # 导入系统配置
            for cfg in DEFAULT_CONFIGS:
                config = SystemConfig(**cfg)
                session.add(config)
            log.info(f"已添加 {len(DEFAULT_CONFIGS)} 个系统配置")

            await session.commit()

        # 导入岗位趋势数据（独立检查，支持增量补充）
        result = await session.execute(select(JobTrend).limit(1))
        existing_jobs = result.scalar_one_or_none()

        if existing_jobs:
            log.warning("岗位数据已存在，跳过导入")
        else:
            for job_data in DEFAULT_JOBS:
                skills = job_data.pop("skills", [])
                trend = JobTrend(**job_data)
                session.add(trend)
                await session.flush()
                for skill in skills:
                    session.add(JobSkill(trend_id=trend.id, **skill))
            await session.commit()
            log.info(f"已添加 {len(DEFAULT_JOBS)} 个岗位趋势")

        log.info("种子数据导入完成！")


if __name__ == "__main__":
    setup_logger("INFO")

    # 先初始化表
    log.info("正在初始化数据库...")
    asyncio.run(init_db())
    log.info("数据库表创建完成")

    # 再导入数据
    asyncio.run(seed_data())
