"""GitHub Trending 采集器"""

from datetime import datetime, timezone

from backend.services.collector.web_collector import WebCollector
from backend.services.collector.base import RawItem
from backend.utils.logger import log


class GitHubTrendingCollector(WebCollector):
    """GitHub Trending 热门项目采集器"""

    async def collect(self) -> list[RawItem]:
        items = []
        soup = await self._get_soup("https://github.com/trending?since=daily")
        if not soup:
            return items

        articles = soup.select("article.Box-row")
        if not articles:
            articles = soup.select("article")  # fallback

        for article in articles[:15]:
            try:
                h2 = article.select_one("h2")
                if not h2:
                    continue
                repo_full = h2.get_text(strip=True).replace(" ", "")
                repo_url = f"https://github.com/{repo_full}"

                desc_el = article.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                stars_el = article.select_one("a[href*='/stargazers']")
                stars_text = stars_el.get_text(strip=True) if stars_el else "0"
                stars = self._parse_stars(stars_text)

                lang_el = article.select_one("[itemprop='programmingLanguage']")
                lang = lang_el.get_text(strip=True) if lang_el else ""

                items.append(RawItem(
                    title=repo_full,
                    url=repo_url,
                    author="",
                    published_at=datetime.now(timezone.utc),
                    summary=description[:300],
                    content=None,
                    source_id=self.source_id,
                    extra={"stars": stars, "language": lang},
                ))
            except Exception as e:
                log.warning(f"GitHub Trending 解析条目失败: {e}")
                continue

        log.info(f"GitHub Trending: 采集完成，获取 {len(items)} 条")
        return items

    def _parse_stars(self, text: str) -> int:
        text = text.strip().replace(",", "")
        if "k" in text.lower():
            return int(float(text.lower().replace("k", "")) * 1000)
        try:
            return int(text)
        except ValueError:
            return 0
