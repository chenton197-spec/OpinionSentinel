## Plan: 公司舆情监控网站详细实施方案

目标是在空工作区中规划一套可落地的公司舆情监控网站 MVP，面向内部运营与品牌团队使用。方案以快速形成可演示、可扩展、可逐步接入真实数据源为原则，优先完成闭环能力而不是全量平台能力。推荐方案为同仓分层架构：Next.js 负责后台前端界面，FastAPI 提供业务接口与采集调度入口，PostgreSQL 负责业务存储，Elasticsearch 负责全文检索与趋势聚合，Redis/Celery 负责异步采集、情感分析、预警与报表任务。

MVP 的第一阶段应重点保证“能稳定看到有价值的舆情结果”，而不是“覆盖所有平台”。因此首期推荐纳入企业官网/公告、新闻门户和搜索聚合结果三类来源，并为公众号、微博、知乎/论坛预留扩展接口。这样可以先交付一个真正可用的后台，再迭代高风险来源。

**Steps**
1. Phase 1: 产品边界、角色与页面结构定义
   明确产品只服务内部使用，不做公开访问站点；首期先采用单管理员或极简账号体系，不实现复杂多角色权限。
   页面结构建议为：登录页、总览看板、舆情列表、舆情详情、关键词规则、预警记录、日报/周报、系统设置。
   每个页面的职责需要在开工前写清楚，避免接口先行导致后续返工。
   此阶段产物应包括页面清单、页面字段清单、页面间跳转关系、默认筛选维度、MVP 明确不做的功能。
2. Phase 2: 技术架构与项目结构设计
   项目建议采用 monorepo 或双应用同仓结构，根目录维护统一脚本与开发说明。
   前端采用 Next.js App Router + TypeScript，适合快速搭后台页面与服务端路由。
   后端采用 FastAPI，便于后续接入 NLP、爬虫、异步任务与数据处理流程。
   基础设施上定义 PostgreSQL、Elasticsearch、Redis、Celery Worker、Celery Beat、本地文件导出目录。
   此阶段需要确定环境变量命名规范、日志格式、时间字段时区标准、统一错误码结构。
3. Phase 3: 信息架构与核心数据模型定义
   先设计标准化舆情数据对象，避免后续每接一个来源就污染业务层。
   核心实体至少包括：Article、Source、KeywordRule、AlertEvent、ReportTask、SentimentResult、CrawlerJob。
   Article 需要包含标题、摘要、正文、来源名称、来源类型、原始链接、作者、发布时间、抓取时间、去重指纹、情感结果、关键词命中结果、标签集合、地区或行业标签。
   KeywordRule 需要支持包含词、排除词、情感阈值、来源范围、是否启用、通知方式、创建人、更新时间。
   AlertEvent 需要记录命中规则、命中文章、触发原因、触发时间、通知状态、通知回执。
   ReportTask 需要记录报表类型、时间范围、生成状态、下载地址、触发人。
   此阶段输出应成为后续数据库 schema、索引映射和接口返回结构的依据。
4. Phase 4: 采集接入策略与适配器边界
   为所有数据源定义统一 Source Adapter 接口，例如 fetch_list、fetch_detail、normalize、extract_publish_time、build_fingerprint。
   MVP 第一批只实现三类来源：企业官网/公告、新闻门户、搜索聚合结果。
   企业官网/公告重点解决 HTML 与 PDF 公告解析；新闻门户重点解决栏目列表与详情抽取；搜索聚合结果主要作为兜底渠道，用于补足品牌关键词覆盖率。
   公众号、微博、知乎/论坛不纳入首期稳定交付，只保留 adapter 协议、来源枚举和值对象结构。
   采集策略需区分一次性回填与定时增量抓取，后续调度层才能无缝扩展。
5. Phase 5: 数据清洗、去重与标准化流水线
   采集结果进入统一处理流水线：正文提取、无关内容剔除、HTML 清洗、标题修正、时间规范化、URL 规范化、指纹生成。
   去重建议至少同时使用 URL 唯一性和正文指纹近似检测两层策略，避免新闻转载大量重复。
   对于正文为空、时间不可信、内容过短的记录，需要定义降级规则或直接丢弃规则。
   清洗后形成标准 Article DTO，再分别写入 PostgreSQL 与 Elasticsearch。
