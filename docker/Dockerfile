# =============================================================================
# AI机会雷达 - Docker 镜像
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（仅保留必要库，lxml 使用预编译 wheel）
RUN apt-get update \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# 创建运行时目录
RUN mkdir -p data logs backup

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read())"

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
