# AI机会雷达 — 开发任务看板（Task Board）

> 更新日期：2026-06-10 | 总任务数：25 | 预估总工时：33h | 开发周期：14天

---

## 图例

| 标记 | 含义 |
|------|------|
| 🔴 P0 | 阻塞级，先完成 |
| 🟠 P1 | 核心功能，必须完成 |
| 🟡 P2 | 增强功能，尽力完成 |
| ⬜ | 待开始 |
| 🔄 | 进行中 |
| ✅ | 已完成 |

---

## P0（阻塞级 — 必须优先完成）

> 这些任务构成MVP的核心链路，任何一个未完成系统都无法工作。

### 项目骨架

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ✅ | 项目目录与配置文件 | 30min | — | 目录结构、.env、.gitignore、requirements.txt |
| ✅ | config.py 配置管理 | 30min | — | pydantic-settings，4个LLM提供商切换 |
| ✅ | main.py 应用入口 | 30min | — | FastAPI初始化、CORS、生命周期、健康检查 |
| ⬜ | tool**函数 (logger/retry/helpers) | 30min | — | loguru日志、async重试、通用工具 |
| ✅ | database.py 数据库引擎 | 30min | — | 异步引擎、WAL模式、会话管理、自动建表 |

### 数据库

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ✅ | 10张ORM模型表 | 1.5h | database.py | news/analysis/report/project/opportunity/job/config/log/user |
| ⬜ | Pydantic Schema定义 | 30min | 模型表 | 请求/响应验证模型 |

### 采集模块

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | BaseCollector + RSS采集器 | 30min | 数据库 | 抽象基类 + feedparser |
| ⬜ | Blog采集器（4个Blog源） | 30min | BaseCollector | OpenAI/Anthropic/Google/DeepSeek |
| ⬜ | API采集器 + Hacker News | 30min | BaseCollector | HN API适配 |
| ⬜ | 三重去重机制 | 30min | 数据库 | URL精确 + 标题相似度 + 内容哈希 |
| ⬜ | CollectorService（采集编排） | 30min | 所有采集器 | 遍历源→去重→写入→日志 |
| ⬜ | APScheduler集成（定时任务） | 30min | CollectorService | 4个定时任务注册 |

### AI分析

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | LLM客户端封装 | 30min | config.py | AsyncOpenAI，支持DeepSeek/通义/GLM |
| ⬜ | 资讯分析器（Prompt+LLM调用） | 30min | LLM客户端 | 摘要、四维评分、attention_level |
| ⬜ | 批量分析（并发控制） | 30min | 资讯分析器 | Semaphore=3，进度日志 |
| ⬜ | 聚合分析器 | 30min | 资讯分析器 | 当日趋势总结生成 |

### 日报生成

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | ReportGenerator（数据筛选+编排） | 30min | 聚合分析 | 6板块内容编排 |
| ⬜ | 行动建议生成（LLM调用） | 30min | ReportGenerator | 2-3条具体建议 |
| ⬜ | Markdown/HTML格式化 | 30min | ReportGenerator | 日报双格式输出 |
| ⬜ | 空数据/异常处理 | 30min | ReportGenerator | 无数据时降级展示 |

### 展示与推送

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | Web页面路由 + 基础模板(base.html) | 30min | — | 导航+侧边栏+响应式 |
| ⬜ | 仪表盘页面(dashboard.html) | 30min | Web路由 | 统计卡片+状态展示 |
| ⬜ | 日报详情页面(report.html) | 30min | Web路由 | 6板块日报渲染 |
| ⬜ | REST API路由（日报/资讯/系统） | 1h | Schema定义 | Swagger所有端点可调用 |
| ⬜ | 企业微信推送 | 30min | 日报生成 | Markdown消息，2048字节限制 |
| ⬜ | PushService（推送编排+重试） | 30min | 企业微信 | 渠道遍历+3次重试 |

