# OpinionSentinel

OpinionSentinel 是一个全栈的自动化公司舆情监控系统。它提供了一个现代化的后台管理界面，基于规则的监控引擎，并支持基于自然语言处理的舆情预警和自动报表生成。

项目采用“同仓双应用” (Monorepo) 结构：
- `apps/web`: 基于 Next.js (App Router) 构建的现代化管理界面。
- `apps/api`: 基于 FastAPI 构建的高性能业务接口与定时调度工作节点。
- `docker-compose.yml`: PostgreSQL、Elasticsearch、Redis 等环境依赖。

## 核心特性
- 📊 **总览看板**：实时了解最新舆情动态和数据统计。
- 📰 **舆情监测**：自动化抓取和清洗各类文章、新闻。
- ⚙️ **监控规则**：灵活配置企业关键词与监控规则。
- 🚨 **实时预警**：舆情事件能够针对性自动判定并完成预警。
- 📈 **自动报表**：支持自动生成 HTML/PDF 等多种格式的多维度报告。

## 目录结构
```text
apps/
  api/  # Python / FastAPI 后端业务代码
  web/  # React / Next.js 前端应用代码
```

## 快速开始

### 1. 准备环境变量
```bash
cp .env.example .env
```

### 2. 启动基础依赖服务
确保您本机安装了 Docker 环境，然后运行：
```bash
docker compose up -d postgres elasticsearch redis
```

### 3. 可选快捷联调方式
如果在根目录下带有 Node.js 支持，可以通过便捷 scripts 分别启动：
```bash
npm run dev:web     # 启动前端应用
npm run dev:api     # 启动 FastAPI 后端接口服务
npm run dev:worker  # 启动异步任务 Worker
```

也可以深入 `apps/api` 与 `apps/web` 独立初始化对应语言模块运行依赖。
