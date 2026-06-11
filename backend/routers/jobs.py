"""岗位趋势 API 路由"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.job import JobTrend
from backend.schemas.job import JobTrendSchema
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["岗位趋势"])


@router.get("")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """获取岗位趋势列表"""
    query = (
        select(JobTrend)
        .options(selectinload(JobTrend.skills))
        .order_by(desc(JobTrend.analysis_date))
    )
    total = await db.execute(select(func.count(JobTrend.id)))
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))

    return SuccessResponse(data={
        "items": [JobTrendSchema.model_validate(j) for j in result.scalars().all()],
        "total": total.scalar() or 0,
        "page": page,
        "page_size": page_size,
    })
