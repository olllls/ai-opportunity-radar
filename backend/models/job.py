"""岗位趋势模型"""

from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class JobTrend(Base, TimestampMixin):
    """岗位趋势"""

    __tablename__ = "job_trends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="岗位名称"
    )
    sample_count: Mapped[Optional[int]] = mapped_column(
        Integer, comment="采样数量"
    )
    avg_salary_min: Mapped[Optional[float]] = mapped_column(
        Float, comment="最低薪资(万/年)"
    )
    avg_salary_max: Mapped[Optional[float]] = mapped_column(
        Float, comment="最高薪资(万/年)"
    )
    salary_trend: Mapped[Optional[str]] = mapped_column(
        String(10), comment="up/stable/down"
    )
    market_demand_level: Mapped[Optional[str]] = mapped_column(
        String(10), comment="high/medium/low"
    )
    learning_recommendation: Mapped[Optional[str]] = mapped_column(
        Text, comment="学习建议"
    )
    analysis_date: Mapped[Optional[date]] = mapped_column(
        Date, comment="分析日期"
    )

    skills = relationship("JobSkill", backref="trend", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_trends_date", "analysis_date"),
        Index("idx_trends_role", "role_name"),
    )

    def __repr__(self) -> str:
        return f"<JobTrend {self.role_name}>"


class JobSkill(Base, TimestampMixin):
    """岗位技能"""

    __tablename__ = "job_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trend_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_trends.id"), nullable=False, comment="岗位趋势ID"
    )
    skill_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="技能名称"
    )
    frequency: Mapped[Optional[float]] = mapped_column(
        Float, comment="出现频率%"
    )
    is_new: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否新增需求"
    )

    def __repr__(self) -> str:
        return f"<JobSkill {self.skill_name}>"
