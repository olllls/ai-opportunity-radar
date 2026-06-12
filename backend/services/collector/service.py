"""采集编排服务"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.collection_source import CollectionSource
from backend.models.news import NewsItem
from backend.models.opportunity import StartupOpportunity
from backend.models.project import OpenSourceProject
from backend.utils.logger import log
from backend.utils.dedup import is_duplicate
from backend.utils.helpers import compute_content_hash
from backend.services.collector.rss_collector import RSSCollector
from backend.services.collector.hacker_news import HNCollector
from backend.services.collector.github_trending import GitHubTrendingCollector
from backend.services.collector.product_hunt import ProductHuntCollector


COLLECTOR_MAP = {
    "rss": RSSCollector,
    "api": None,  # 根据具体源选择
    "web_scrape": None,
}


def _get_collector(source: dict) -> object | None:
    """根据采集源配置获取对应的采集器实例"""
    collect_type = source.get("collect_type", "")
    name = source.get("name", "")

    if collect_type == "rss":
        return RSSCollector(source)
    if collect_type == "api" and "hacker" in name.lower():
        return HNCollector(source)
    if collect_type == "web_scrape":
        if "github" in name.lower():
            return GitHubTrendingCollector(source)
        if "product" in name.lower():
            return ProductHuntCollector(source)
        # Fallback web scraper
        from backend.services.collector.web_collector import WebCollector
        return WebCollector(source)

    log.warning(f"未知采集类型: {name} / {collect_type}")
    return None


class CollectorService:
    """采集编排服务"""

    async def collect_all(self, session: AsyncSession) -> dict:
        """采集所有活跃源"""
        results = {"total": 0, "new": 0, "failed": 0, "sources": []}

        sources = await session.execute(
            select(CollectionSource).where(CollectionSource.is_active.is_(True))
        )
        sources = sources.scalars().all()

        for source in sources:
            result = await self.collect_source(session, source)
            results["sources"].append(result)
            results["total"] += result.get("total", 0)
            results["new"] += result.get("new", 0)
            results["failed"] += result.get("failed", 0)

        log.info(f"全源采集完成: {results['new']} 新 / {results['total']} 总 / {results['failed']} 失败")
        return results

    async def collect_source(self, session: AsyncSession, source: CollectionSource) -> dict:
        """采集指定源"""
        settings = get_settings()
        source_dict = {
            "id": source.id,
            "name": source.name,
            "collect_type": source.collect_type,
            "feed_url": source.feed_url or "",
            "api_url": source.api_url or "",
            "web_url": source.web_url or "",
            "api_key": settings.product_hunt_token,
        }

        collector = _get_collector(source_dict)
        if not collector:
            return {"source": source.name, "total": 0, "new": 0, "failed": 1, "error": "未知采集类型"}

        raw_items = await collector.collect()
        new_count = 0

        for item in raw_items:
            dup, method = await is_duplicate(session, item.url, item.title, item.summary or "")
            if dup:
                continue

            news = NewsItem(
                source_id=source.id,
                title=item.title,
                url=item.url,
                author=item.author or "",
                published_at=item.published_at,
                summary=item.summary or "",
                content=json.dumps(item.extra, ensure_ascii=False) if item.extra else (item.content or ""),
                content_hash=compute_content_hash(
                    (item.title + (item.summary or item.content or ""))[:2000]
                ),
                status="pending",
            )
            session.add(news)
            new_count += 1

        # Product Hunt 数据同步提取到创业机会表
        if new_count > 0 and "product" in source.name.lower():
            for item in raw_items:
                extra = item.extra or {}
                existing = await session.execute(
                    select(StartupOpportunity).where(StartupOpportunity.product_name == item.title)
                )
                if existing.scalar_one_or_none():
                    continue
                opp = StartupOpportunity(
                    product_name=item.title,
                    product_url=extra.get("website") or item.url,
                    source_type="product_hunt",
                    source_url=item.url,
                    description=extra.get("description") or item.summary or "",
                )
                session.add(opp)

        # GitHub Trending 数据同步提取到开源项目表
        if new_count > 0 and "github" in source.name.lower():
            for item in raw_items:
                extra = item.extra or {}
                existing = await session.execute(
                    select(OpenSourceProject).where(OpenSourceProject.repo_name == item.title)
                )
                if existing.scalar_one_or_none():
                    continue
                project = OpenSourceProject(
                    repo_name=item.title,
                    repo_url=item.url,
                    description=item.summary or "",
                    stars_count=extra.get("stars", 0),
                    primary_lang=extra.get("language", ""),
                )
                session.add(project)

        # 更新采集源状态
        source.last_collected = datetime.now(timezone.utc)
        source.last_status = "success"

        await session.commit()

        log.info(f"{source.name}: 采集 {len(raw_items)} 条，新增 {new_count} 条")
        return {"source": source.name, "total": len(raw_items), "new": new_count, "failed": 0}
