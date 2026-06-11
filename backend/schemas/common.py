"""通用响应模型"""

from __future__ import annotations

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict | list | None = None


class PaginatedResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict | None = None


class ErrorResponse(BaseModel):
    code: int = 400
    message: str
    detail: str | None = None


class PaginationMeta(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
