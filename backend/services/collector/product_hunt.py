"""Product Hunt 采集器（GraphQL API 版）"""

from datetime import datetime, timezone

import httpx

from backend.services.collector.base import BaseCollector, RawItem
from backend.utils.logger import log


PH_QUERY = """query {
  posts(first: 20, order: VOTES) {
    edges {
      node {
        id
        name
        tagline
        description
        url
        votesCount
        website
        topics(first: 5) {
          edges {
            node { name }
          }
        }
        createdAt
      }
    }
  }
}"""


class ProductHuntCollector(BaseCollector):
    """Product Hunt 热门产品采集器（GraphQL API）"""

    def __init__(self, source: dict):
        super().__init__(source)
        self.api_url = "https://api.producthunt.com/v2/api/graphql"
        self.token = source.get("api_key", "") or ""

    async def collect(self) -> list[RawItem]:
        items = []
        if not self.token:
            log.warning("Product Hunt: 未配置 API Token，跳过采集")
            return items

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            resp = await self.client.post(
                self.api_url,
                headers=headers,
                json={"query": PH_QUERY},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"Product Hunt API 请求失败: {e}")
            return items

        edges = data.get("data", {}).get("posts", {}).get("edges", [])
        for edge in edges:
            try:
                node = edge.get("node", {})
                name = node.get("name", "")
                tagline = node.get("tagline", "")
                description = node.get("description", "") or tagline
                url = node.get("url", "")
                website = node.get("website", "")
                votes = node.get("votesCount", 0)
                ts = node.get("createdAt")
                published = None
                if ts:
                    try:
                        published = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        published = datetime.now(timezone.utc)

                topics = []
                for t in (node.get("topics", {}).get("edges", [])):
                    tn = t.get("node", {}).get("name", "")
                    if tn:
                        topics.append(tn)

                items.append(RawItem(
                    title=name,
                    url=url,
                    published_at=published or datetime.now(timezone.utc),
                    summary=tagline[:300],
                    content=description[:1000] if description else None,
                    source_id=self.source_id,
                    extra={
                        "votes": votes,
                        "website": website,
                        "topics": topics,
                        "description": description,
                    },
                ))
            except Exception as e:
                log.warning(f"Product Hunt 解析条目失败: {e}")
                continue

        log.info(f"Product Hunt: API 采集完成，获取 {len(items)} 条")
        return items
