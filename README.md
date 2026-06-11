# 📡 AI机会雷达 (AI Opportunity Radar)

> **每天5分钟，掌握AI机会** — 自动采集、AI分析、每日推送的智能信息聚合平台

---

## 项目简介

AI机会雷达是一款面向AI从业者、独立开发者和技术创业者的信息聚合与分析平台。系统自动从7个全球主流AI信息源采集数据，利用大语言模型进行深度分析，每日生成高质量的中文AI机会日报，帮助用户在5分钟内掌握AI领域的关键动态与商业机会。

**作品集亮点：LLM工程化 · 全链路自动化 · 模块化设计 · 国产可用方案**

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 自动采集 | 7个核心源（OpenAI/Anthropic/Google AI/DeepSeek Blog + GitHub Trending + Hacker News + Product Hunt），支持RSS/API/网页抓取 |
| AI分析 | LLM驱动的资讯摘要、四维评分体系（重要性/学习价值/商业价值/创业价值）、关注等级判定 |
| 开源分析 | GitHub Star趋势、技术栈分析、推荐指数计算、复刻价值评估 |
| 创业分析 | AI产品商业模式分析、个人开发者可行性评估 |
| 岗位趋势 | 高频技能统计、新增技能识别、学习路径建议 |
| 日报生成 | 6板块日报（要闻/工具/开源/创业/岗位/行动建议），5分钟内读完 |
| 推送通知 | 企业微信机器人 + 邮件推送，失败自动重试 |
| Web后台 | 仪表盘、日报浏览、资讯管理、系统配置、日志查看，响应式设计 |

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI (Python 3.11+) | 异步高性能，自动API文档 |
| 数据库 | SQLite + SQLAlchemy 2.0 | MVP零配置，可迁移PostgreSQL |
| 任务调度 | APScheduler | 进程内调度，零外部依赖 |
| 前端 | TailwindCSS CDN + Jinja2 | 响应式，零构建工具 |
| AI分析 | DeepSeek / 通义千问 / GLM | 国内优先，多Provider切换 |
| 部署 | Docker / docker-compose | 环境一致性，一键部署 |

---

## 项目结构

```
ai-daily/
├── backend/                # 后端源码
│   ├── main.py            # 应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── models/            # ORM模型（10张表）
│   ├── schemas/           # Pydantic验证
│   ├── services/          # 业务服务层
│   │   ├── collector/     # 数据采集（7个源）
│   │   ├── analyzer/      # AI分析
│   │   ├── reporter/      # 日报生成
│   │   ├── pusher/        # 推送服务
│   │   ├── trends/        # 岗位趋势
│   │   └── scheduler.py  # 任务调度
│   ├── routers/           # REST API路由
│   ├── web/               # Web页面路由
│   ├── templates/         # Jinja2模板
│   ├── static/            # 静态资源
│   └── utils/             # 工具函数
├── docs/                   # 项目文档
├── scripts/                # 工具脚本
├── docker/                 # Docker部署
├── data/                   # SQLite数据库（运行时）
├── logs/                   # 日志文件（运行时）
└── requirements.txt        # Python依赖
```

---

## 本地启动

```bash
# 前置条件：Python 3.11+，一个LLM API Key（推荐DeepSeek）

# 1. 克隆项目
git clone <repo-url>
cd ai-daily

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Key

# 4. 初始化数据库
python scripts/seed_data.py

# 5. 启动应用
uvicorn backend.main:app --reload

# 6. 访问 http://localhost:8000
```

---

## Docker 部署

```bash
cp .env.example .env         # 编辑填入 API Key
cd docker
docker-compose up -d         # 一键启动
docker-compose exec app python scripts/seed_data.py  # 初始化数据
docker-compose logs -f       # 查看日志
# 访问 http://localhost:8000
```

---

## 未来规划

| 版本 | 规划内容 |
|------|---------|
| V1.1 | Redis缓存、自定义采集源、飞书/钉钉推送、日报PDF导出 |
| V2.0 | 用户系统、多订阅、PostgreSQL迁移、搜索功能 |
| V2.5 | AI对话查询、个性化推荐、热点预测 |
| V3.0 | SaaS多租户、API开放平台、团队协作、付费订阅 |

---

## 文档索引

| 文档 | 视角 | 说明 |
|------|------|------|
| [PRD](docs/PRD.md) | 产品经理 | 项目背景、用户画像、功能需求、MVP范围 |
| [架构设计](docs/architecture.md) | 架构师 | 系统架构图、数据流、ER图、API设计、部署方案 |
| [开发规划](docs/planning.md) | 项目经理 | 阶段规划、里程碑、风险管理、版本路线图 |
| [任务看板](docs/task.md) | 开发者 | 优先级分组、任务清单、工时估算、状态追踪 |

---

## 许可证

MIT License
