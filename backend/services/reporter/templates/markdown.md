# 📡 AI机会雷达 · {{ date }}

**阅读时间：约5分钟** | 生成时间：{{ generated_at }}

---

## 🔴 今日重点新闻

{% for item in news %}
### {{ loop.index }}. {{ item.title }}
**关注等级：** {{ item.attention_level | upper }}
**一句话：** {{ item.one_sentence }}
**重要度：** {{ item.importance_score }}/10 | **学习价值：** {{ item.learning_score }}/10
**商业价值：** {{ item.business_score }}/10 | **创业价值：** {{ item.startup_score }}/10
[原文链接]({{ item.url }})

{% endfor %}
---

## 🛠️ AI工具推荐

{% for item in tools %}
### {{ item.title }}
**评分：** {{ item.importance_score }}/10 | **来源：** {{ item.source }}
{{ item.one_sentence }}

{% endfor %}
---

## ⭐ GitHub热门项目

{% for item in projects %}
### {{ item.repo_name }}
⭐ {{ item.stars_count }} | **技术栈：** {{ item.tech_stack }}
**推荐指数：** {{ item.recommendation_score }}/10
**是否值得学习：** {{ item.worth_learning }}
**是否值得复刻：** {{ item.worth_cloning }}
{{ item.summary }}

{% endfor %}
---

## 💡 创业机会分析

{% for item in opportunities %}
### {{ item.product_name }}
**商业模式：** {{ item.business_model }}
**适合个人开发：** {{ item.personal_dev_friendly }}
**机会评分：** {{ item.opportunity_score }}/10

{% endfor %}
---

## 📊 AI岗位趋势

{% for item in jobs %}
### {{ item.role_name }}
**市场需求：** {{ item.market_demand_level }}
**高频技能：** {{ item.skills | join(', ') }}
**学习建议：** {{ item.learning_recommendation }}

{% endfor %}
---

## 🎯 今日行动建议

{% for action in actions %}
- {{ action }}
{% endfor %}

---

> 数据来源：{{ total_sources }}个信息源 · {{ total_news }}条资讯
> 关注等级：🔴 urgent = 立即关注 | 🟠 high = 值得关注 | ⚪ normal = 一般信息
