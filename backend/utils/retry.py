"""异步重试装饰器 - 支持指数退避和可配置异常类型"""

import asyncio
import functools
from typing import Callable, Optional, Type, Union

from backend.utils.logger import log


def async_retry(
    max_attempts: int = 3,
    delays: Optional[list[Union[int, float]]] = None,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    backoff_factor: float = 2.0,
):
    """异步函数重试装饰器

    Args:
        max_attempts: 最大重试次数
        delays: 自定义延迟列表（秒），优先级高于 backoff_factor
        exceptions: 需要重试的异常类型
        backoff_factor: 指数退避因子，第一次重试延迟 base_delay
    """
    if delays is None:
        delays = [1, 2, 4]  # 默认 1s, 2s, 4s

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        delay_index = min(attempt - 1, len(delays) - 1)
                        delay = delays[delay_index]
                        log.warning(
                            f"{func.__name__} 第 {attempt}/{max_attempts} 次失败: {e}，"
                            f"{delay}秒后重试"
                        )
                        await asyncio.sleep(delay)
                    else:
                        log.error(
                            f"{func.__name__} 重试 {max_attempts} 次均失败: {e}"
                        )

            raise last_exception

        return wrapper

    return decorator