6. Phase 6: 情感分析与标签增强链路
   MVP 不建议自训模型，先接外部 NLP/LLM 服务，输出正向、负向、中性三分类以及置信度。
   如预算允许，可同时提取风险标签、品牌实体、竞品实体、行业主题词；如果预算有限，则先只做情感和关键词命中。
   情感分析任务必须异步执行，避免阻塞采集入库。
   分析失败时应允许重试，并在后台界面展示“待分析”或“分析失败”状态。
7. Phase 7: 检索与聚合方案设计
   PostgreSQL 存储业务主数据与规则数据，Elasticsearch 负责全文检索与统计聚合。
   列表页检索条件至少支持：关键词、来源类型、来源名称、时间范围、情感、是否命中规则。
   看板需要的聚合包括：按日趋势、情感分布、来源分布、高频关键词、重点文章列表。
   此阶段需要提前约束 Elasticsearch 索引结构与可筛选字段，避免后续聚合性能差。
8. Phase 8: 后端 API 设计
   API 以页面驱动为原则，优先围绕页面所需数据组织，而不是抽象成过早的平台接口。
   需要的核心接口包括：舆情列表查询、舆情详情、看板概览、趋势统计、关键词规则增删改查、预警记录列表、报表生成任务创建、报表下载记录查询。
   列表接口要支持分页、排序、复合筛选；详情接口要返回正文、情感、来源信息、命中规则、相似内容或相关文章。
   看板接口要支持按时间窗口和品牌关键词范围获取聚合结果。
   报表接口建议采用异步任务模式，避免前端长时间等待。
9. Phase 9: 前端后台页面规划
   总览看板页面展示核心 KPI：总舆情量、负面占比、今日新增、重点来源、趋势图、来源分布、情感分布、重点舆情列表。
   舆情列表页面需要高密度筛选、表格视图、快速查看摘要、情感标签、来源标签、命中规则标记。
   舆情详情页面需要显示完整正文、原文跳转、情感结果、关键词命中情况、来源信息、采集时间、相关推荐或相似内容。
   关键词规则页面需要支持创建监控词、排除词、预警阈值、通知方式与启停操作。
   预警记录页面展示触发记录、触发原因、发送结果、关联文章。
   日报/周报页面用于选择时间范围、生成报表、查看历史导出记录。
10. Phase 10: 预警与通知机制
   预警机制建议先支持两类触发：关键词命中、负面情感命中。
   通知通道在 MVP 只实现一个，优先建议飞书或邮件二选一，避免在通道适配上分散精力。
   预警去抖需要提前考虑，例如同一规则与同一文章只触发一次，避免消息轰炸。
   通知失败应记录失败原因并允许后台重发。
11. Phase 11: 报表导出策略
   首期推荐导出 HTML 或 PDF，不建议直接做复杂 Word 排版。
   报表内容至少包括：时间范围、舆情总量、情感分布、来源分布、趋势图、重点负面舆情、重点传播来源。
   报表模板设计要与看板复用同一统计口径，避免页面和报表数字不一致。
12. Phase 12: 调度、重试与稳定性设计
   通过 Celery Worker 执行采集、正文清洗、情感分析、预警通知、报表生成。
   通过 Celery Beat 或等价调度器执行定时抓取与日报/周报生成。
   对抓取失败、分析失败、通知失败分别定义重试次数、退避策略和失败状态。
   至少保证系统对单一来源失效时不会拖垮整条链路。
13. Phase 13: MVP 演示与验收准备
   需要准备一套可重复演示的种子数据方案，以防演示当天真实站点抓取不稳定。
   演示链路建议覆盖：采集入库、列表检索、详情查看、情感标签展示、趋势统计、规则创建、预警触发、报表导出。
   此阶段还应补充开发 README、环境变量说明、启动方式、任务运行方式和已知限制说明。

