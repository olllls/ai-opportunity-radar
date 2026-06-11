"""邮件推送（SMTP）"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from backend.services.pusher.base import BasePusher
from backend.utils.logger import log


class EmailPusher(BasePusher):
    """邮件推送"""

    async def push(self, content: dict) -> bool:
        host = self.config.get("email_smtp_host", "")
        port = self.config.get("email_smtp_port", 587)
        user = self.config.get("email_smtp_user", "")
        password = self.config.get("email_smtp_password", "")
        to_addr = self.config.get("email_to", "")

        if not all([host, user, password, to_addr]):
            log.warning("邮件配置不完整，跳过邮件推送")
            return False

        try:
            html = self._format_html(content)
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📡 AI机会雷达 · {content.get('date', '')}"
            msg["From"] = user
            msg["To"] = to_addr
            msg.attach(MIMEText(html, "html", "utf-8"))

            import asyncio
            def _send():
                with smtplib.SMTP(host, port) as server:
                    server.starttls()
                    server.login(user, password)
                    server.send_message(msg)

            await asyncio.to_thread(_send)
            log.info(f"邮件推送成功: {to_addr}")
            return True
        except Exception as e:
            log.error(f"邮件推送失败: {e}")
            return False

    def _format_html(self, content: dict) -> str:
        """生成简单的HTML邮件"""
        news_html = ""
        for n in content.get("news", [])[:5]:
            level_colors = {"urgent": "#ef4444", "high": "#f97316", "normal": "#6b7280"}
            color = level_colors.get(n.get("attention_level", ""), "#6b7280")
            news_html += f"""
            <div style="border-left:4px solid {color}; padding:12px; margin:8px 0; background:#f9fafb;">
                <strong>{n.get('title', '')}</strong>
                <p style="color:#6b7280; font-size:14px;">{n.get('one_sentence', '')}</p>
            </div>"""

        return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,sans-serif; max-width:640px; margin:0 auto; padding:20px;">
<h1>📡 AI机会雷达 · {content.get('date', '')}</h1>
<p style="color:#6b7280;">阅读时间：约5分钟</p>
<hr>
<h2>🔴 今日重点</h2>
{news_html}
<hr>
<p style="color:#9ca3af; font-size:12px;">
    数据来源：{content.get('total_sources', 0)}个信息源 · {content.get('total_news', 0)}条资讯<br>
    查看完整日报：<a href="{self.config.get('site_url', '')}">{self.config.get('site_url', '')}</a>
</p>
</body></html>"""
