#!/bin/bash
set -euo pipefail

# =============================================================================
# AI 机会雷达 - 部署脚本（服务器端）
# =============================================================================
# 用法:
#   cd /opt/ai-daily
#   bash docker/deploy.sh
# =============================================================================

PROJECT_DIR="/opt/ai-daily"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查前置条件
check_prereqs() {
    if ! command -v docker &>/dev/null; then
        error "Docker 未安装。请先执行服务器初始化。"
        exit 1
    fi
    if ! docker compose version &>/dev/null; then
        error "Docker Compose v2 未安装。"
        exit 1
    fi
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        error ".env 文件缺失。请从 .env.example 复制并填入密钥:"
        echo "  cp .env.example .env"
        echo "  vim .env"
        exit 1
    fi
}

# 部署应用
deploy_app() {
    cd "$PROJECT_DIR"

    # 拉取最新代码
    info "拉取最新代码..."
    if [ -d ".git" ]; then
        git pull
    else
        warn "非 Git 目录，跳过 git pull"
    fi

    # 创建运行时目录
    mkdir -p data logs backup

    # 构建并启动
    cd "$PROJECT_DIR/docker"
    info "构建并启动 Docker 容器..."
    docker compose up -d --build

    # 等待服务就绪
    info "等待服务就绪..."
    for i in {1..12}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            echo ""
            info "✓ 健康检查通过！"
            return 0
        fi
        sleep 5
    done

    echo ""
    warn "健康检查超时，请检查日志:"
    docker compose logs --tail=20 app
    return 1
}

# 显示状态
show_status() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}  部署完成${NC}"
    echo "============================================"
    echo ""
    echo -e "${CYAN}容器状态:${NC}"
    cd "$PROJECT_DIR/docker"
    docker compose ps
    echo ""
    echo -e "${CYAN}快速验证:${NC}"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://<server-ip>/health"
    echo "  curl http://<server-ip>/docs"
    echo ""
    echo -e "${CYAN}导入种子数据:${NC}"
    echo "  docker compose exec app python scripts/seed_data.py"
    echo ""
}

# =============================================================================
main() {
    echo ""
    echo "============================================"
    echo "  AI 机会雷达 - 部署"
    echo "  服务器: $(hostname)"
    echo "============================================"
    echo ""

    check_prereqs
    deploy_app
    show_status
}

main "$@"
