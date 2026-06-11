"""AI机会雷达 - 应用入口

FastAPI 应用初始化、路由注册、生命周期管理。
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.config import get_settings
from backend.database import init_db, close_db, get_session_maker
from backend.utils.logger import log, setup_logger, db_log_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # 配置日志
    setup_logger(settings.log_level)

    # 初始化数据库
    await init_db()
    app.state.settings = settings

    # 启动日志写入后台任务
    session_maker = get_session_maker()
    app.state._log_task = asyncio.create_task(db_log_worker(session_maker))

    # 启动调度器
    from backend.services.scheduler import AppScheduler
    scheduler = AppScheduler()
    scheduler.start()
    app.state.scheduler = scheduler

    log.info(f"🚀 {settings.site_name} 启动完成 (http://localhost:8000)")

    yield

    # 关闭时清理
    scheduler.stop()
    await close_db()
    log.info("应用已关闭")


app = FastAPI(
    title="AI机会雷达",
    description="AI Opportunity Radar - 每天5分钟，掌握AI机会",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="backend/templates")
app.state.templates = templates

# Web 页面路由
from backend.web.routes import router as web_router
app.include_router(web_router)

# API 路由
from backend.routers import reports_router, news_router, system_router, dashboard_router, projects_router, opportunities_router, jobs_router
app.include_router(reports_router)
app.include_router(news_router)
app.include_router(system_router)
app.include_router(dashboard_router)
app.include_router(projects_router)
app.include_router(opportunities_router)
app.include_router(jobs_router)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": "1.0.0"}
