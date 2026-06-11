# AI机会雷达 — 项目上下文 (PROJECT_CONTEXT)

> 生成日期：2026-06-10 | 用于 Claude Code 上下文压缩后快速恢复

---

## 项目概述

自动采集7个AI信息源，利用LLM分析并每日生成中文AI机会日报的聚合平台。目标用户在5分钟内掌握AI领域关键动态与商业机会。

**当前阶段**：MVP核心链路编码完成，API路由层和业务层已实现，正在补充P1分析器和Web模板。
**API Key**：已配置 DeepSeek API（已验证通过）。

---

## 文档结构

| 文档 | 职责 | 读者 |
|------|------|------|
| `README.md` | 项目简介、功能列表、技术栈、启动指南、Docker部署 | GitHub访客/新开发者 |
| `docs/PRD.md` | 项目背景、用户画像、痛点矩阵、功能需求、MVP范围、产品路线图 | 产品经理视角 |
| `docs/architecture.md` | 系统架构图、模块设计、数据流、ER图、API清单、部署架构、ADR | 架构师/开发者 |
| `docs/planning.md` | 开发哲学、阶段规划、里程碑、风险管理、版本路线图 | 项目经理视角 |
| `docs/task.md` | P0/P1/P2任务分组、工时/状态/前置依赖、进度统计 | 开发者视角 |
| `PROJECT_CONTEXT.md` | 本文件：压缩上下文后的快速恢复入口 | Claude Code |

---

## 技术栈

| 层 | 技术 | 备注 |
|----|------|------|
| 后端框架 | FastAPI (Python 3.11) | 异步高性能，自动API文档(Swagger) |
| 数据库 | SQLite + SQLAlchemy 2.0 (async) | 10张表，WAL模式，可迁PostgreSQL |
| 模板引擎 | Jinja2 + TailwindCSS (CDN) | 响应式，零构建工具 |
| 任务调度 | APScheduler | 进程内调度，4个定时任务 |
| LLM API | DeepSeek / 通义千问 / GLM / OpenAI | OpenAI兼容SDK封装，可切换Provider |
| 数据采集 | httpx + feedparser + BeautifulSoup4 | 7个源，3种采集方式 |
| 推送 | 企业微信Webhook / SMTP邮件 | 抽象基类设计，失败重试3次 |
| 部署 | Docker + docker-compose | 数据卷持久化，健康检查 |

---

## 已完成内容

### 基础设施
- [x] 项目目录结构（backend/ scripts/ docker/ docs/ 完整布局）
- [x] 配置管理（config.py，pydantic-settings，4个LLM提供商切换）
- [x] 数据库引擎（异步SQLAlchemy + WAL模式 + 自动建表）
- [x] 10张ORM模型表（完整字段、索引、外键、关系）
- [x] 工具函数（loguru日志、async重试装饰器、日期/文本/哈希/相似度）

### 数据采集
- [x] BaseCollector 抽象基类
- [x] RSS采集器（feedparser，适配所有标准RSS/Atom）
- [x] API采集器（httpx异步，Hacker News适配）
- [x] Web抓取器（BeautifulSoup + UA轮换，GitHub Trending + Product Hunt）
- [x] CollectorService（全源采集编排 + 三重去重写入）
- [x] 种子数据（7个采集源 + 5条系统配置）

### AI分析
- [x] LLM客户端（OpenAI兼容SDK封装，chat / chat_with_json，自动重试，Token统计）
- [x] NewsAnalyzer（资讯级分析：四维评分 + attention_level + 摘要）
- [x] 批量分析（asyncio.Semaphore并发控制，最多50条/批）
- [x] Aggregator（当日趋势总结 + 热点提取）
- [x] AnalyzerService（pending分析编排 + 单条重分析）

### 日报生成
- [x] ReportGenerator（6板块编排：要闻/工具/开源/创业/岗位/行动）
- [x] 行动建议生成（LLM调用，2-3条可执行建议）
- [x] 数据筛选排序（attention_level优先，评分加权）
- [x] ReportService（生成/查询/列表，JSON格式化输出）

### 推送通知
- [x] BasePusher 抽象基类 + push_with_retry（3次重试，指数退避）
- [x] WechatWorkPusher（Markdown格式化，2048字节限制）
- [x] EmailPusher（SMTP + HTML模板）
- [x] PushService（渠道遍历 + 结果日志）

### 任务调度
- [x] AppScheduler（全源采集/2h、AI分析/07:00、日报生成/07:30、推送/08:00）
- [x] 手动触发接口（trigger_collect/analyze/report/push 方法）

### Web页面
- [x] 页面路由（/daily /news /config /logs，Jinja2渲染）
- [x] base.html（导航栏 + TailwindCSS + 暗黑模式 + 响应式）
- [x] reports.html（日报列表，空状态处理）
- [x] report.html（6板块渲染，关注等级颜色标签，评分展示）
- [x] news/config/logs 占位页面
- [x] 静态资源（style.css：评分进度条/关注等级/打印样式/main.js：交互）

### 部署
- [x] Dockerfile + docker-compose.yml
- [x] init_db.py / seed_data.py / backup.py 脚本

### 文档
- [x] README.md（精简版，GitHub导向）
- [x] docs/PRD.md（产品视角，9章节完整PRD）
- [x] docs/architecture.md（架构师视角，Mermaid图表+8章节）
- [x] docs/planning.md（项目经理视角，甘特图+ADR+版本路线）
- [x] docs/task.md（P0/P1/P2分组，57个任务）
- [x] .env.example / .gitignore / requirements.txt

---

## 未完成内容

