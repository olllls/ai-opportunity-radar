"""系统配置模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class SystemConfig(Base):
    """系统运行时配置"""

    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="配置键名"
    )
    config_value: Mapped[str] = mapped_column(
        Text, nullable=False, comment="配置值JSON"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), comment="配置说明"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<SystemConfig {self.config_key}>"
