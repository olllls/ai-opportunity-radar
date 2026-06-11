"""日报 API 路由"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.reporter.service import ReportService
from backend.schemas.report import ReportListItem, ReportDetail, GenerateResponse
from backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1/reports", tags=["日报"])
report_service = ReportService()


@router.get("")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """获取日报列表（分页）"""
    data = await report_service.get_reports(db, page=page, page_size=page_size)
    return SuccessResponse(data=data)


@router.get("/today")
async def get_today_report(db: AsyncSession = Depends(get_db)):
    """获取今日日报"""
    report = await report_service.get_today(db)
    if not report:
        raise HTTPException(status_code=404, detail="今日暂无日报")
    return SuccessResponse(data=report)


@router.get("/{date_str}")
async def get_report_by_date(date_str: str, db: AsyncSession = Depends(get_db)):
    """获取指定日期日报"""
    from backend.utils.helpers import parse_date
    report_date = parse_date(date_str)
    if not report_date:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用 YYYY-MM-DD")
    report = await report_service.get_by_date(db, report_date)
    if not report:
        raise HTTPException(status_code=404, detail=f"{date_str} 暂无日报")
    return SuccessResponse(data=report)


@router.post("/generate")
async def generate_report(db: AsyncSession = Depends(get_db)):
    """手动生成日报"""
    result = await report_service.generate_report(db)
    return SuccessResponse(data=GenerateResponse(**result).model_dump())
