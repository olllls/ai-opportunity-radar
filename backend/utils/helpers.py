"""通用工具函数"""

import re
from datetime import datetime, date
from typing import Optional


def format_date(dt: Optional[datetime]) -> str:
    """格式化日期为 YYYY-MM-DD"""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d")


def format_datetime(dt: Optional[datetime]) -> str:
    """格式化为 YYYY-MM-DD HH:mm:ss"""
    if dt is None:
        return ""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_date(date_str: str) -> Optional[date]:
    """解析 YYYY-MM-DD 格式的日期字符串"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """截断文本到指定长度"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + suffix


def is_valid_url(url: str) -> bool:
    """检查 URL 是否有效"""
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def compute_content_hash(text: str) -> str:
    """计算内容的 SHA256 哈希（用于去重）"""
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def levenshtein_similarity(s1: str, s2: str) -> float:
    """计算两个字符串的 Levenshtein 相似度 (0.0 - 1.0)"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    s1, s2 = s1.lower(), s2.lower()
    m, n = len(s1), len(s2)

    # 使用优化的一维 DP
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr[j] = min(
                curr[j - 1] + 1,      # 插入
                prev[j] + 1,          # 删除
                prev[j - 1] + cost,   # 替换
            )
        prev = curr

    max_len = max(m, n)
    if max_len == 0:
        return 1.0
    return 1.0 - prev[n] / max_len


def safe_int(value, default: int = 0) -> int:
    """安全转换为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def clamp(value: int, min_val: int = 1, max_val: int = 10) -> int:
    """将值限制在指定范围内"""
    return max(min_val, min(value, max_val))
