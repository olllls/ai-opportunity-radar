"""日报模型"""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class DailyReport(Base, TimestampMixin):
    """日报"""

    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[date] = mapped_column(
        Date, nullable=False, unique=True, comment="日报日期"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="日报标题")
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="日报摘要")
    total_news: Mapped[int] = mapped_column(Integer, default=0, comment="覆盖资讯数")
    total_sources: Mapped[int] = mapped_column(Integer, default=0, comment="覆盖源数")
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending/generating/completed/failed"
    )
    model_used: Mapped[Optional[str]] = mapped_column(String(50), comment="使用模型")
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, comment="输入Token数")
    completion_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, comment="输出Token数"
    )
    generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="生成时间"
    )

    items = relationship("ReportItem", backref="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_reports_date", "report_date"),
        Index("idx_reports_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<DailyReport {self.report_date}>"


class ReportItem(Base, TimestampMixin):
    """日报项目"""

    __tablename__ = "report_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("daily_reports.id"), nullable=False, comment="日报ID"
    )
    section_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="news/tool/project/opportunity/job/action"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, comment="排序号")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="内容JSON")

    def __repr__(self) -> str:
        return f"<ReportItem {self.section_type} #{self.sort_order}>"
