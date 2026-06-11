"""数据库引擎与会话管理

使用 SQLAlchemy 异步模式 + aiosqlite。
SQLite 配置 WAL 模式提升并发性能。
"""

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import get_settings
from backend.utils.logger import log
from backend.models.base import Base


# 延迟初始化：引擎和会话在 lifespan 中创建
_engine = None
_async_session_maker = None


def get_engine():
    """获取数据库引擎"""
    global _engine
    if _engine is None:
        settings = get_settings()

        # 确保数据目录存在
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            connect_args={
                "check_same_thread": False,
            },
        )
        log.info(f"数据库引擎已创建: {db_path}")
    return _engine


def get_session_maker():
    """获取会话工厂"""
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_maker


async def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    maker = get_session_maker()
    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库：创建所有表"""
    engine = get_engine()
    from backend.models import Base as ModelBase
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)

    # 启用 WAL 模式和外键约束
    async with engine.connect() as conn:
        await conn.execute(
            text("PRAGMA journal_mode = WAL")
        )
        await conn.execute(
            text("PRAGMA foreign_keys = ON")
        )

    log.info("数据库初始化完成（所有表已创建）")


async def close_db():
    """关闭数据库连接"""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        log.info("数据库连接已关闭")
