"""创业机会模型"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class StartupOpportunity(Base, TimestampMixin):
    """创业机会"""

    __tablename__ = "startup_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="产品名称"
    )
    product_url: Mapped[Optional[str]] = mapped_column(
        String(500), comment="产品链接"
    )
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="product_hunt/hacker_news/other"
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500), comment="来源链接"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, comment="产品描述")

    analysis = relationship("OpportunityAnalysis", backref="opportunity", uselist=False)

    def __repr__(self) -> str:
        return f"<StartupOpportunity {self.product_name}>"


class OpportunityAnalysis(Base, TimestampMixin):
    """创业机会分析"""

    __tablename__ = "opportunity_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("startup_opportunities.id"), nullable=False, unique=True, comment="机会ID"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), comment="分类"
    )
    target_users: Mapped[Optional[str]] = mapped_column(
        String(500), comment="目标用户"
    )
    business_model: Mapped[Optional[str]] = mapped_column(Text, comment="商业模式")
    pricing_model: Mapped[Optional[str]] = mapped_column(
        String(50), comment="收费方式"
    )
    estimated_mrr: Mapped[Optional[str]] = mapped_column(
        String(100), comment="预估月收入"
    )
    competition_level: Mapped[Optional[str]] = mapped_column(
        String(20), comment="low/medium/high"
    )
    personal_dev_friendly: Mapped[Optional[bool]] = mapped_column(
        Boolean, comment="适合个人开发"
    )
    dev_difficulty: Mapped[Optional[str]] = mapped_column(
        String(20), comment="low/medium/high"
    )
    development_time: Mapped[Optional[str]] = mapped_column(
        String(100), comment="预估开发周期"
    )
    key_features: Mapped[Optional[str]] = mapped_column(
        String(1000), comment="核心功能JSON"
    )
    improvement_suggestion: Mapped[Optional[str]] = mapped_column(
        Text, comment="改进建议"
    )
    opportunity_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="机会评分1-10"
    )
    analysis_date: Mapped[Optional[date]] = mapped_column(
        Date, comment="分析日期"
    )

    __table_args__ = (
        Index("idx_opportunity_score", "opportunity_score"),
    )

    def __repr__(self) -> str:
        return f"<OpportunityAnalysis {self.opportunity_id} score={self.opportunity_score}>"
