#!/usr/bin/env python3
"""数据库初始化脚本

用法：
    python scripts/init_db.py          # 初始化数据库
    python scripts/init_db.py --reset  # 删除旧数据库后重新创建
"""

import asyncio
import sys
import os
from pathlib import Path

# 将项目根目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logger import setup_logger
from backend.utils.logger import log
from backend.database import get_engine, get_session_maker
from backend.models.base import Base


async def init_database(reset: bool = False):
    """初始化数据库"""
    # 先导入所有模型以确保 Base.metadata 完整
    from backend.models import (
        CollectionSource, NewsItem, AnalysisResult,
        DailyReport, ReportItem,
        OpenSourceProject, ProjectAnalysis,
        StartupOpportunity, OpportunityAnalysis,
        JobTrend, JobSkill,
        SystemConfig, SystemLog, User,
    )

    db_path = "data/database.db"

    if reset:
        if os.path.exists(db_path):
            os.remove(db_path)
            log.warning(f"已删除旧数据库: {db_path}")

    # 确保 data 目录存在
    Path("data").mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 启用 WAL 和外键
    async with engine.connect() as conn:
        await conn.execute(conn.text("PRAGMA journal_mode = WAL"))
        await conn.execute(conn.text("PRAGMA foreign_keys = ON"))

    log.info("数据库初始化完成！所有表已创建。")

    # 输出表列表
    async with engine.connect() as conn:
        result = await conn.execute(
            conn.text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in result]
        log.info(f"已创建 {len(tables)} 张表: {', '.join(tables)}")


if __name__ == "__main__":
    setup_logger("INFO")
    reset = "--reset" in sys.argv
    asyncio.run(init_database(reset=reset))