**Relevant files**
- /Users/yangxiao/projects/demo/package.json — 根目录统一脚本，负责串联前端、后端、基础服务的本地启动命令。
- /Users/yangxiao/projects/demo/pnpm-workspace.yaml — 如果采用 monorepo，用于管理前后端工作区。
- /Users/yangxiao/projects/demo/apps/web/package.json — 前端依赖、开发脚本、构建脚本。
- /Users/yangxiao/projects/demo/apps/web/src/app — App Router 页面目录，包含看板、列表、详情、规则、报表等路由。
- /Users/yangxiao/projects/demo/apps/web/src/components — 看板图表、筛选器、数据表格、状态标签、规则表单等复用组件。
- /Users/yangxiao/projects/demo/apps/web/src/lib/api.ts — 前端调用后端 API 的封装层。
- /Users/yangxiao/projects/demo/apps/web/src/types — 前端共享类型定义，如 Article、DashboardStats、KeywordRule。
- /Users/yangxiao/projects/demo/apps/api/pyproject.toml — FastAPI、Celery、数据库、Elasticsearch 等依赖配置。
- /Users/yangxiao/projects/demo/apps/api/app/main.py — FastAPI 应用入口、路由注册、中间件挂载。
- /Users/yangxiao/projects/demo/apps/api/app/core/config.py — 环境变量与配置管理。
- /Users/yangxiao/projects/demo/apps/api/app/routes — 舆情、统计、规则、预警、报表接口路由。
- /Users/yangxiao/projects/demo/apps/api/app/schemas — 请求响应 schema 定义，保证 API 结构稳定。
- /Users/yangxiao/projects/demo/apps/api/app/models — PostgreSQL ORM 模型，承载规则、任务、文章元数据等。
- /Users/yangxiao/projects/demo/apps/api/app/services/article_service.py — 列表查询、详情组装、文章业务逻辑。
- /Users/yangxiao/projects/demo/apps/api/app/services/dashboard_service.py — 趋势、来源分布、情感分布、高频关键词统计逻辑。
- /Users/yangxiao/projects/demo/apps/api/app/services/alert_service.py — 规则命中、去抖、通知派发与状态记录。
- /Users/yangxiao/projects/demo/apps/api/app/services/report_service.py — 报表聚合与导出任务组织。
- /Users/yangxiao/projects/demo/apps/api/app/crawlers — 各来源采集器与标准化适配器。
- /Users/yangxiao/projects/demo/apps/api/app/pipelines — 清洗、去重、正文提取、标签增强流水线。
- /Users/yangxiao/projects/demo/apps/api/app/search — Elasticsearch 索引映射、查询条件构造、聚合查询实现。
- /Users/yangxiao/projects/demo/apps/api/app/tasks — Celery 任务定义、重试策略、定时任务入口。
- /Users/yangxiao/projects/demo/apps/api/app/integrations — NLP 服务、邮件或飞书通知、PDF 生成等外部集成。
- /Users/yangxiao/projects/demo/docker-compose.yml — PostgreSQL、Elasticsearch、Redis 等本地依赖容器编排。
- /Users/yangxiao/projects/demo/.env.example — 本地环境变量模板，包括数据库、索引、通知、NLP 服务配置。
- /Users/yangxiao/projects/demo/README.md — 项目结构、启动命令、开发流程、MVP 范围声明。
- /Users/yangxiao/projects/demo/docs/product-plan.md — 当前项目计划文档。

**Verification**
1. 工程验证
   前端、后端、PostgreSQL、Elasticsearch、Redis、Celery Worker、Celery Beat 可以本地启动，并且通过 README 中的步骤可复现。
2. 采集验证
   至少两个新闻源和一个企业官网源可成功抓取，抓取结果经过清洗后写入数据库和搜索索引。
3. 去重验证
   同一来源重复抓取不会造成重复展示；转载文章或高度相似文章会被标记或合并处理。
4. 分析验证
   新文章入库后能异步获得情感标签；失败任务有可见状态和重试结果。
5. 列表验证
   舆情列表支持分页、排序、时间筛选、来源筛选、情感筛选、规则命中筛选，并能返回稳定结果。
