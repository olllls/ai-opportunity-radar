"""去重工具 - URL精确匹配 + 标题相似度 + 内容哈希"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.news import NewsItem
from backend.utils.helpers import levenshtein_similarity, compute_content_hash


TITLE_SIMILARITY_THRESHOLD = 0.85


async def is_duplicate(
    session: AsyncSession,
    url: str,
    title: str,
    content: str = "",
) -> tuple[bool, str]:
    """三重去重检查

    Returns:
        (是否重复, 匹配方式)
    """
    # 1. URL 精确匹配
    result = await session.execute(
        select(NewsItem).where(NewsItem.url == url).limit(1)
    )
    if result.scalar_one_or_none():
        return True, "url"

    # 2. 内容哈希匹配
    if content:
        content_hash = compute_content_hash(content[:2000])
        result = await session.execute(
            select(NewsItem).where(NewsItem.content_hash == content_hash).limit(1)
        )
        if result.scalar_one_or_none():
            return True, "content_hash"

    # 3. 标题相似度匹配
    all_titles = await session.execute(
        select(NewsItem.title).order_by(NewsItem.created_at.desc()).limit(200)
    )
    for (existing_title,) in all_titles:
        if levenshtein_similarity(title, existing_title) >= TITLE_SIMILARITY_THRESHOLD:
            return True, "title_similarity"

    return False, ""
