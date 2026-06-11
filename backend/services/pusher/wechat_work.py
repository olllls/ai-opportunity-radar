"""企业微信机器人推送"""

import json

import httpx

from backend.services.pusher.base import BasePusher
from backend.utils.logger import log


class WechatWorkPusher(BasePusher):
    """企业微信机器人推送"""

    async def push(self, content: dict) -> bool:
        webhook = self.config.get("wechat_webhook", "")
        if not webhook:
            log.warning("企业微信Webhook未配置")
            return False

        message = self._format_message(content)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook, json={
                    "msgtype": "markdown",
                    "markdown": {"content": message},
                })
                if resp.status_code == 200:
                    log.info("企业微信推送成功")
                    return True
                else:
                    log.error(f"企业微信推送失败: {resp.status_code} {resp.text}")
                    return False
        except Exception as e:
            log.error(f"企业微信推送异常: {e}")
            return False

    def _format_message(self, content: dict) -> str:
        """格式化为企微Markdown消息（限制2048字节）"""
        lines = [f"# 📡 AI机会雷达 · {content.get('date', '')}\n"]

        # 重点新闻
        news = content.get("news", [])
        if news:
            lines.append("**🔴 今日重点**")
            for n in news[:5]:
                level_icon = {"urgent": "🔴", "high": "🟠", "normal": "⚪"}.get(n.get("attention_level", ""), "⚪")
                lines.append(f">{level_icon} [{n.get('attention_level', '').upper()}] {n.get('title', '')}")
                if n.get("one_sentence"):
                    lines.append(f"> 一句话：{n['one_sentence']}")
            lines.append("")

        # GitHub项目
        projects = content.get("projects", [])
        if projects:
            lines.append("**⭐ 热门开源**")
            for p in projects[:3]:
                lines.append(f"- {p.get('repo_name', '')} ⭐ {p.get('stars_count', 0)}")
                if p.get("summary"):
                    lines.append(f"  {p['summary'][:50]}")
            lines.append("")

        # 行动建议
        actions = content.get("actions", [])
        if actions:
            lines.append("**🎯 行动建议**")
            for a in actions[:2]:
                lines.append(f"- {a}")
            lines.append("")

        url = self.config.get("site_url", "")
        if url:
            lines.append(f"[查看完整日报]({url})")

        msg = "\n".join(lines)
        # 截断到2048字节（企微限制）
        if len(msg.encode("utf-8")) > 2048:
            msg = msg[:2000] + "\n\n...（完整日报请查看Web页面）"
        return msg
