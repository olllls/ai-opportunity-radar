# AI 机会雷达 —— 部署状态

## 当前状态

本地开发完成，开发完成度约 80%。Docker 已具备基础部署能力。尚未购买服务器、配置域名、配置 HTTPS。

---

## 已确认 P0 问题

| # | 问题 | 风险 | 状态 |
|---|------|------|------|
| 1 | 缺少 `.dockerignore` | `.env`（含真实密钥）可能进入镜像 | 待修复 |
| 2 | `docker-compose.yml` 缺少 nginx 服务 | 不支持 HTTPS | 待修复 |
| 3 | `nginx.conf` 中 `proxy_pass localhost:8000` | Nginx 容器内无法到达 app 容器 | 应改为 `http://app:8000` |

## 已确认 P1 问题

| # | 问题 | 说明 |
|---|------|------|
| 1 | `SITE_URL=http://localhost:8000` | 部署时改为正式域名 |
| 2 | `backup.py` 未处理 SQLite WAL 文件 | 后续修复 |
| 3 | `backup.py` 运行时 `dispose` 引擎 | 与调度器冲突，后续修复 |
| 4 | 容器以 root 运行 | 后续优化 |

---

## 当前部署目标

- Ubuntu 22.04 · Docker Compose · Nginx · HTTPS
- 域名访问 · 企业微信推送正常 · 连续运行 7 天无异常

---

## 下一步

允许修改：`.dockerignore`、`docker-compose.yml`、`nginx.conf`、`DEPLOYMENT.md`

禁止修改：API、数据模型、业务逻辑、页面功能

优先完成 P0。

---

## 部署完成标准

- `https://域名/` 可访问
- `https://域名/health` 返回 ok
- `https://域名/docs` 正常
- 日报采集/推送正常
- 连续运行 7 天无异常

---

## 新会话启动指令

项目已完成本地开发，当前处于部署阶段。请先阅读 `PROJECT_CONTEXT.md`、`PROJECT_DEPLOY_STATUS.md`、`DEPLOYMENT.md`，然后继续执行部署任务。不要重新规划产品。
