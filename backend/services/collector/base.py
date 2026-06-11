"""采集器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx


@dataclass
class RawItem:
    """原始采集数据"""
    title: str
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    source_id: Optional[int] = None
    extra: dict = field(default_factory=dict)


class BaseCollector(ABC):
    """采集器抽象基类"""

    def __init__(self, source: dict):
        self.source = source
        self.source_id = source.get("id", 0)
        self.source_name = source.get("name", "unknown")
        self.collect_type = source.get("collect_type", "")
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """获取共享 httpx 客户端（延迟初始化）"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        """关闭共享 httpx 客户端"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    async def collect(self) -> list[RawItem]:
        """执行采集，返回原始数据列表"""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.source_name}>"
