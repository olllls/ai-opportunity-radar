"""开源项目与项目分析模型"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin


class OpenSourceProject(Base, TimestampMixin):
    """开源项目"""

    __tablename__ = "open_source_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="owner/repo"
    )
    repo_url: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="GitHub URL"
    )
    description: Mapped[Optional[str]] = mapped_column(Text, comment="项目描述")
    stars_count: Mapped[int] = mapped_column(Integer, default=0, comment="Star数")
    forks_count: Mapped[int] = mapped_column(Integer, default=0, comment="Fork数")
    primary_lang: Mapped[Optional[str]] = mapped_column(
        String(50), comment="主要编程语言"
    )
    topics: Mapped[Optional[str]] = mapped_column(
        String(500), comment="标签JSON数组"
    )
    license: Mapped[Optional[str]] = mapped_column(String(100), comment="开源协议")
    created_at_github: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="GitHub创建时间"
    )
    updated_at_github: Mapped[Optional[datetime]] = mapped_column(
        DateTime, comment="GitHub更新时间"
    )

    analysis = relationship("ProjectAnalysis", backref="project", uselist=False)

    __table_args__ = (
        Index("idx_projects_stars", "stars_count"),
    )

    def __repr__(self) -> str:
        return f"<OpenSourceProject {self.repo_name}>"


class ProjectAnalysis(Base, TimestampMixin):
    """项目分析结果"""

    __tablename__ = "project_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("open_source_projects.id"), nullable=False, unique=True, comment="项目ID"
    )
    tech_stack: Mapped[Optional[str]] = mapped_column(
        String(500), comment="技术栈JSON"
    )
    star_growth_rate: Mapped[Optional[float]] = mapped_column(
        Float, comment="近7天增长率"
    )
    star_growth_velocity: Mapped[Optional[str]] = mapped_column(
        String(10), comment="fast/stable/slow"
    )
    function_analysis: Mapped[Optional[str]] = mapped_column(Text, comment="功能分析")
    learning_value: Mapped[Optional[int]] = mapped_column(
        Integer, comment="学习价值1-10"
    )
    clone_value: Mapped[Optional[int]] = mapped_column(Integer, comment="复刻价值1-10")
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(20), comment="beginner/intermediate/advanced"
    )
    recommendation_score: Mapped[Optional[float]] = mapped_column(
        Float, comment="推荐指数1-10"
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="中文摘要")
    worth_learning_reason: Mapped[Optional[str]] = mapped_column(
        Text, comment="值得学习的理由"
    )
    worth_cloning_reason: Mapped[Optional[str]] = mapped_column(
        Text, comment="值得复刻的理由"
    )
    similar_projects: Mapped[Optional[str]] = mapped_column(
        String(500), comment="类似项目JSON"
    )
    analysis_date: Mapped[Optional[date]] = mapped_column(
        Date, comment="分析日期"
    )

    __table_args__ = (
        Index("idx_project_analysis_score", "recommendation_score"),
    )

    def __repr__(self) -> str:
        return f"<ProjectAnalysis {self.project_id} score={self.recommendation_score}>"
