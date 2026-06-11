"""AI机会雷达 - 配置管理

配置加载优先级：
1. .env 文件（启动时加载，不可变）
2. system_config 数据库表（运行时可变，覆盖 .env）
3. 代码默认值（最低优先级）
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从 .env 文件加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----- LLM API 配置 -----
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    tongyi_api_key: str = ""
    tongyi_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    tongyi_model: str = "qwen-plus"

    glm_api_key: str = ""
    glm_api_base: str = "https://open.bigmodel.cn/api/paas/v4"
    glm_model: str = "glm-4-plus"

    openai_api_key: str = ""
    openai_api_base: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # 默认 LLM 提供商
    llm_provider: str = "deepseek"

    # ----- 数据库 -----
    database_url: str = "sqlite+aiosqlite:///./data/database.db"

    # ----- 推送配置 -----
    wechat_webhook_url: str = ""
    email_smtp_host: str = "smtp.qq.com"
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_smtp_password: str = ""
    email_to: str = ""

    # ----- 应用设置 -----
    site_name: str = "AI机会雷达"
    site_url: str = "http://localhost:8000"

    # ----- 定时任务 -----
    collect_start_time: str = "06:00"
    collect_end_time: str = "23:00"
    report_generate_time: str = "07:30"
    push_time: str = "08:00"

    # ----- 调试 -----
    log_level: str = "INFO"
    debug: bool = False

    @property
    def llm_config(self) -> dict:
        """获取当前 LLM 提供商的配置"""
        provider = self.llm_provider
        configs = {
            "deepseek": {
                "api_key": self.deepseek_api_key,
                "base_url": self.deepseek_api_base,
                "model": self.deepseek_model,
            },
            "tongyi": {
                "api_key": self.tongyi_api_key,
                "base_url": self.tongyi_api_base,
                "model": self.tongyi_model,
            },
            "glm": {
                "api_key": self.glm_api_key,
                "base_url": self.glm_api_base,
                "model": self.glm_model,
            },
            "openai": {
                "api_key": self.openai_api_key,
                "base_url": self.openai_api_base,
                "model": self.openai_model,
            },
        }
        return configs.get(provider, configs["deepseek"])

    @property
    def available_providers(self) -> list[str]:
        """返回已配置 API Key 的可用提供商列表"""
        available = []
        if self.deepseek_api_key:
            available.append("deepseek")
        if self.tongyi_api_key:
            available.append("tongyi")
        if self.glm_api_key:
            available.append("glm")
        if self.openai_api_key:
            available.append("openai")
        return available


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
