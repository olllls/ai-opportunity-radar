"""RSS Feed 采集器"""

from datetime import datetime, timezone
from typing import Optional

import feedparser

from backend.services.collector.base import BaseCollector, RawItem
from backend.utils.logger import log


class RSSCollector(BaseCollector):
    """RSS / Atom Feed 采集器"""

    def __init__(self, source: dict):
        super().__init__(source)
        self.feed_url = source.get("feed_url", "")
        self.web_url = source.get("web_url", "")
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )

    async def collect(self) -> list[RawItem]:
        items = []
        if not self.feed_url:
            log.warning(f"{self.source_name}: 未配置 feed_url")
            return items

        try:
            # feedparser 是同步的，用 asyncio 的线程池执行
            import asyncio
            feed = await asyncio.to_thread(
                feedparser.parse, self.feed_url
            )

            if feed.bozo and not feed.entries:
                log.error(f"{self.source_name}: RSS解析失败: {feed.bozo_exception}")
                return items

            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                if not title or not link:
                    continue

                published = self._parse_date(
                    entry.get("published_parsed") or entry.get("updated_parsed")
                )
                author = entry.get("author", "")
                summary = entry.get("summary", "") or entry.get("description", "")
                content = ""
                if hasattr(entry, "content"):
                    content = entry.content[0].get("value", "") if entry.content else ""

                items.append(RawItem(
                    title=title,
                    url=link,
                    author=author or None,
                    published_at=published,
                    summary=summary[:500] if summary else None,
                    content=content[:5000] if content else None,
                    source_id=self.source_id,
                ))

            log.info(f"{self.source_name}: RSS采集完成，获取 {len(items)} 条")

        except Exception as e:
            log.error(f"{self.source_name}: RSS采集失败: {e}")

        return items

    def _parse_date(self, parsed) -> Optional[datetime]:
        """解析 feedparser 的时间格式"""
        if parsed is None:
            return None
        try:
            import time
            ts = time.mktime(parsed)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception:
            return None
