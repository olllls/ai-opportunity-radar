"""推送服务编排"""

from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.report import DailyReport
from backend.services.pusher.wechat_work import WechatWorkPusher
from backend.services.pusher.email import EmailPusher
from backend.services.reporter.service import ReportService
from backend.utils.logger import log


class PushService:
    """推送服务"""

    def __init__(self):
        self.report_service = ReportService()
        self._pushers = None

    def _get_pushers(self) -> list:
        if self._pushers is None:
            settings = get_settings()
            config = {
                "wechat_webhook": settings.wechat_webhook_url,
                "email_smtp_host": settings.email_smtp_host,
                "email_smtp_port": settings.email_smtp_port,
                "email_smtp_user": settings.email_smtp_user,
                "email_smtp_password": settings.email_smtp_password,
                "email_to": settings.email_to,
                "site_url": settings.site_url,
            }
            self._pushers = []
            if config.get("wechat_webhook"):
                self._pushers.append(WechatWorkPusher(config))
            if config.get("email_smtp_host") and config.get("email_smtp_user"):
                self._pushers.append(EmailPusher(config))
        return self._pushers

    async def push_report(self, session: AsyncSession, report_date: date | None = None) -> dict:
        """推送指定日期的日报"""
        if report_date is None:
            report_date = date.today()

        report_data = await self.report_service.get_by_date(session, report_date)
        if not report_data:
            log.warning(f"{report_date} 日报不存在，无法推送")
            return {"success": False, "error": "日报不存在"}

        pushers = self._get_pushers()
        if not pushers:
            log.warning("未配置推送渠道")
            return {"success": False, "error": "未配置推送渠道"}

        content = {
            "date": report_data["report_date"],
            "news": report_data["sections"].get("news", []),
            "projects": report_data["sections"].get("projects", []),
            "actions": report_data["sections"].get("actions", []),
            "total_news": report_data["total_news"],
            "total_sources": report_data["total_sources"],
        }

        results = []
        for pusher in pushers:
            success = await pusher.push_with_retry(content)
            results.append({"channel": pusher.__class__.__name__, "success": success})

        log.info(f"推送完成: {results}")
        return {"success": True, "results": results}