### 部署

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ✅ | 启动脚本（init_db/seed_data/backup） | 30min | 数据库 | 数据库初始化+种子数据+备份 |
| ✅ | Docker部署（Dockerfile+compose） | 30min | — | 多阶段构建+容器编排 |

---

## P1（重要 — MVP核心功能必须完成）

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | Web抓取器（BeautifulSoup） | 30min | BaseCollector | 通用HTML解析 |
| ⬜ | GitHub Trending + Product Hunt | 30min | Web抓取器 | 特定源适配 |
| ⬜ | 手动采集API (POST /system/collect) | 30min | CollectorService | 手动触发 |
| ⬜ | 分析错误处理+补分析机制 | 30min | 批量分析 | 失败重试+下次补跑 |
| ⬜ | ProjectAnalyzer（GitHub数据分析） | 30min | LLM客户端 | Star增长+技术栈 |
| ⬜ | 推荐指数公式实现 | 30min | ProjectAnalyzer | 5维度加权计算 |
| ⬜ | OpportunityAnalyzer（商业模式评估） | 30min | LLM客户端 | Product Hunt分析 |
| ⬜ | 机会评分+个人开发友好度 | 30min | OpportunityAnalyzer | 综合评分+可行性 |
| ⬜ | 日报列表页 + 资讯列表页 | 30min | base.html | 分页+筛选 |
| ⬜ | 资讯详情页 | 30min | base.html | 分析结果展示 |
| ⬜ | 项目分析页 + 创业机会页 | 30min | base.html | 推荐指数展示 |
| ⬜ | 邮件推送（SMTP） | 30min | 日报生成 | HTML邮件模板 |
| ⬜ | 手动操作API扩展 | 30min | 推送模块 | 重试推送等 |
| ⬜ | 岗位数据采集（种子数据） | 30min | 数据库 | 100条种子数据 |
| ⬜ | 技能分析（高频/新增技能） | 30min | 岗位数据 | 频率统计+对比 |
| ⬜ | 学习建议生成 | 30min | 技能分析 | LLM生成学习路径 |
| ⬜ | .env.example完善 | 30min | — | 配置项注释+示例 |

---

## P2（增强 — 有时间再做）

| 状态 | 任务 | 工时 | 前置 | 说明 |
|------|------|------|------|------|
| ⬜ | 岗位趋势页 + 系统配置页 | 30min | base.html | 技能词条+配置表单 |
| ⬜ | 日志页 + 静态资源(CSS/JS) | 30min | base.html | 日志筛选+暗黑模式 |
| ⬜ | 前端按钮联动 | 30min | 手动操作API | 手动采集/推送按钮 |
| ⬜ | 性能优化 | 30min | 集成测试 | 查询+页面加载优化 |
| ⬜ | README完善 | 30min | — | 项目说明+启动指南 |

---

## 进度统计

| 优先级 | 总任务 | 已完成 | 总工时 |
|--------|-------|-------|-------|
| P0 | 35 | 8 | 19h |
| P1 | 17 | 0 | 10.5h |
| P2 | 5 | 0 | 2.5h |
| **总计** | **57** | **8** | **32h** |

### 已完成任务

- 项目目录与配置文件
- config.py 配置管理
- main.py 应用入口
- database.py 数据库引擎
- 10张ORM模型表
- 启动脚本（init_db/seed_data/backup）
- Docker部署（Dockerfile+compose）
- tool**函数 (logger/retry/helpers)

---

## 开发顺序建议

```
第一阶段（P0优先）：
  1. 项目骨架（已完**）→ 2. 数据库（已完**）→ 3. LLM客户端
  4. 采集器（RSS/Blog/API/Web） → 5. 去重+编排 → 6. 调度

第二阶段（P0优先）：
  7. 资讯分析 → 8. 聚合分析 → 9. 项目分析 → 10. 机会分析
  11. 日报生成 → 12. Schema → 13. API路由

第三阶段（P0→P1→P2）：
  14. Web页面 → 15. 推送 → 16. 岗位趋势
  17. 集成测试 → 18. Bug修复 → 19. 文档
```
