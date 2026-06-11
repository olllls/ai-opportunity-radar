"""网页抓取采集器基类"""

from __future__ import annotations

from abc import abstractmethod

from bs4 import BeautifulSoup

from backend.services.collector.base import BaseCollector, RawItem
from backend.utils.logger import log


class WebCollector(BaseCollector):
    """网页抓取采集器"""

    def __init__(self, source: dict):
        super().__init__(source)
        self.web_url = source.get("web_url", "")
        self.timeout = 30
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        ]

    @abstractmethod
    async def collect(self) -> list[RawItem]:
        pass

    async def _get_soup(self, url: str) -> BeautifulSoup | None:
        """GET 请求并返回 BeautifulSoup 对象（使用共享客户端）"""
        import random
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        try:
            resp = await self.client.get(url, headers=headers)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            log.error(f"{self.source_name} 抓取失败: {e} {url}")
        return None
