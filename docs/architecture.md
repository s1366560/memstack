# VIP Memory 架构文档

## 系统架构概览

VIP Memory 采用现代化的三层架构设计，实现了关注点分离和模块化开发。

```
┌─────────────────────────────────────────────────────────┐
│                    客户端层 (Clients)                     │
├─────────────────────────────────────────────────────────┤
│  Web Console  │  Python SDK  │  REST API  │  CLI Tools  │
└────────────┬────────────────┴────────────┴──────────────┘
             │
             │  HTTP/HTTPS (API Key Authentication)
             │
┌────────────▼────────────────────────────────────────────┐
│                   API层 (FastAPI)                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Episodes   │  │    Memory    │  │     Auth     │  │
│  │   Endpoints  │  │   Endpoints  │  │  Middleware  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────┬────────────────────────────────────────────┘
             │
             │  Service Dependencies
             │
┌────────────▼────────────────────────────────────────────┐
│                 业务逻辑层 (Services)                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │         Graphiti Service (Knowledge Graph)        │  │
│  │  - Episode Processing                            │  │
│  │  - Entity Extraction                             │  │
│  │  - Relationship Building                         │  │
│  │  - Memory Search                                 │  │
│  └──────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────┘
             │
             │  LLM & Database Connections
             │
┌────────────▼────────────────────────────────────────────┐
│                  基础设施层 (Infrastructure)              │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Neo4j   │  │PostgreSQL│  │  Redis   │  │  LLM   │ │
│  │  Graph   │  │ Metadata │  │  Cache   │  │Gemini/ │ │
│  │   DB     │  │    DB    │  │          │  │  Qwen  │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. API层 (server/)

#### 1.1 认证中间件 (auth.py)
- **功能**: API Key验证和用户身份识别
- **实现**: FastAPI依赖注入
- **存储**: 内存存储（开发环境），未来支持数据库
- **特性**:
  - SHA256哈希存储
  - Bearer token格式
  - 自动过期检查
  - 权限验证支持

#### 1.2 API端点 (api/)
- **episodes.py**: Episode创建和管理
  - `POST /api/v1/episodes/` - 创建新episode
  - 异步处理，立即返回202 Accepted
  
- **memory.py**: 记忆搜索
  - `POST /api/v1/memory/search` - 搜索知识图谱
  - 支持语义搜索和过滤

#### 1.3 数据模型 (models/)
- **auth.py**: 用户和API Key模型
- **episode.py**: Episode相关模型
- **memory.py**: 搜索请求和响应模型
- **entity.py**: 实体模型

使用Pydantic v2进行数据验证和序列化。

### 2. 业务逻辑层 (services/)

#### 2.1 Graphiti Service (graphiti_service.py)
封装Graphiti核心功能：

```python
class GraphitiService:
    async def initialize() -> None
        """初始化Graphiti客户端和索引"""
    
    async def add_episode(episode: EpisodeCreate) -> Episode
        """添加episode到知识图谱"""
    
    async def search(query: MemoryQuery) -> MemoryResponse
        """搜索知识图谱"""
    
    async def health_check() -> bool
        """健康检查"""
```

**工作流程**:
1. **Episode摄取**
   - 接收原始内容
   - 提取实体和关系
   - 构建knowledge graph节点和边
   - 更新community结构

2. **记忆检索**
   - 混合检索策略（向量+关键词+图遍历）
   - 时态感知查询
   - 结果重排序和聚合

### 3. LLM客户端层 (llm_clients/)

#### 3.1 Qwen集成
- **qwen_client.py**: 通义千问对话API
- **qwen_embedder.py**: 文本向量嵌入
- **qwen_reranker_client.py**: 搜索结果重排序

支持DashScope API和兼容的OpenAI格式。

### 4. 数据持久层

#### 4.1 Neo4j (图数据库)
存储知识图谱的三层结构：

1. **Episode子图**
   - 节点类型: Episode
   - 属性: name, content, created_at, valid_at
   - 关系: 时序关系

2. **Semantic Entity子图**
   - 节点类型: Entity
   - 属性: name, type, attributes, summary
   - 关系: 实体间关系（typed edges）

3. **Community子图**
   - 节点类型: Community
   - 属性: name, summary, member_count
   - 关系: 实体归属关系

#### 4.2 PostgreSQL (元数据存储)
- 用户数据
- API Key记录
- 审计日志
- 配置信息

#### 4.3 Redis (缓存层)
- 会话缓存
- 查询结果缓存
- Rate limiting计数器

## Python SDK架构

### 客户端设计
```python
# 同步客户端
class VipMemoryClient:
    def __init__(api_key, base_url, timeout, max_retries)
    def create_episode(...) -> EpisodeResponse
    def search_memory(...) -> MemoryResponse
    def __enter__() / __exit__()  # Context manager

# 异步客户端
class VipMemoryAsyncClient:
    async def create_episode(...) -> EpisodeResponse
    async def search_memory(...) -> MemoryResponse
    async def __aenter__() / __aexit__()  # Async context manager
