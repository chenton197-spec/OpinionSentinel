# 公司舆情监控网站

基于 [docs/product-plan.md](docs/product-plan.md) 落地的 MVP 代码骨架，采用“同仓双应用”结构：

- `apps/web`: Next.js App Router 后台界面
- `apps/api`: FastAPI 业务接口与后续调度入口
- `docker-compose.yml`: PostgreSQL、Elasticsearch、Redis 本地依赖

当前实现重点是先把可演示闭环搭起来：看板、列表、详情、规则、预警、报表、设置页已经成型；FastAPI 已提供对应的演示接口；前端支持接口不可用时使用本地回退数据。

## 已实现范围

- 后台页面：登录、总览看板、舆情列表、舆情详情、关键词规则、预警记录、日报/周报、系统设置
- 后端接口：`/api/dashboard/overview`、`/api/articles`、`/api/articles/{id}`、`/api/rules`、`/api/alerts`、`/api/reports`
- 演示数据：内置种子数据、规则、预警和报表任务
- 扩展骨架：采集器接口、清洗流水线、搜索查询构造、异步任务边界、通知集成边界
- 当前后端已切到 PostgreSQL 持久化 CompanyProfile、Article、Rule、ReportTask，并支持 Celery 异步导出 HTML/PDF 报表

## 目录结构

```text
apps/
  api/
    app/
      core/
      crawlers/
      data/
      integrations/
      models/
      pipelines/
      routes/
      schemas/
      search/
      services/
      tasks/
  web/
    src/
      app/
      components/
      lib/
      types/
docs/
  product-plan.md
```

## 本地启动

1. 复制环境变量模板

```bash
cp .env.example .env
```

2. 启动基础依赖

```bash
docker compose up -d postgres elasticsearch redis
```

3. 启动前端

```bash
npm --prefix apps/web run dev
```

4. 安装并启动后端

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m uvicorn app.main:app --reload --port 8000

# 新开一个终端启动 Celery Worker
.venv/bin/celery -A app.tasks.celery_app:celery_app worker --loglevel=info
```

## 常用命令

```bash
npm run dev:web
npm run dev:api
npm run dev:worker
npm run lint:web
npm run check:api
npm run infra:up
npm run infra:down
```

## 当前实现说明

- 前端已对齐计划中的后台信息架构，报表页已支持触发 HTML/PDF 异步导出；规则页仍需补更完整的编辑交互。
- 后端启动后会自动建表，并把种子数据迁入 PostgreSQL，后续写操作不会再因服务重启丢失。
- 真实抓取现已覆盖企业官网/公告候选、新闻门户 RSS，以及搜索聚合作为兜底来源。
- 前端已内置本地日志采集，最近 30 分钟的页面访问、点击、表单操作、网络请求、错误与心跳信息会落到 `logs/frontend/operations.ndjson`，汇总信息写入 `logs/frontend/summary.json`。

## 建议的下一步

1. 将 `demo_store` 替换为 PostgreSQL + Elasticsearch 真正读写。
2. 为规则创建和报表创建补上前端真实提交交互。
3. 实现企业官网、新闻门户、搜索聚合三个来源的首批真实采集器。
4. 接入 Celery Worker / Beat 与飞书或邮件通知通道。