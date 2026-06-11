"""系统 API 路由"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.config_model import SystemConfig
from backend.models.log import SystemLog
from backend.services.scheduler import AppScheduler
from backend.schemas.system import SystemConfigSchema, ConfigUpdate, LogEntry, CollectResponse, PushResponse
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/system", tags=["系统"])


# ---------- 配置 ----------

@router.get("/config")
async def get_config(db: AsyncSession = Depends(get_db)):
    """获取所有系统配置"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    return SuccessResponse(data=[
        SystemConfigSchema.model_validate(c).model_dump() for c in configs
    ])


@router.get("/config/{config_key}")
async def get_config_by_key(config_key: str, db: AsyncSession = Depends(get_db)):
    """获取指定配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == config_key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail=f"配置 {config_key} 不存在")
    return SuccessResponse(data=SystemConfigSchema.model_validate(config).model_dump())


@router.put("/config/{config_key}")
async def update_config(config_key: str, body: ConfigUpdate, db: AsyncSession = Depends(get_db)):
    """更新配置"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.config_key == config_key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail=f"配置 {config_key} 不存在")
    config.config_value = body.config_value
    await db.commit()
    return SuccessResponse(data=SystemConfigSchema.model_validate(config).model_dump())


# ---------- 手动操作 ----------

scheduler = AppScheduler()


@router.post("/collect")
async def manual_collect():
    """手动触发全源采集"""
    result = await scheduler.trigger_collect()
    return SuccessResponse(data=CollectResponse(**result).model_dump())


@router.post("/analyze")
async def manual_analyze():
    """手动触发AI分析"""
    result = await scheduler.trigger_analyze()
    return SuccessResponse(data=result)


@router.post("/report")
async def manual_generate():
    """手动生成日报"""
    result = await scheduler.trigger_report()
    return SuccessResponse(data=result)


@router.post("/push")
async def manual_push():
    """手动推送日报"""
    result = await scheduler.trigger_push()
    return SuccessResponse(data=PushResponse(**result).model_dump())


# ---------- 日志 ----------

@router.get("/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    level: str | None = Query(None, pattern="^(INFO|WARNING|ERROR|CRITICAL)$"),
    module: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """查看系统日志"""
    query = select(SystemLog).order_by(desc(SystemLog.created_at))
    count_query = select(func.count(SystemLog.id))

    if level:
        query = query.where(SystemLog.log_level == level)
        count_query = count_query.where(SystemLog.log_level == level)
    if module:
        query = query.where(SystemLog.module == module)
        count_query = count_query.where(SystemLog.module == module)

    total = await db.execute(count_query)
    total_count = total.scalar() or 0

    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )
    logs = result.scalars().all()

    return SuccessResponse(data={
        "items": [LogEntry.model_validate(l) for l in logs],
        "total": total_count,
        "page": page,
        "page_size": page_size,
    })
