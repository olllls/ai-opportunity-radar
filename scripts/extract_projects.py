#!/usr/bin/env python3
"""从 news_items 中提取 GitHub Trending 数据到 open_source_projects"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from backend.database import get_session_maker, init_db
from backend.models.news import NewsItem
from backend.models.project import OpenSourceProject
from backend.utils.logger import setup_logger, log


async def extract_projects():
    Session = get_session_maker()
    async with Session() as session:
        result = await session.execute(
            select(NewsItem).where(NewsItem.source_id == 6)
        )
        items = result.scalars().all()
        log.info(f"GitHub Trending news items: {len(items)}")

        count = 0
        for item in items:
            repo_name = item.title.strip()
            if "/" not in repo_name:
                continue

            existing = await session.execute(
                select(OpenSourceProject).where(OpenSourceProject.repo_name == repo_name)
            )
            if existing.scalar_one_or_none():
                continue

            description = item.summary or ""
            repo_url = item.url

            # Try to parse stars/language from content (stored as JSON extra)
            stars = 0
            language = None
            if item.content:
                try:
                    extra = json.loads(item.content)
                    if isinstance(extra, dict):
                        stars = extra.get("stars", 0)
                        language = extra.get("language")
                except (json.JSONDecodeError, ValueError):
                    pass

            project = OpenSourceProject(
                repo_name=repo_name,
                repo_url=repo_url,
                description=description[:500],
                stars_count=stars,
                forks_count=0,
                primary_lang=language,
            )
            session.add(project)
            count += 1

        await session.commit()
        log.info(f"提取完成: 新增 {count} 个项目")


if __name__ == "__main__":
    setup_logger("INFO")
    asyncio.run(init_db())
    asyncio.run(extract_projects())
