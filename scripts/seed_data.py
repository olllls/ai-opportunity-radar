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


async def seed_data():
    """导入种子数据"""
    Session = get_session_maker()

    async with Session() as session:
        # 检查是否已有数据
        result = await session.execute(select(SystemConfig).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            log.warning("数据库已有种子数据，跳过导入")
            log.warning("如需重新导入，请先执行 python scripts/init_db.py --reset")
            return

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
        log.info("种子数据导入完成！")


if __name__ == "__main__":
    setup_logger("INFO")

    # 先初始化表
    log.info("正在初始化数据库...")
    asyncio.run(init_db())
    log.info("数据库表创建完成")

    # 再导入数据
    asyncio.run(seed_data())