### P0（阻塞级 — 已完成 ✅）
- [x] REST API路由：/api/v1/reports（列表/今日/指定日期/手动生成）
- [x] REST API路由：/api/v1/news（列表/详情/手动分析/待分析统计）
- [x] REST API路由：/api/v1/system（配置增改/采集/分析/生成/推送/日志）
- [x] REST API路由：/api/v1/dashboard/stats
- [x] Pydantic Schema（common/report/news/system 完整定义）
- [x] DeepSeek API Key 已配置并验证通过

### P1（重要，已完成 ✅）
- [x] 开源项目分析器（ProjectAnalyzer + 推荐指数公式）
- [x] 创业机会分析器（OpportunityAnalyzer + 商业模式评估）
- [x] REST API路由：/api/v1/projects /opportunities /jobs（含analyze端点）
- [x] P1 Pydantic Schema：project / opportunity / job
- [x] 资讯列表页（分页+状态标签+手动采集按钮）
- [x] 资讯详情页（四维评分展示+注意力等级+立即分析按钮）
- [x] 项目页（Star/评分/难度/语言筛选）
- [x] 机会页（个人开发友好度+评分+改善建议）
- [x] 岗位页（薪资/需求度/技能词条+🔥新技能标识）

### P2（增强，有时间再做）
- [ ] 系统配置页面表单（LLM/推送/时间配置）
- [ ] 日志页面（筛选/自动刷新）
- [ ] 前端手动操作按钮（采集/分析/生成/推送联动API）
- [ ] 岗位趋势种子数据 + 技能分析
- [ ] 集成测试 + 异常场景覆盖
- [ ] Docker映像验证 + 部署文档

---

## 当前架构

### 数据采集流程
```
定时触发 → 遍历7个活跃采集源 → RSS/API/Web抓取
  → 三重去重（URL/内容哈希/标题相似度）
  → 写入 news_items（status=pending）
  → 更新 source.last_status
```

### AI分析流程
```
每日07:00触发 → 查询 pending 资讯（最多50条）
  → Semaphore(3)并发调用LLM
  → 解析JSON（摘要+四维评分）
  → clamp评分到1-10，calc_attention_level
  → 写入 analysis_results，更新news.status
  → 聚合分析：生成趋势总结+热点
```

### 日报生成流程
```
每日07:30触发 → 查询当日analysis_results
  → 按attention_level排序，取Top5新闻
  → 筛选business_score≥6的工具
  → 按recommendation_score排序项目
  → LLM生成行动建议
  → 6板块编排 → 保存到daily_reports+report_items
```

### 推送流程
```
每日08:00触发 → 查询当日日报
  → 遍历已配置渠道（企微/邮件）
  → 格式化Markdown/HTML
  → push_with_retry(max=3次)
  → 记录推送日志
```

---

## 数据库设计摘要（10张表）

| 表 | 用途 | 日均数据量 |
|----|------|-----------|
| collection_sources | 采集源配置（7个默认源） | 0（只更新） |
| news_items | 采集的原始资讯 | 50-80条 |
| analysis_results | AI分析结果（一对一关联news） | 50-80条 |
| daily_reports | 日报 | 1条 |
| report_items | 日报各板块内容（6条/日报） | 6条 |
| open_source_projects | GitHub开源项目 | 10-20条 |
| project_analysis | 项目分析（一对一关联project） | 10-20条 |
| startup_opportunities | 创业机会 | 5-10条 |
| opportunity_analysis | 机会分析（一对一关联opportunity） | 5-10条 |
| job_trends | 岗位趋势 | 1条 |
| job_skills | 岗位技能 | 10-20条 |
| system_config | 系统运行时配置（5个默认配置） | 0（只更新） |
| system_logs | 运行日志 | 100-200条 |
| users | 用户（预留，无默认数据） | 0 |

---

## 项目风险

| 风险 | 影响 | 状态 |
|------|------|------|
| ~~API路由层未实现~~ | **已实现，全部验证通过** | ✅ 已修复 |
| ~~Project分析器/Opportunity分析器未实现~~ | **已实现并集成到AnalyzerService** | ✅ 已修复 |
| openai SDK 1.0+ 兼容性验证 | 仅单元测试过，未全链路跑通 | ⚠️ 需实测 |
| 采集源RSS可能改版 | 需监控采集成功率 | 🟡 后续处理 |
| 岗位趋势模块仅骨架 | 种子数据未加载 | 🟡 后续处理 |

---

## 下一步开发计划（按优先级）

1. **实现Pydantic Schema**（`schemas/*.py`）— 统一请求/响应模型
2. **实现REST API路由**（`routers/reports/news/system/dashboard.py`）— 对接Service层
3. **实现开源项目分析器**（`analyzer/project_analyzer.py`）— 推荐指数公式
4. **实现创业机会分析器**（`analyzer/opportunity_analyzer.py`）— 商业模式评估
5. **补全Web模板**（项目页/机会页/岗位页/配置表单/日志页）
6. **配置页表单提交功能**（保存配置到system_config表）
7. **初始化git仓库 + 首次commit**

---

## Claude Code 接手说明

**阅读顺序**：
1. 本文档（PROJECT_CONTEXT.md）→ 快速了解项目全貌
2. `docs/task.md` → 查看P0/P1/P2任务清单和进度
3. `docs/architecture.md` → 理解模块设计和数据流

**运行命令**：
```bash
cd /d/admin/projects/ai-daily
"C:/Users/admin/AppData/Local/Programs/Python/Python311/python.exe" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**关键路径**：app启动 → lifespan初始化数据库 + 启动调度器 → web路由注册 → 手工触发采集/分析/日报/推送验证全链路。

**注意**：`.env` 中需配置至少一个LLM API Key（默认`deepseek`）AI分析功能才能工作。
