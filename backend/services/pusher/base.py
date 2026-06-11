"""推送器基类"""

from abc import ABC, abstractmethod

from backend.utils.logger import log


class BasePusher(ABC):
    """推送器抽象基类"""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def push(self, content: dict) -> bool:
        """执行推送，返回是否成功"""
        pass

    async def push_with_retry(self, content: dict, max_retries: int = 3) -> bool:
        """带重试的推送"""
        import asyncio
        for attempt in range(1, max_retries + 1):
            try:
                success = await self.push(content)
                if success:
                    return True
            except Exception as e:
                log.warning(f"{self.__class__.__name__} 第{attempt}次推送失败: {e}")

            if attempt < max_retries:
                delay = attempt * 60
                log.info(f"{delay}秒后重试...")
                await asyncio.sleep(delay)

        log.error(f"{self.__class__.__name__} 推送失败（已重试{max_retries}次）")
        return False
