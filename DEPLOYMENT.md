# AI 机会雷达 —— 生产部署指南

> 适用环境：Ubuntu 22.04 LTS · Docker Compose · Nginx · HTTPS

---

## 目录

1. [部署架构](#1-部署架构)
2. [前置条件](#2-前置条件)
3. [服务器初始化](#3-服务器初始化)
4. [项目部署](#4-项目部署)
5. [HTTPS 配置](#5-https-配置)
6. [域名配置](#6-域名配置)
7. [数据备份](#7-数据备份)
8. [日志管理](#8-日志管理)
9. [运维命令](#9-运维命令)
10. [回滚方案](#10-回滚方案)
11. [部署检查清单](#11-部署检查清单)

---

## 1. 部署架构

```
用户 → HTTPS :443
         ↓
    Nginx 容器（TLS 终止 + 反向代理）
         ↓ :8000 (Docker 内部网络)
    FastAPI 容器（Uvicorn + APScheduler）
         │
    Docker 数据卷:
     ├─ data/    → SQLite 数据库文件
     ├─ logs/    → 应用日志
     └─ backup/  → 数据库自动备份
```

| 组件 | 说明 |
|------|------|
| Nginx | TLS 终止、反向代理到 FastAPI、静态文件缓存 |
| FastAPI | 应用服务 + APScheduler 定时任务（内嵌） |
| SQLite | 单文件数据库，通过 volume 持久化 |
| 无外部依赖 | 无需 Redis / PostgreSQL / Celery |

---

## 2. 前置条件

| 资源 | 要求 | 参考 |
|------|------|------|
| 云服务器 | 2C2G+，Ubuntu 22.04 | 阿里云轻量 ~34元/月 |
| 域名 | 1个，已 ICP 备案 | 用于 HTTPS |
| 端口 | 80 (HTTP), 443 (HTTPS) | 安全组/防火墙放行 |
| Docker | 24+ | 通过 apt 安装 |
| Docker Compose | v2 | 通过 apt 安装 |

---

## 3. 服务器初始化

### 3.1 基础环境

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
sudo apt install -y docker.io docker-compose-v2

# 启动 Docker
sudo systemctl enable --now docker

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
# 退出重登或 newgrp docker 生效

# 验证
docker --version && docker compose version
```

### 3.2 放行防火墙端口

```bash
# 如果用 ufw
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status

# 如果用云平台安全组：在控制台放行 80 和 443
```

### 3.3 创建项目目录

```bash
sudo mkdir -p /opt/ai-daily
sudo chown $USER:$USER /opt/ai-daily
cd /opt/ai-daily
mkdir -p data logs backup docker/ssl
```

---

## 4. 项目部署

### 4.1 本地打包上传

```bash
# === 在开发机（Windows）上执行 ===
# 打开 Git Bash 或 WSL

cd /d/admin/projects/ai-daily

# 打包（排除 .env / data / logs / .git 等）
tar czf ai-daily.tar.gz \
  --exclude=.env \
  --exclude=data \
  --exclude=logs \
  --exclude=backup \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude='*.pyc' \
  .

# 上传到服务器（替换 your-server-ip）
scp ai-daily.tar.gz ubuntu@your-server-ip:/opt/ai-daily/
```

### 4.2 服务器上解压与配置

```bash
# === 在服务器上执行 ===
cd /opt/ai-daily
tar xzf ai-daily.tar.gz

# 创建 .env 配置文件
cp .env.example .env
vim .env
```

**`.env` 必须修改的字段：**

```ini
DEEPSEEK_API_KEY=sk-xxx              # 填入真实密钥
SITE_URL=https://your-domain.com     # 改为生产域名

# 推送配置（按需）
WECHAT_WEBHOOK_URL=                  # 企业微信 webhook
EMAIL_SMTP_USER=                     # SMTP 用户名
EMAIL_SMTP_PASSWORD=                 # SMTP 密码/授权码
EMAIL_TO=                            # 接收邮箱
```

### 4.3 启动服务

```bash
cd /opt/ai-daily/docker

# 启动所有容器
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f app
```

### 4.4 验证部署

```bash
# 1. 容器状态
docker compose ps
# 预期输出：app 和 nginx 均为 "Up"

# 2. 应用健康检查（容器内）
curl -s http://localhost:8000/health
# 预期：{"status":"ok","version":"1.0.0"}

# 3. 种子数据
docker compose exec app python scripts/seed_data.py
```

### 4.5 更新部署

```bash
# === 本地打包新版本 → scp 上传后 ===
cd /opt/ai-daily
tar xzf ai-daily.tar.gz

cd docker
docker compose up -d --build
```

---

## 5. HTTPS 配置

### 5.1 certbot 申请证书（推荐）

```bash
# 安装 certbot（需要先停止 nginx 容器或使用独立模式）
sudo apt install -y certbot

# 停止 nginx 容器（certbot standalone 需要 80 端口）
cd /opt/ai-daily/docker
docker compose stop nginx

# 申请证书（替换 your-domain.com）
sudo certbot certonly --standalone -d your-domain.com --email your-email@example.com --agree-tos --non-interactive

# 复制证书到 docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/ai-daily/docker/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem  /opt/ai-daily/docker/ssl/
sudo chown $USER:$USER /opt/ai-daily/docker/ssl/*.pem

# 重启 nginx 容器
docker compose up -d nginx
```

### 5.2 自动续期

创建续期脚本 `/opt/ai-daily/docker/ssl-renew.sh`：

```bash
#!/bin/bash
set -e

DOMAIN="your-domain.com"
EMAIL="your-email@example.com"
NGINX_SSL="/opt/ai-daily/docker/ssl"
COMPOSE_DIR="/opt/ai-daily/docker"

# 临时启动简易 HTTP 服务器用于验证（nginx 容器可能没运行）
docker run --rm -p 80:80 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d $DOMAIN --email $EMAIL --agree-tos --non-interactive

# 复制新证书
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $NGINX_SSL/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem  $NGINX_SSL/
chmod 644 $NGINX_SSL/*.pem

# 重载 nginx
cd $COMPOSE_DIR && docker compose exec nginx nginx -s reload
```

加入 crontab：

```bash
chmod +x /opt/ai-daily/docker/ssl-renew.sh
sudo crontab -e
# 添加：
# 0 3 1 * * /opt/ai-daily/docker/ssl-renew.sh >> /var/log/ssl-renew.log 2>&1
```

---

## 6. 域名配置

### 6.1 DNS 解析

在域名 DNS 管理面板添加 A 记录：

| 记录类型 | 主机记录 | 记录值 |
|---------|---------|--------|
| A | @ | 服务器公网 IP |
| A | www | 服务器公网 IP |

### 6.2 ICP 备案

中国大陆服务器必须备案。通常在云厂商控制台提交：

1. 登录阿里云/腾讯云备案系统
2. 填写主体信息（个人/企业）
3. 填写域名信息
4. 等待管局审核（一般 5-20 天）
5. 备案通过后在服务器上放置备案号

> ⚠️ 未备案域名会被拦截，无法访问 80/443 端口

---

## 7. 数据备份

### 7.1 手动备份

```bash
# 停止应用 → 复制数据库（确保数据一致性）
cd /opt/ai-daily/docker
docker compose stop app
cp /opt/ai-daily/data/database.db /opt/ai-daily/backup/database-$(date +%Y%m%d).db
docker compose start app
```

### 7.2 自动备份脚本

创建 `/opt/ai-daily/docker/backup.sh`：

```bash
#!/bin/bash
set -e

BACKUP_DIR="/opt/ai-daily/backup"
DB_FILE="/opt/ai-daily/data/database.db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# 冷备：停 app 确保数据一致性
cd /opt/ai-daily/docker
docker compose stop app

cp "$DB_FILE" "$BACKUP_DIR/database_$DATE.db"

docker compose start app

# 压缩
gzip -f "$BACKUP_DIR/database_$DATE.db"

# 清理超过 30 天的备份
find "$BACKUP_DIR" -name 'database_*.db.gz' -mtime +$RETENTION_DAYS -delete

echo "[$(date)] 备份完成: database_$DATE.db.gz"
```

添加定时任务：

```bash
chmod +x /opt/ai-daily/docker/backup.sh
sudo crontab -e
# 添加：
# 0 3 * * * /opt/ai-daily/docker/backup.sh >> /var/log/ai-daily-backup.log 2>&1
```

### 7.3 恢复数据库

```bash
cd /opt/ai-daily/docker
docker compose stop app
cp /opt/ai-daily/backup/database_20260612.db.gz /tmp/
gunzip /tmp/database_20260612.db.gz
cp /tmp/database_20260612.db /opt/ai-daily/data/database.db
docker compose start app
```

---

## 8. 日志管理

### 8.1 日志轮转（logrotate）

创建 `/etc/logrotate.d/ai-daily`：

```
/opt/ai-daily/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

### 8.2 日志查看

```bash
# 应用日志
docker compose logs -f app

# 最近 100 行
docker compose logs --tail=100 app

# Nginx 日志
docker compose logs -f nginx

# 宿主机日志文件
tail -f /opt/ai-daily/logs/app.log
```

---

## 9. 运维命令

| 场景 | 命令 |
|------|------|
| 启动所有服务 | `cd /opt/ai-daily/docker && docker compose up -d` |
| 停止所有服务 | `cd /opt/ai-daily/docker && docker compose down` |
| 重启应用 | `docker compose restart app` |
| 重建并重启 | `docker compose up -d --build app` |
| 查看状态 | `docker compose ps` |
| 查看资源占用 | `docker stats` |
| 进入容器 | `docker compose exec app bash` |
| 查看日志 | `docker compose logs -f app` |
| 手动采集 | `curl -X POST https://your-domain.com/api/v1/system/collect` |
| 手动生成日报 | `curl -X POST https://your-domain.com/api/v1/reports/generate` |
| 手动推送 | `curl -X POST https://your-domain.com/api/v1/system/push/retry` |
| 查看配置 | `docker compose exec app python -c "from backend.config import get_settings; s=get_settings(); print(s.model_dump())"` |

---

## 10. 回滚方案

### 10.1 回滚到上一版本

```bash
# 如果保留旧压缩包
cd /opt/ai-daily
tar xzf ai-daily_rollback.tar.gz

cd docker
docker compose up -d --build
```

### 10.2 回滚数据库

```bash
# 从备份恢复
cp /opt/ai-daily/backup/database_20260611.db.gz /tmp/
gunzip -f /tmp/database_20260611.db.gz
docker compose stop app
cp /tmp/database_20260611.db /opt/ai-daily/data/database.db
docker compose start app
```

### 10.3 回滚后验证

```bash
curl -s https://your-domain.com/health
curl -s https://your-domain.com/
```

---

## 11. 部署检查清单

### 阶段一：服务器就绪

- [ ] 云服务器已购买（2C2G+, Ubuntu 22.04）
- [ ] 域名已购买 + ICP 备案完成
- [ ] DNS A 记录已指向服务器 IP（已生效）
- [ ] SSH 可登录服务器
- [ ] 安全组/防火墙已放行 80 和 443
- [ ] Docker 已安装并启动
- [ ] Docker Compose v2 已安装

### 阶段二：项目就绪（本地操作）

- [ ] `.env` 已填入真实 API 密钥
- [ ] `.dockerignore` 已创建（防密钥泄漏）
- [ ] `SITE_URL` 已改为生产域名
- [ ] Nginx 配置中 `proxy_pass http://app:8000`（非 localhost）
- [ ] `docker-compose.yml` 已添加 nginx 服务
- [ ] SSL 证书文件准备就绪
- [ ] 本地打包测试通过：`docker compose up -d` 正常运行

### 阶段三：首次部署

- [ ] 项目已上传到 `/opt/ai-daily`
- [ ] 运行时目录已创建：`data/ logs/ backup/ docker/ssl/`
- [ ] `.env` 已从 `.env.example` 复制并按生产填写
- [ ] HTTPS 证书已申请并放入 `docker/ssl/`
- [ ] `docker compose up -d` 成功
- [ ] 两个容器均正常运行
- [ ] `curl localhost:8000/health` 返回 ok
- [ ] `curl https://your-domain.com/health` 可访问
- [ ] 种子数据已导入：`docker compose exec app python scripts/seed_data.py`
- [ ] 首页可访问：`curl https://your-domain.com`
- [ ] API 文档可访问：`https://your-domain.com/docs`

### 阶段四：上线后配置

- [ ] certbot 自动续期 crontab 已配置
- [ ] 每日数据库备份 crontab 已配置
- [ ] logrotate 日志轮转已配置
- [ ] 备份恢复流程已验证

### 阶段五：验收

- [ ] 自动采集定时任务按计划触发
- [ ] 日报生成正常（次日 07:30 检查）
- [ ] 推送送达正常（企业微信/邮件）
- [ ] Web 页面访问正常
- [ ] 容器内存占用 < 512MB

---

## 附录 A：关键文件路径

| 文件/目录 | 路径（服务器） |
|-----------|--------------|
| 项目根目录 | `/opt/ai-daily/` |
| 数据库文件 | `/opt/ai-daily/data/database.db` |
| 应用日志 | `/opt/ai-daily/logs/` |
| 备份目录 | `/opt/ai-daily/backup/` |
| SSL 证书 | `/opt/ai-daily/docker/ssl/` |
| Nginx 配置 | `/opt/ai-daily/docker/nginx.conf` |
| Docker Compose | `/opt/ai-daily/docker/docker-compose.yml` |
| 环境变量 | `/opt/ai-daily/.env` |
| 备份脚本 | `/opt/ai-daily/docker/backup.sh` |
| SSL 续期脚本 | `/opt/ai-daily/docker/ssl-renew.sh` |

## 附录 B：所需新增/修改的文件清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `.dockerignore` | **新增** | 防止 `.env` 密钥和 data/ 进入镜像 |
| `docker/nginx.conf` | **新增** | Nginx 反向代理 + HTTPS 配置 |
| `docker/docker-compose.yml` | **修改** | 增加 nginx 服务，app 改为 expose |
| `docker/ssl-renew.sh` | **新增** | certbot 自动续期脚本 |
| `docker/backup.sh` | **新增** | 容器级 SQLite 冷备脚本 |
| `docker/Dockerfile` | **可选修改** | 添加非 root 用户（P1 建议） |
| `.env` 中 `SITE_URL` | **修改** | 改为生产域名 |
