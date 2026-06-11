"""任务调度器 - APScheduler 集成"""

from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.config import get_settings
from backend.database import get_session_maker
from backend.services.collector.service import CollectorService
from backend.services.analyzer.service import AnalyzerService
from backend.services.reporter.service import ReportService
from backend.services.pusher.service import PushService
from backend.utils.logger import log


class AppScheduler:
    """应用任务调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collector = CollectorService()
        self.analyzer = AnalyzerService()
        self.reporter = ReportService()
        self.pusher = PushService()

    def start(self):
        if self.scheduler.running:
            log.warning("调度器已在运行")
            return

        settings = get_settings()

        # 1. 采集任务：每2小时执行
        self.scheduler.add_job(
            self._run_collect,
            IntervalTrigger(hours=2, start_date=datetime.now() + timedelta(seconds=30)),
            id="collect_all",
            name="全源采集",
            replace_existing=True,
        )

        # 2. 分析任务：每天07:00
        self.scheduler.add_job(
            self._run_analyze,
            CronTrigger(hour=7, minute=0),
            id="analyze_pending",
            name="AI分析",
            replace_existing=True,
        )

        # 3. 日报生成：每天07:30
        self.scheduler.add_job(
            self._run_generate_report,
            CronTrigger(hour=7, minute=30),
            id="generate_report",
            name="日报生成",
            replace_existing=True,
        )

        # 4. 推送任务：每天08:00
        self.scheduler.add_job(
            self._run_push,
            CronTrigger(hour=8, minute=0),
            id="push_report",
            name="推送通知",
            replace_existing=True,
        )

        self.scheduler.start()
        log.info("任务调度器已启动（采集/2h | 分析/07:00 | 日报/07:30 | 推送/08:00）")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            log.info("任务调度器已停止")

    async def _run_collect(self):
        """执行全源采集"""
        log.info("[定时任务] 开始全源采集")
        maker = get_session_maker()
        async with maker() as session:
            try:
                result = await self.collector.collect_all(session)
                log.info(f"[定时任务] 采集完成: {result}")
            except Exception as e:
                log.error(f"[定时任务] 采集失败: {e}")

    async def _run_analyze(self):
        """执行AI分析"""
        log.info("[定时任务] 开始AI分析")
        maker = get_session_maker()
        async with maker() as session:
            try:
                result = await self.analyzer.analyze_pending(session)
                log.info(f"[定时任务] 分析完成: {result}")
            except Exception as e:
                log.error(f"[定时任务] 分析失败: {e}")

    async def _run_generate_report(self):
        """生成日报"""
        log.info("[定时任务] 开始生成日报")
        maker = get_session_maker()
        async with maker() as session:
            try:
                result = await self.reporter.generate_report(session)
                log.info(f"[定时任务] 日报生成: {result}")
            except Exception as e:
                log.error(f"[定时任务] 日报生成失败: {e}")

    async def _run_push(self):
        """推送日报"""
        log.info("[定时任务] 开始推送")
        maker = get_session_maker()
        async with maker() as session:
            try:
                result = await self.pusher.push_report(session)
                log.info(f"[定时任务] 推送完成: {result}")
            except Exception as e:
                log.error(f"[定时任务] 推送失败: {e}")

    async def trigger_collect(self):
        """手动触发采集"""
        maker = get_session_maker()
        async with maker() as session:
            return await self.collector.collect_all(session)

    async def trigger_analyze(self):
        """手动触发分析"""
        maker = get_session_maker()
        async with maker() as session:
            return await self.analyzer.analyze_pending(session)

    async def trigger_report(self):
        """手动触发生成日报"""
        maker = get_session_maker()
        async with maker() as session:
            return await self.reporter.generate_report(session)

    async def trigger_push(self):
        """手动触发推送"""
        maker = get_session_maker()
        async with maker() as session:
            return await self.pusher.push_report(session)
