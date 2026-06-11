"""Product Hunt 采集器"""

from datetime import datetime, timezone

from backend.services.collector.web_collector import WebCollector
from backend.services.collector.base import RawItem
from backend.utils.logger import log


class ProductHuntCollector(WebCollector):
    """Product Hunt 热门产品采集器"""

    async def collect(self) -> list[RawItem]:
        items = []
        soup = await self._get_soup("https://www.producthunt.com/")
        if not soup:
            return items

        # 尝试多种选择器适配 Product Hunt 的页面结构
        posts = soup.select("a[href*='/posts/']") or soup.select('[class*="post"] a[href*="/posts/"]')

        seen = set()
        for post in posts[:20]:
            try:
                href = post.get("href", "")
                if not href or "/posts/" not in href:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                full_url = f"https://www.producthunt.com{href}" if href.startswith("/") else href
                title = post.get_text(strip=True) or ""

                # 找父级中的描述
                parent = post.parent
                desc = ""
                for _ in range(5):
                    if parent:
                        desc_el = parent.select_one("p, [class*='description'], [class*='tagline']")
                        if desc_el:
                            desc = desc_el.get_text(strip=True)
                            break
                        parent = parent.parent

                items.append(RawItem(
                    title=title[:200],
                    url=full_url,
                    summary=desc[:300] if desc else None,
                    source_id=self.source_id,
                    published_at=datetime.now(timezone.utc),
                ))
            except Exception as e:
                log.warning(f"Product Hunt 解析条目失败: {e}")
                continue

        log.info(f"Product Hunt: 采集完成，获取 {len(items)} 条")
        return items
