#!/bin/bash
set -euo pipefail

# =============================================================================
# AI 机会雷达 - SQLite 冷备脚本
# =============================================================================
# 用法: bash docker/backup.sh
# 定时: 0 3 * * * /opt/ai-daily/docker/backup.sh >> /var/log/ai-daily-backup.log 2>&1
# =============================================================================

PROJECT_DIR="/opt/ai-daily"
BACKUP_DIR="$PROJECT_DIR/backup"
DB_FILE="$PROJECT_DIR/data/database.db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 停应用 → 冷拷贝（保证数据一致性）
cd "$PROJECT_DIR/docker"
docker compose stop app
cp "$DB_FILE" "$BACKUP_DIR/database_$DATE.db"
docker compose start app

# 压缩
gzip -f "$BACKUP_DIR/database_$DATE.db"

# 清理过期备份
find "$BACKUP_DIR" -name 'database_*.db.gz' -mtime +$RETENTION_DAYS -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ 备份完成: database_$DATE.db.gz"
echo "   备份目录: $BACKUP_DIR"
echo "   保留天数: $RETENTION_DAYS"
