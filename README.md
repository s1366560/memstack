# VIP Memory - 企业级 AI 记忆云平台

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.26%2B-blue.svg)](https://neo4j.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

基于开源项目 [Graphiti](https://github.com/getzep/graphiti) 构建的企业级 AI 记忆云平台，为 AI 应用和智能体提供强大的长短期记忆管理能力。

## ✨ 核心特性

- 🧠 **动态知识整合** - 实时整合对话数据、结构化业务数据和外部信息，无需批量重计算
- ⏰ **时态感知** - 双时间戳模型支持精确的历史时点查询
- ⚡ **高性能检索** - 混合检索机制（语义 + 关键词 + 图遍历）实现亚秒级响应
- 🔐 **API Key认证** - 简单安全的认证机制，支持权限控制
- 📦 **完整SDK** - Python同步/异步客户端，支持重试和错误处理
- 🌐 **Web控制台** - 基于React的可视化管理界面
- 📝 **备忘录(Memos)** - 类似 Flomo 的轻量级记录，支持标签和隐私控制
- 🕸️ **图谱可视化** - 交互式知识图谱展示
- 🧪 **高测试覆盖** - 52%+测试覆盖率，持续集成保障
- 🤖 **多 LLM 支持** - Google Gemini 和阿里云通义千问 (Qwen)

## 📋 项目架构

VIP Memory采用三层架构设计：

### 1. Server (FastAPI后端)
```
server/
├── api/              # REST API端点
│   ├── episodes.py   # Episode创建和管理
│   └── memory.py     # 记忆搜索
├── services/         # 业务逻辑层
│   └── graphiti_service.py  # Graphiti集成
├── models/           # Pydantic数据模型
│   ├── auth.py       # 认证模型
│   ├── episode.py    # Episode模型
│   ├── memory.py     # 记忆模型
│   └── entity.py     # 实体模型
├── llm_clients/      # LLM提供商集成
│   ├── qwen_client.py      # 通义千问客户端
│   ├── qwen_embedder.py    # 向量嵌入
│   └── qwen_reranker_client.py  # 重排序
├── auth.py           # API Key认证中间件
├── config.py         # 配置管理
└── main.py           # FastAPI应用入口
```

### 2. SDK (Python客户端)
```
sdk/python/vip_memory/
├── client.py         # 同步HTTP客户端
├── async_client.py   # 异步HTTP客户端
├── models.py         # 请求/响应模型
└── exceptions.py     # 异常定义
```

### 3. Web (React控制台)
```
web/
├── src/
│   ├── pages/        # 页面组件
│   │   ├── Dashboard.tsx    # 仪表板
│   │   ├── Episodes.tsx     # Episode管理
│   │   ├── Search.tsx       # 记忆搜索
│   │   ├── GraphView.tsx    # 图可视化
│   │   └── Settings.tsx     # 设置
│   ├── components/   # 通用组件
│   └── services/     # API服务
├── Dockerfile        # 多阶段构建
└── nginx.conf        # 反向代理配置
```

## 🚀 快速开始

### 前置要求

- **Python**: 3.10+ 
- **Node.js**: 18+ (仅Web开发)
- **Neo4j**: 5.26+ 
- **PostgreSQL**: 16+ (可选，用于元数据)
- **Redis**: 7+ (可选，用于缓存)
- **LLM API**: Google Gemini 或阿里云通义千问

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/yourusername/vip-memory.git
cd vip-memory

# 使用 uv 安装（推荐）
uv sync --extra dev

# 或使用 pip
pip install -e ".[dev,neo4j,evaluation]"
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置必要配置
# 必需配置:
# - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
# - LLM_PROVIDER (gemini 或 qwen)
# - 对应的LLM API密钥
```

### 3. 启动服务

#### 方式1: Docker Compose (推荐)
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api
```

#### 方式2: 本地开发
```bash
# 启动依赖服务
make docker-up  # 启动 Neo4j, PostgreSQL, Redis

# 启动API服务
make dev  # http://localhost:8000

# 启动Web控制台 (新终端)
cd web
npm install
npm run dev  # http://localhost:5173
```

### 4. 验证安装

```bash
# 检查健康状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs

# 获取默认API Key (开发模式)
# 在服务器启动日志中查找:
# "Generated default API key: vpm_sk_..."
```

## 📚 使用指南

### Python SDK使用

#### 安装SDK
```bash
pip install ./sdk/python
```

#### 同步客户端
```python
from vip_memory import VipMemoryClient

# 初始化客户端
client = VipMemoryClient(
    api_key="vpm_sk_your_api_key",
    base_url="http://localhost:8000/api/v1"
)

# 创建Episode
response = client.create_episode(
    name="用户对话",
    content="用户想要预订明天的会议室",
    source_type="text",
    group_id="user_123"
)
print(f"Episode ID: {response.id}")

# 搜索记忆
results = client.search_memory(
    query="会议室预订",
    limit=10
)
for result in results.results:
    print(f"- {result.content} (score: {result.score})")
```

#### 异步客户端
```python
from vip_memory import VipMemoryAsyncClient
import asyncio

async def main():
    async with VipMemoryAsyncClient(api_key="vpm_sk_...") as client:
        # 创建Episode
        response = await client.create_episode(
            name="异步对话",
            content="测试内容"
        )
        
        # 搜索记忆
        results = await client.search_memory(query="测试")
        print(f"找到 {results.total} 条结果")

asyncio.run(main())
```

### Web控制台使用

1. **访问**: http://localhost:5173
2. **设置API Key**: 进入 Settings 页面，输入API Key
3. **创建Episode**: Episodes 页面，填写表单提交
4. **搜索记忆**: Search 页面，输入查询关键词
5. **查看图谱**: GraphView 页面（开发中）

### 直接API调用

```bash
# 设置API Key
export API_KEY="vpm_sk_your_api_key"

# 创建Episode
curl -X POST http://localhost:8000/api/v1/episodes/ \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试Episode",
    "content": "这是测试内容",
    "source_type": "text"
  }'

# 搜索记忆
curl -X POST http://localhost:8000/api/v1/memory/search \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "测试",
    "limit": 10
  }'
```

## 🧪 开发和测试

### 开发命令
```bash
make help           # 显示所有可用命令
make install        # 安装依赖
make dev            # 启动开发服务器
make test           # 运行测试套件
make test-unit      # 仅运行单元测试
make test-integration  # 运行集成测试
make format         # 格式化代码
make lint           # 运行代码检查
make clean          # 清理临时文件
```

### 测试覆盖率
当前测试覆盖率: **52%** (31个测试，全部通过)

详细测试报告: [TEST_REPORT.md](TEST_REPORT.md)

```bash
# 运行测试并生成覆盖率报告
make test

# 查看HTML覆盖率报告
open htmlcov/index.html
```

### 代码风格
- 遵循PEP 8规范
- 使用Ruff进行格式化和检查
- 使用MyPy进行类型检查
- 参考 [AGENTS.md](AGENTS.md) 获取详细规范

## 📖 文档

- **[快速开始指南](docs/quickstart.md)** - 详细的安装和配置说明
- **[API参考](docs/api-reference.md)** - 完整的API端点文档
- **[SDK文档](sdk/python/README.md)** - Python SDK详细文档
- **[Web控制台](web/README.md)** - Web应用使用指南
- **[开发指南](AGENTS.md)** - 贡献者开发规范
- **[测试报告](TEST_REPORT.md)** - 测试覆盖率详情
- **[故障排查](docs/startup-troubleshooting.md)** - 常见问题解决

## 🔐 认证机制

VIP Memory使用API Key进行认证：

### API Key格式
- 前缀: `vpm_sk_`
- 长度: 71字符 (前缀 + 64位十六进制)
- 存储: SHA256哈希后存储，不保存明文

### 开发环境
服务启动时自动生成默认API Key并打印到日志：
```
INFO:     Generated default API key: vpm_sk_abc123...
INFO:     Default user created: developer@vip-memory.local
```

### 生产环境
通过API管理API Key：
```python
# API Key管理端点
POST /api/v1/auth/keys    # 创建Key
GET  /api/v1/auth/keys    # 列出Key
DELETE /api/v1/auth/keys/{id} # 删除Key
```

### 认证流程
1. 客户端在请求头中添加: `Authorization: Bearer vpm_sk_...`
2. 服务器验证API Key是否存在且有效
3. 检查权限和过期时间
4. 返回认证结果或401错误

## 🏗️ 部署

### Docker部署
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### Web应用独立部署
```bash
# 构建Web应用镜像
cd web
docker build -t vip-memory-web .

# 运行容器
docker run -d -p 80:80 \
  -e API_URL=http://api:8000 \
  vip-memory-web
```

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 提交PR前的检查清单
- [ ] 运行 `make format` 格式化代码
- [ ] 运行 `make lint` 通过代码检查
- [ ] 运行 `make test` 确保测试通过
- [ ] 更新相关文档
- [ ] 添加测试覆盖新功能

### 开发流程
1. Fork 本仓库
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送到分支: `git push origin feature/amazing-feature`
5. 提交Pull Request

详细开发规范请参考 [AGENTS.md](AGENTS.md)

## 📝 更新日志

### v0.1.0 (2024-12-19)
- ✅ FastAPI后端API实现
- ✅ API Key认证机制
- ✅ Python SDK (同步/异步)
- ✅ React Web控制台
- ✅ Docker部署配置
- ✅ 测试基础设施 (52%覆盖率)
- ✅ 完整文档和示例

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

本项目基于以下优秀开源项目：

- [Graphiti](https://github.com/getzep/graphiti) - 核心知识图谱引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Neo4j](https://neo4j.com/) - 图数据库
- [React](https://react.dev/) - UI框架
- [Ant Design](https://ant.design/) - 组件库

## 📞 联系方式

- 项目主页: [https://github.com/yourusername/vip-memory](https://github.com/yourusername/vip-memory)
- 问题反馈: [GitHub Issues](https://github.com/yourusername/vip-memory/issues)
- 文档网站: [https://vip-memory.readthedocs.io](https://vip-memory.readthedocs.io)

---

**注意**: 本项目当前处于开发阶段，API可能会有变动。生产环境使用前请充分测试。
