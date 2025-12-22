## 目标与原则
- 引入 Zep 的长时记忆与异步摘要/嵌入流水线理念，完善检索与上下文装配 [1][3][4]
- 引入 Memos 的多用户、标签、公开/私有、REST API 与简洁前端交互范式 [2][5]
- 保持当前 Graphiti 驱动的图记忆架构不变，面向生产补齐鉴权/RBAC、持久化、可观测性、安全与前端可视化

## 现状与缺口
- 配置必填项：`server/config.py:55` 现强制 `OPENAI_API_KEY`；需按 `LLM_PROVIDER` 动态可选
- CORS 过宽：`server/main.py:86` 默认 `allow_origins=["*"]`
- Graphiti 实体查询为占位：`server/services/graphiti_service.py:268-286`
- 文档标注 API Key 管理端点待实现：`README.md:304`
- Postgres/Redis 已配置但未落地用户/Key/审计/缓存等持久化能力
- 前端 `GraphView` 未实现图渲染：`web/src/pages/GraphView.tsx:1-18`

## 后端增强（Zep 对齐）
- 会话与记忆域模型
  - 新增实体：`users`、`api_keys`、`tenants`、`sessions`、`episodes_meta`、`facts`（含 `valid_at/invalid_at`）、`embeddings`（pgvector）
  - 将 Episode 生成的实体/关系的元信息入库，保留 Graphiti 作为图构建与检索主路
- 异步流水线
  - Episode 入站→后台任务生成摘要、事实抽取、消息/摘要嵌入，写入 `facts/embeddings` [1][3][4]
  - 采用 Redis 队列（或 FastAPI background tasks）与幂等策略
- 检索策略
  - 保留 `GraphitiService.search`（RRF）并增加向量召回融合；支持基于 `session_id`/`tenant` 的范围检索

## 鉴权与 RBAC
- API Key 管理端点
  - `POST /api/v1/auth/keys` 创建；`GET/DELETE /api/v1/auth/keys/{id}`；`GET /api/v1/auth/keys` 列表（分页/过滤）
  - Key 加盐哈希存储、状态/过期、用途范围（scopes）与轮换
- 用户与角色
  - `users/roles/permissions` 三表；最小权限原则；以 `tenant_id` 实现隔离
  - 认证中间件支持 `Authorization: Bearer vpm_sk_...` 与后续 OAuth2 SSO（Memos 对齐）[5]

## 数据持久化与迁移
- 使用 SQLAlchemy + Alembic 管理迁移；开启 pgvector 扩展用于 `embeddings`
- 将默认开发内存用户/Key迁移至 Postgres；审计日志（`audit_logs`）记录关键操作
- 引入 Redis 用于缓存热点检索、限流令牌桶

## 记忆/事实（Zep 对齐）
- 事实表（关系随时间演变）：`facts(entity_id, predicate, object, valid_at, invalid_at, source_episode)` [2]
- 会话摘要：按窗口维护 `session_summaries`；检索时装配最近消息+摘要+关系上下文 [1][3][4]

## 备忘录功能（Memos 对齐）
- 备忘录模型：`memos(id, user_id, content(markdown), visibility, created_at)`；标签、附件与日历视图 [2][5]
- API：`POST/GET/PUT/DELETE /api/v1/memos`；标签过滤、全文检索、公共分享页
- 与 Episode 关联：支持将备忘录提升为 Episode 或附注，参与检索上下文

## 前端改造
- GraphView：以 Cytoscape.js 渲染实体/关系图，筛选与聚焦，支持 `tenant/session` 过滤
- Settings：API Key 管理 UI（创建/禁用/轮换）、安全设置（CORS/限流）
- Memos：备忘录列表/详情/编辑器（Markdown）、标签过滤与公共页；交互式日历

## SDK 扩展
- Python SDK 增加 `AuthKeysClient`、`MemosClient`、`SessionsClient` 与检索融合接口
- 保持同步/异步一致的异常层次与重试策略

## 可观测性与安全
- Metrics：请求耗时、成功率、Episode 处理速率、任务队列长度、DB/Redis 状态（Prometheus 端点）
- Tracing：OpenTelemetry OTLP 导出；链路覆盖 API→服务→Graphiti/DB
- 安全：
  - 生产禁用默认 Key 生成；CORS 收敛到白名单域
  - 速率限制与 WAF 规则；敏感字段脱敏日志

## 配置与兼容
- `LLM_PROVIDER` 驱动下的必填项校验：未选 OpenAI 时不强制 `OPENAI_API_KEY`（`server/config.py:55`）
- `.env` 与文档补齐各变量说明与最小配置组合

## 测试与质量
- 单测：模型/服务/接口；集成测：Episode→流水线→检索→装配
- 提升覆盖率至 ≥85%；前端 e2e（Cypress）覆盖 API Key 与 Memos 工作流

## 交付与验收
- 阶段性交付：
  - 第一阶段：API Key 管理、RBAC 基础、配置修正与 CORS 收敛
  - 第二阶段：持久化落地、异步流水线与检索融合
  - 第三阶段：Memos 前后端、GraphView 与 SDK 扩展
  - 第四阶段：可观测性、安全与测试覆盖
- 文档更新：API 参考、部署与运维、迁移指南

## 参考
- Zep 长期记忆、异步摘要/嵌入、会话上下文装配：[1] https://github.com/getzep/zep-python，[3] https://github.com/getzep/zep-js，[4] https://getzep.github.io/zep-js/
- Memos 自托管备忘录、标签/可见性、REST API 与前端交互：[2] https://github.com/usememos/memos，[5] https://www.appinn.com/memos/