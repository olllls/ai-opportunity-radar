"""LLM API 客户端封装

支持 DeepSeek / 通义千问 / GLM / OpenAI。
所有 API 兼容 OpenAI SDK 格式。
"""

import json
import time
from typing import Optional

from openai import AsyncOpenAI

from backend.config import get_settings
from backend.utils.logger import log
from backend.utils.retry import async_retry


class LLMClient:
    """LLM API 客户端"""

    def __init__(self, provider: Optional[str] = None):
        settings = get_settings()
        config = settings.llm_config if provider is None else self._get_provider_config(settings, provider)

        api_key = config.get("api_key", "")
        if not api_key:
            raise ValueError(f"LLM provider '{provider or settings.llm_provider}' API Key 未配置")

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=config["base_url"],
        )
        self.model = config["model"]
        self.provider = provider or settings.llm_provider
        self._no_llm = False
        log.info(f"LLM客户端初始化: {self.provider} / {self.model}")

    @property
    def available(self) -> bool:
        return not self._no_llm

    def _get_provider_config(self, settings, provider: str) -> dict:
        configs = {
            "deepseek": {"api_key": settings.deepseek_api_key, "base_url": settings.deepseek_api_base, "model": settings.deepseek_model},
            "tongyi": {"api_key": settings.tongyi_api_key, "base_url": settings.tongyi_api_base, "model": settings.tongyi_model},
            "glm": {"api_key": settings.glm_api_key, "base_url": settings.glm_api_base, "model": settings.glm_model},
            "openai": {"api_key": settings.openai_api_key, "base_url": settings.openai_api_base, "model": settings.openai_model},
        }
        return configs.get(provider, configs["deepseek"])

    @async_retry(max_attempts=3, delays=[5, 15, 30])
    async def chat(self, messages: list, temperature: float = 0.3, max_tokens: int = 2048) -> dict:
        """标准对话补全"""
        start = time.time()
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        elapsed = time.time() - start
        result = {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            "elapsed_ms": int(elapsed * 1000),
        }
        log.debug(f"LLM调用完成: {result['usage']['total_tokens']} tokens, {result['elapsed_ms']}ms")
        return result

    async def chat_with_json(self, messages: list, temperature: float = 0.3, max_tokens: int = 2048) -> dict:
        """JSON 模式对话补全（失败即降级，不重试）"""
        """JSON 模式对话补全"""
        if self._no_llm:
            raise RuntimeError("LLM 不可用（余额不足）")

        start = time.time()
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "Insufficient Balance" in err_str or "insufficient_quota" in err_str:
                log.warning(f"LLM API 余额不足，切换到无 LLM 模式")
                self._no_llm = True
            raise

        elapsed = time.time() - start
        raw = response.choices[0].message.content
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            log.error(f"JSON解析失败: {e}, raw={raw[:200]}")
            raise ValueError(f"LLM响应JSON解析失败: {e}")

        result = {
            "content": parsed,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            "elapsed_ms": int(elapsed * 1000),
        }
        return result
