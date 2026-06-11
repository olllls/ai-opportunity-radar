"""AI分析结果模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class AnalysisResult(Base, TimestampMixin):
    """AI分析结果"""

    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    news_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("news_items.id"), nullable=False, unique=True, comment="关联资讯ID"
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="AI中文摘要")
    categories: Mapped[Optional[str]] = mapped_column(
        String(500), comment="分类标签JSON数组"
    )
    importance_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="重要程度1-10"
    )
    learning_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="学习价值1-10"
    )
    business_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="商业价值1-10"
    )
    startup_score: Mapped[Optional[int]] = mapped_column(
        Integer, comment="创业价值1-10"
    )
    attention_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="low/normal/high/urgent"
    )
    developer_impact: Mapped[Optional[str]] = mapped_column(
        Text, comment="开发者影响"
    )
    industry_impact: Mapped[Optional[str]] = mapped_column(
        Text, comment="行业影响"
    )
    one_sentence: Mapped[Optional[str]] = mapped_column(
        String(200), comment="一句话总结"
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(
        String(100), comment="建议行动"
    )
    model_used: Mapped[Optional[str]] = mapped_column(
        String(50), comment="使用模型"
    )
    prompt_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, comment="输入Token数"
    )
    completion_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, comment="输出Token数"
    )
    analysis_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer, comment="分析耗时ms"
    )

    __table_args__ = (
        Index("idx_analysis_attention", "attention_level"),
        Index("idx_analysis_importance", "importance_score"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisResult news={self.news_item_id} score={self.importance_score}>"
