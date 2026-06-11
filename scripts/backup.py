#!/usr/bin/env python3
"""数据库备份脚本

每天备份 SQLite 数据库，保留最近 7 天。

用法：
    python scripts/backup.py                    # 执行备份
    python scripts/backup.py --keep 14          # 保留14天
    python scripts/backup.py --force            # 立即备份（不检查最后备份时间）
"""

import os
import shutil
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.logger import setup_logger, log
from backend.database import get_engine


DEFAULT_KEEP_DAYS = 7
DB_PATH = "data/database.db"
BACKUP_DIR = "backup"
STATUS_FILE = "backup/backup_status.json"


def get_last_backup_date() -> str | None:
    """获取最后一次备份日期"""
    try:
        status_path = Path(STATUS_FILE)
        if status_path.exists():
            data = json.loads(status_path.read_text())
            return data.get("last_backup_date")
    except Exception:
        pass
    return None


def save_backup_status(date_str: str, file_size: int):
    """保存备份状态"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    status = {
        "last_backup_date": date_str,
        "last_backup_time": datetime.now().isoformat(),
        "file_size_bytes": file_size,
    }
    Path(STATUS_FILE).write_text(json.dumps(status, indent=2))


def clean_old_backups(keep_days: int):
    """清理超过保留天数的备份"""
    backup_path = Path(BACKUP_DIR)
    if not backup_path.exists():
        return

    cutoff = datetime.now() - timedelta(days=keep_days)
    removed = 0

    for f in backup_path.glob("database-*.db*"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
                removed += 1
        except Exception as e:
            log.warning(f"删除备份失败 {f}: {e}")

    if removed:
        log.info(f"已清理 {removed} 个旧备份文件")


async def backup_database(force: bool = False, keep_days: int = DEFAULT_KEEP_DAYS):
    """执行数据库备份"""
    db_path = Path(DB_PATH)

    if not db_path.exists():
        log.error(f"数据库文件不存在: {DB_PATH}")
        return False

    # 检查是否今天已经备份过
    today = datetime.now().strftime("%Y-%m-%d")
    if not force:
        last_date = get_last_backup_date()
        if last_date == today:
            log.info("今天已经备份过了，跳过（使用 --force 强制备份）")
            return True

    # 创建备份目录
    backup_path = Path(BACKUP_DIR)
    backup_path.mkdir(parents=True, exist_ok=True)

    # 备份文件名
    backup_file = backup_path / f"database-{today}.db"
    backup_gz = backup_path / f"database-{today}.db.gz"

    try:
        # 确保数据库连接关闭
        engine = get_engine()
        await engine.dispose()

        # 复制文件
        shutil.copy2(db_path, backup_file)
        file_size = backup_file.stat().st_size

        # 压缩（可选）
        try:
            import gzip
            with open(backup_file, "rb") as f_in:
                with gzip.open(backup_gz, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file.unlink()  # 删除未压缩的
            log.info(f"备份完成 (已压缩): {backup_gz} ({file_size / 1024:.1f} KB)")
        except Exception:
            log.info(f"备份完成: {backup_file} ({file_size / 1024:.1f} KB)")

        # 保存备份状态
        save_backup_status(today, file_size)

        # 清理旧备份
        clean_old_backups(keep_days)

        return True

    except Exception as e:
        log.error(f"备份失败: {e}")
        return False


if __name__ == "__main__":
    import asyncio

    setup_logger("INFO")

    force = "--force" in sys.argv
    keep_days = DEFAULT_KEEP_DAYS

    for arg in sys.argv:
        if arg.startswith("--keep="):
            try:
                keep_days = int(arg.split("=")[1])
            except ValueError:
                pass

    log.info(f"开始备份 (保留 {keep_days} 天)...")
    success = asyncio.run(backup_database(force=force, keep_days=keep_days))

    sys.exit(0 if success else 1)
