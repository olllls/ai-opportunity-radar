"""系统日志模型"""

from typing import Optional

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class SystemLog(Base, TimestampMixin):
    """系统运行日志"""

    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_level: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="INFO/WARNING/ERROR/CRITICAL"
    )
    module: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="collector/analyzer/report/push/web"
    )
    message: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="日志消息"
    )
    detail: Mapped[Optional[str]] = mapped_column(Text, comment="详细信息JSON")

    __table_args__ = (
        Index("idx_logs_level", "log_level"),
        Index("idx_logs_module", "module"),
        Index("idx_logs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SystemLog [{self.log_level}] {self.module}: {self.message[:50]}>"
