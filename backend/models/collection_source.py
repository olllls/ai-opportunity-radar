"""采集源配置模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class CollectionSource(Base, TimestampMixin):
    """采集源配置"""

    __tablename__ = "collection_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="采集源名称")
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="blog/community/trending"
    )
    feed_url: Mapped[Optional[str]] = mapped_column(String(500), comment="RSS地址")
    api_url: Mapped[Optional[str]] = mapped_column(String(500), comment="API地址")
    web_url: Mapped[Optional[str]] = mapped_column(String(500), comment="网页URL")
    collect_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="rss/api/web_scrape"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    collect_interval: Mapped[int] = mapped_column(
        Integer, default=120, comment="采集间隔(分钟)"
    )
    last_collected: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="最后采集时间"
    )
    last_status: Mapped[Optional[str]] = mapped_column(
        String(20), comment="success/failed"
    )
    config: Mapped[Optional[str]] = mapped_column(Text, comment="额外配置JSON")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<CollectionSource {self.name}>"
