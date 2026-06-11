"""API 采集器基类"""

from __future__ import annotations

from abc import abstractmethod

import httpx

from backend.services.collector.base import BaseCollector, RawItem
from backend.utils.logger import log


class APICollector(BaseCollector):
    """REST API 采集器"""

    def __init__(self, source: dict):
        super().__init__(source)
        self.api_url = source.get("api_url", "")
        self.timeout = 30

    @abstractmethod
    async def collect(self) -> list[RawItem]:
        pass

    async def _get_json(self, url: str) -> dict | list | None:
        """GET 请求并返回 JSON（使用共享客户端）"""
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            log.error(f"{self.source_name} HTTP错误: {e.response.status_code} {url}")
        except httpx.TimeoutException:
            log.error(f"{self.source_name} 超时: {url}")
        except Exception as e:
            log.error(f"{self.source_name} 请求失败: {e} {url}")
        return None
