"""用户模型（预留）"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class User(Base):
    """用户（预留，多用户模式时使用）"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="用户名"
    )
    email: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, comment="邮箱"
    )
    password_hash: Mapped[str] = mapped_column(
        String(256), nullable=False, comment="密码哈希"
    )
    nickname: Mapped[Optional[str]] = mapped_column(
        String(100), comment="昵称"
    )
    role: Mapped[str] = mapped_column(
        String(20), default="user", comment="user/admin"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否激活"
    )
    preferences: Mapped[Optional[str]] = mapped_column(
        Text, comment="偏好设置JSON"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"