6. 看板验证
   趋势图、来源分布、情感分布、高频关键词与实际索引聚合口径一致。
7. 预警验证
   新增规则后，命中数据能生成预警事件，通知成功或失败都会在记录页留痕。
8. 报表验证
   可创建日报或周报任务，任务完成后可下载导出文件，内容包含核心统计和重点舆情。
9. 稳定性验证
   单个采集器失败不会阻塞其他任务；NLP 服务异常时系统能降级或明确提示。
10. 演示验证
   在无外网或外部站点异常时，仍可通过种子数据演示主要业务流程。

**Decisions**
- 当前推荐定位：内部运营后台，不做对外展示型官网。
- 当前推荐阶段目标：MVP 演示版，但保留向正式版演进的结构。
- 当前建议首期数据源：企业官网/公告、新闻门户、搜索聚合结果。
- 当前建议延后数据源：公众号、微博全量、知乎/论坛深度抓取。
- 当前建议首期分析能力：情感分析与关键词命中优先，实体抽取与传播路径放入后续阶段。
- 当前建议首期通知通道：飞书或邮件二选一。
- 当前建议首期报表格式：HTML/PDF，暂不优先 Word。
- 当前明确不含：复杂角色权限、全平台稳定采集、行业专属训练模型、复杂 BI 自助分析。

**Further Considerations**
1. 如果你的真实目标是对外展示公司舆情能力，而不是内部运营使用，则前端信息架构和视觉风格要重做，计划需要切换为“官网展示站 + 后台”双端架构。
2. 如果你必须首期覆盖微博或公众号，建议在计划中改为采购第三方数据接口，否则会显著增加实施风险与不确定性。
3. 如果你更关心快速演示而不是先打真实采集闭环，可以把 Phase 4 到 Phase 6 先建立在模拟数据与导入数据之上，再逐步替换为真实采集器。
4. 如果后续团队人数增加，建议在正式版阶段引入角色权限、审阅流和人工标注纠错能力，用于提升负面舆情判断质量。

## 当前实施进展

### 已完成

**基础结构与页面（第一轮完成）**
- 同仓双应用结构：Next.js 前端后台 + FastAPI 后端，docker-compose 提供 PostgreSQL/Redis/Elasticsearch 基础设施定义。
- 所有核心页面已可访问并通过浏览器全量回归：登录页、总览看板、舆情列表（含筛选）、舆情详情、关键词规则展示、预警记录、日报周报、系统设置。
- 公司主体配置保存、自动补关键词、自动生成规则的完整流程已落地。
- 舆情列表支持关键词、来源类型、情感、规则命中、当前公司范围五维筛选。
- 详情页、预警页、报表页的动态运营建议（飞书告警 / 先去重 / 补官方回应）已落地。
- 前端 30 分钟操作日志已落盘。

**持久化（2026-05-24 完成）**
- 已将 CompanyProfile、Article、KeywordRule、AlertEvent、ReportTask 从内存 demo_store 切换到 SQLAlchemy ORM + PostgreSQL。
- 新建 `app/db/session.py` 管理 engine 与 SessionLocal；`app/models/entities.py` 包含五张表的完整 ORM 定义。
- 后端启动时自动建表，若表为空则迁入种子数据，服务重启后数据不再丢失。
- ORM 注解已修正为 `Optional[...]` 以兼容 Python 3.9，避免 declarative mapping 阶段报错。
- 已新增 `psycopg[binary]` 驱动和 `reportlab` 依赖，并完成本机安装验证。

**规则 CRUD（2026-05-24 完成）**
- 后端新增 GET / PUT / DELETE `/api/rules/{rule_id}` 接口，service 层补了对应 DB-backed 函数。
- `RuleUpdateRequest` 支持字段级部分更新。
- 运行时验证通过：创建、读取、更新启停、删除均正常，DELETE 返回 204。

