"""Hacker News 采集器"""

from datetime import datetime, timezone
from typing import Optional

from backend.services.collector.api_collector import APICollector
from backend.services.collector.base import RawItem
from backend.utils.logger import log


class HNCollector(APICollector):
    """Hacker News 热门故事采集器"""

    async def collect(self) -> list[RawItem]:
        items = []

        # 1. 获取最新故事 ID
        story_ids = await self._get_json(f"{self.api_url}topstories.json")
        if not story_ids:
            return items

        # 2. 取前 30 条
        top_ids = story_ids[:30]

        # 3. 逐条获取详情
        for story_id in top_ids:
            detail = await self._get_json(f"{self.api_url}item/{story_id}.json")
            if not detail or detail.get("type") != "story":
                continue

            title = detail.get("title", "").strip()
            url = detail.get("url", "") or f"https://news.ycombinator.com/item?id={story_id}"
            if not title:
                continue

            ts = detail.get("time", 0)
            published = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None

            items.append(RawItem(
                title=title,
                url=url,
                author=detail.get("by", ""),
                published_at=published,
                summary=f"▲ {detail.get('score', 0)} points | {detail.get('descendants', 0)} comments",
                content=None,
                source_id=self.source_id,
            ))

        log.info(f"Hacker News: 采集完成，获取 {len(items)} 条")
        return items