```

### 核心特性
1. **重试机制**: 指数退避，最多3次
2. **超时控制**: 默认30秒，可配置
3. **错误处理**: 完整的异常层次
4. **认证**: 自动添加Authorization header

## Web控制台架构

### 技术栈
- **构建**: Vite 5.0
- **框架**: React 18.2 + TypeScript 5.3
- **UI库**: Ant Design 5.12
- **路由**: React Router 6.20
- **状态管理**: React Hooks (useState, useEffect)
- **HTTP**: Axios

### 组件结构
```
src/
├── main.tsx              # 应用入口
├── App.tsx               # 路由配置
├── components/
│   └── Layout.tsx        # 主布局（侧边栏+内容区）
├── pages/
│   ├── Dashboard.tsx     # 仪表板
│   ├── Episodes.tsx      # Episode管理
│   ├── Search.tsx        # 记忆搜索
│   ├── GraphView.tsx     # 图可视化
│   └── Settings.tsx      # 设置
└── services/
    └── api.ts            # API客户端
```

### 认证流程
1. 用户在Settings输入API Key
2. 保存到localStorage
3. Axios请求拦截器自动添加header
4. 401错误时清除key并重定向

## 部署架构

### Docker Compose部署
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    depends_on: [neo4j, postgres, redis]
  
  web:
    build: ./web
    ports: ["80:80"]
    environment:
      - API_URL=http://api:8000
  
  neo4j:
    image: neo4j:5.26
  
  postgres:
    image: postgres:16
  
  redis:
    image: redis:7
```

### 独立Web部署
Web应用可以独立部署到任何静态托管服务：

1. **构建**: `npm run build` → dist/
2. **部署**: 上传到Nginx/Cloudflare/Vercel
3. **配置**: 设置API_URL环境变量

## 数据流

### Episode创建流程
```
Client (SDK/Web)
  │
  │ POST /api/v1/episodes/
  │ Authorization: Bearer vpm_sk_...
  │
  ▼
API Layer (FastAPI)
  │
  │ verify_api_key_dependency()
  │ ✓ 验证API Key
  │
  ▼
Service Layer (GraphitiService)
  │
  │ add_episode()
  │ ├─ Extract entities
  │ ├─ Identify relationships
  │ └─ Update communities
  │
  ▼
Infrastructure (Neo4j + LLM)
  │
  │ Neo4j: 创建节点和边
  │ LLM: 实体提取和摘要
  │
  ▼
Response
  │
  └─ 202 Accepted
     {id, status: "processing"}
```

### 记忆搜索流程
```
Client
  │
  │ POST /api/v1/memory/search
  │ {query, limit, filters}
  │
  ▼
API Layer
  │
  │ Authentication ✓
  │
  ▼
Service Layer
  │
  │ search()
  │ ├─ Semantic search (embedding)
  │ ├─ Keyword search
  │ └─ Graph traversal
  │
  ▼
Infrastructure
  │
  │ Neo4j: Cypher查询
  │ LLM: Embedding + Reranking
  │
  ▼
Response
  │
  └─ 200 OK
     {results: [...], total: N}
```

## 安全架构

### 认证层
- **API Key**: `vpm_sk_` 前缀，64字符随机
- **存储**: SHA256哈希
- **传输**: HTTPS + Bearer token
- **过期**: 可配置过期时间

### 授权层（待实现）
- 基于角色的访问控制（RBAC）
- 资源级权限
- Tenant隔离

### 数据安全
- 敏感数据加密存储
- 审计日志
- 定期备份

## 可扩展性

### 水平扩展
- API服务: 无状态设计，可部署多实例
- Neo4j: 支持集群模式
- Redis: 支持主从复制

### 垂直扩展
- 增加worker数量
- 调整数据库连接池
- 优化LLM调用并发

## 监控和可观测性

### 日志
- 结构化日志（structlog）
- 日志级别: DEBUG/INFO/WARNING/ERROR
- 请求ID追踪

### 指标（待实现）
- API响应时间
- 请求成功率
- Episode处理速度
- 数据库连接状态

### 追踪（待实现）
- OpenTelemetry集成
- 分布式追踪
- 性能分析

## 配置管理

### 环境变量
- **Neo4j**: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
- **LLM**: LLM_PROVIDER, QWEN_API_KEY/GEMINI_API_KEY
- **服务**: HOST, PORT, LOG_LEVEL
- **认证**: REQUIRE_API_KEY

### 配置文件
- `server/config.py`: Settings类（基于Pydantic）
- `.env`: 本地开发配置
- `docker-compose.yml`: 容器化配置

## 技术决策

### 为什么选择FastAPI？
- 自动生成OpenAPI文档
- 异步支持，性能优秀
- 类型提示和验证
- 依赖注入系统

### 为什么使用Neo4j？
- 原生图数据库，性能最优
- Cypher查询语言强大
- 时态查询支持
- Graphiti官方支持

### 为什么选择React？
- 成熟的生态系统
- 组件化开发
- 大量UI库支持
- TypeScript集成好

## 未来规划

### 短期
- [ ] GitHub Actions CI/CD
- [ ] 图可视化完整实现
- [ ] API Key管理界面
- [ ] 测试覆盖率提升至90%

### 中期
- [ ] 多租户支持
- [ ] WebSocket实时更新
- [ ] 高级搜索过滤
- [ ] 导出功能

### 长期
- [ ] 移动端应用
- [ ] 插件系统
- [ ] 多语言支持
- [ ] 企业级特性（SSO、审计等）
