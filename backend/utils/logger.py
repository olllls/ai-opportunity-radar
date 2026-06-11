"""日志配置 - 基于 loguru

日志文件按天滚动，保留30天。
同时将日志写入数据库 system_logs 表。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from queue import Queue as ThreadQueue

from loguru import logger


# 数据库日志队列（线程安全，loguru sink 在后台线程调用）
_db_log_queue: ThreadQueue | None = None


def get_db_log_queue() -> ThreadQueue:
    global _db_log_queue
    if _db_log_queue is None:
        _db_log_queue = ThreadQueue(maxsize=500)
    return _db_log_queue


async def db_log_worker(session_maker):
    """后台任务: 将日志队列写入数据库"""
    queue = get_db_log_queue()
    while True:
        batch = []
        # Drain queue (non-blocking, up to 10 at a time)
        while not queue.empty() and len(batch) < 10:
            try:
                batch.append(queue.get_nowait())
            except Exception:
                break

        if not batch:
            await asyncio.sleep(2)
            continue

        try:
            from backend.models.log import SystemLog
            async with session_maker() as session:
                for item in batch:
                    session.add(SystemLog(**item))
                await session.commit()
        except Exception:
            pass  # 日志写入失败不影响主流程


def enqueue_db_log(msg):
    """loguru sink: 将日志记录放入异步队列"""
    import sys as _sys
    try:
        record = msg.record

        detail = None
        if record.get("exception"):
            import traceback
            detail = "".join(traceback.format_exception(*record["exception"]))

        queue = get_db_log_queue()
        queue.put_nowait({
            "log_level": record["level"].name,
            "module": record["name"].split(".")[-1] if "." in record["name"] else record["name"],
            "message": record["message"][:1000],
            "detail": detail[:5000] if detail else None,
        })
    except Exception as e:
        print(f"[db_log] Error: {e}", file=_sys.stderr)


def setup_logger(log_level: str = "INFO", log_dir: str = "logs"):
    """配置日志系统"""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 移除默认 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan> | <level>{message}</level>",
        colorize=True,
    )

    # 文件输出（按天滚动，保留30天）
    logger.add(
        log_path / "app-{time:YYYY-MM-DD}.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} | {message}",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        enqueue=True,
    )

    # 错误日志单独文件
    logger.add(
        log_path / "error-{time:YYYY-MM-DD}.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} | {message}",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        enqueue=True,
    )

    # 数据库日志 sink（无 format，接收原始记录 dict）
    logger.add(
        enqueue_db_log,
        level=log_level,
    )

    return logger


# 模块级默认 logger
log = logger