**Celery 异步报表（2026-05-24 完成）**
- `app/tasks/celery_app.py` 已改为真实 Celery 应用实例，支持 `task_always_eager` 开关用于本地无 Redis 测试。
- `app/tasks/report_tasks.py` 注册了 `generate_report_export_task`，由 `create_report` 通过 `.delay()` 异步派发。
- 报表状态流转：`pending` → `running` → `ready` / `failed`，失败原因写入 `error_message`。
- `POST /api/reports` 在 eager 模式下直接返回最终 ready 状态；Redis 可用时异步执行。
- `npm run dev:worker` 脚本已补入 `package.json`。

**PDF 导出（2026-05-24 完成）**
- `report_service` 新增 `_build_report_pdf`，使用 reportlab 输出 A4 报表，包含 KPI 摘要和日报重点建议，支持中文自动换行。
- `ReportCreateRequest` 和 `ReportTask` 增加 `output_format` 字段（`html` / `pdf`）。
- 前端报表页新增"生成今日 PDF 日报"按钮，历史任务列表同步显示格式类型和失败原因。
- 运行时验证：PDF 生成后 `status=ready`，`download_url` 指向 `/exports/*.pdf`。

**真实采集（2026-05-24 完成）**
- `refresh_company_news` 改为三路并联：企业官网/公告候选（Bing 过滤 official_hints）→ Google News RSS → Bing News 兜底。
- `_build_article` 接受 `source_type` 参数，三类来源写入正确枚举值。
- 所有新插入文章的 `source_type` 现在能正确区分 company/news/search 三种类型。

**架构重构与探测能力增强（最新完成）**
- **架构解耦**：清理沉冗代码，将原混杂的爬虫与情绪判定逻辑从 `company_service.py` 中剥离，分别抽象至 `crawlers/runners.py` (采集运行器层) 与 `pipelines/sentiment.py` (数据预处理与情绪管道层)。
- **风控词库补全**：针对现代公关危机场景扩展了 `NEGATIVE_HINTS`，覆盖“翻车”、“致歉”、“低俗”、“问责”、“风波”等常用词，消除隐性公关事件漏报盲区。
- **历史溯源池扩容**：将生成式的历史数据检索量上限从 20 提升至 50，避免突发高频普通新闻冲掉近期的负面事件记录。
- **工作区整洁化**：清除了项目中产生的所有临时测试脚本（如 `patch_*.py`, `test_*.js` 等），保证单仓源码纯净。

---

### 尚未完成

**检索与聚合**
- Elasticsearch 尚未接入；列表筛选和看板统计仍基于内存计算（PostgreSQL 全量读取后 Python 层过滤排序）。高数据量时会成为性能瓶颈。

**前端规则管理交互**
- 后端规则 CRUD 接口已就绪，但前端规则页仍是只读展示，创建表单、编辑、启停、删除的前端交互尚未落地。

**通知通道**
- 飞书/邮件真实推送、同规则同文章去抖、失败重发均未落地。预警页目前只有建议展示。

**Celery Beat 定时任务**
- 定时采集、情感分析、预警派发均未配置；当前只有报表导出任务进了 Celery 队列，其余仍由接口同步触发。

**情感分析**
- 仍为启发式关键词逻辑，未接外部 NLP/LLM 服务，无"待分析 / 分析失败 / 重试"状态流转。

**登录与权限**
- 登录页为演示入口，未接真实认证、会话管理和权限边界。

**本机基础设施**
- 当前机器无 Docker、无本地 PostgreSQL/Redis，只有 Homebrew。本次运行时验证用临时 SQLite + `CELERY_TASK_ALWAYS_EAGER=true` 模式完成。真实 PostgreSQL + Celery Worker 联调需要先安装服务。

---

### 下一步优先级

1. **P0（阻塞真实联调）**：`brew install postgresql redis` 或安装 Docker Desktop，然后按 README 跑一遍原生联调，确认持久化、规则 CRUD、Celery Worker PDF 导出对 PostgreSQL 的完整链路。
2. **P1（功能完整性）**：前端规则管理页补 CRUD 交互；接入飞书通知并实现去抖。
3. **P2（规模化就绪）**：Elasticsearch 替换现有内存检索；Celery Beat 配置定时采集；情感分析接外部 NLP/LLM。
4. **P3（收口）**：登录页接真实认证；前端补统一空态/错误/加载态；PDF/周报模板完善。
