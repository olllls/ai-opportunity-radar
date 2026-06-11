"""新闻资讯模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class NewsItem(Base, TimestampMixin):
    """新闻资讯"""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("collection_sources.id"), nullable=False, comment="采集源ID"
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="标题")
    url: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="原文链接"
    )
    author: Mapped[Optional[str]] = mapped_column(String(200), comment="作者")
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="发布时间"
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="原文摘要")
    content: Mapped[Optional[str]] = mapped_column(Text, comment="原文内容")
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), comment="内容哈希(去重)"
    )
    language: Mapped[str] = mapped_column(
        String(10), default="en", comment="语言"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending/analyzed/failed"
    )

    source = relationship("CollectionSource", backref="news_items")
    analysis = relationship("AnalysisResult", backref="news_item", uselist=False)

    __table_args__ = (
        Index("idx_news_status", "status"),
        Index("idx_news_published", "published_at"),
        Index("idx_news_source", "source_id"),
        Index("idx_news_url", "url"),
        Index("idx_news_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<NewsItem {self.title[:50]}>"
