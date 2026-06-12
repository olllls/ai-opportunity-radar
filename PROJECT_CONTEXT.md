# AI Opportunity Radar - PROJECT_CONTEXT

## 项目状态

项目名称：AI Opportunity Radar（AI机会雷达）

当前阶段：

MVP开发完成 → 准备生产环境部署

项目路径：

D:\admin\projects\ai-daily

---

## 项目目标

自动采集AI行业资讯、工具、开源项目和机会信息。

通过大模型分析后生成日报。

最终通过：

* Web页面
* 企业微信
* 邮件

向用户推送。

目标用户：

* AI应用工程师
* 独立开发者
* AI创业者

---

## 当前完成度

产品设计：90%

后端开发：85%

前端开发：80%

数据采集：75%

AI分析：80%

数据库：95%

Docker部署：85%

云服务器部署：0%

监控告警：5%

总体开发完成度：

80%

---

## 已完成功能

### 数据采集

已实现：

* OpenAI Blog RSS
* Hacker News API
* GitHub Trending
* Product Hunt API
* 其他RSS源

共7个数据源。

### 去重机制

实现：

* URL去重
* 标题相似度去重
* 内容哈希去重

### AI分析

支持：

* DeepSeek
* 通义千问
* 智谱GLM
* OpenAI

实现：

* 新闻评分
* 项目评分
* 商业机会评分
* 学习价值评分

支持：

LLM失效自动降级规则分析。

### 日报生成

已实现：

* 今日新闻
* AI工具
* 开源项目
* 创业机会
* 岗位趋势
* 行动建议

### 推送

已实现：

* 企业微信机器人
* 邮件推送

### 定时任务

已实现：

* 采集
* 分析
* 日报生成
* 自动推送

### Web系统

已实现：

* 仪表盘
* 日报页面
* 新闻页面
* 项目页面
* 机会页面
* 岗位页面
* 配置页面
* 日志页面

### API

31个REST接口。

统一SuccessResponse格式。

---

## 技术栈

后端：

FastAPI

数据库：

SQLite

ORM：

SQLAlchemy Async

前端：

Jinja2
HTML
CSS
JavaScript

任务调度：

APScheduler

AI：

DeepSeek API

推送：

企业微信
SMTP邮件

部署：

Docker
Docker Compose

系统：

Ubuntu 22.04

---

## 数据库

14张表：

* collection_sources
* news_items
* analysis_results
* daily_reports
* report_items
* open_source_projects
* project_analysis
* startup_opportunities
* opportunity_analysis
* job_trends
* job_skills
* system_config
* system_logs
* users

---

## 项目结构

核心目录：

backend/

services/

routers/

templates/

docker/

scripts/

docs/

---

## 当前代码审查结果

已修复：

* Product Hunt GraphQL API
* GitHub Trending数据解析
* SuccessResponse统一
* 岗位种子数据
* 配置页面
* 日志页面

剩余P2：

* 手动采集按钮联动
* README完善
* 页面性能优化

---

## 当前阻塞

无功能阻塞。

唯一阻塞：

项目尚未部署到生产环境。

---

## 下一阶段目标

部署上线。

优先级：

P0

1. 购买云服务器
2. Ubuntu 22.04
3. Docker Compose部署
4. Nginx反向代理
5. HTTPS证书
6. 域名绑定
7. 自动重启
8. 日志管理
9. 数据备份

---

## 部署原则

优先：

* 中国大陆可访问
* Docker部署
* 简单稳定

暂不考虑：

* Kubernetes
* 微服务拆分
* PostgreSQL迁移

SQLite当前足够。

---

## 新会话启动指令

项目已完成本地开发。

当前目标：

生产环境部署。

阅读顺序：

1. PROJECT_CONTEXT.md
2. task.md
3. architecture.md

不要重新规划产品。

不要新增功能。

直接进入部署阶段。

优先输出：

服务器方案
Docker方案
Nginx方案
HTTPS方案
部署检查清单
