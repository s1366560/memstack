# VIP Memory - 企业级 AI 记忆云平台

基于开源项目 [Graphiti](https://github.com/getzep/graphiti) 构建的企业级 AI 记忆云平台，为 AI 应用和智能体提供强大的长短期记忆管理能力。

## 核心特性

- 🧠 **动态知识整合** - 实时整合对话数据、结构化业务数据和外部信息，无需批量重计算
- ⏰ **时态感知** - 双时间戳模型支持精确的历史时点查询
- ⚡ **高性能检索** - 混合检索机制（语义 + 关键词 + 图遍历）实现亚秒级响应
- 🔧 **开箱即用** - 完整的用户管理、可视化工具、SDK 和 API
- 🏢 **企业级保障** - SLA 保证、安全合规、技术支持和性能优化
- 📊 **完整评测体系** - 内置 LoCoMo、LongMemEval、PersonaMem、PrefEval 等评测基准
- 🤖 **多 LLM 支持** - 支持 Google Gemini 和阿里云通义千问 (Qwen)，可灵活切换

## 架构设计

基于 Graphiti 的三层知识图谱架构：

1. **Episode 子图** - 存储原始事件数据
2. **Semantic Entity 子图** - 提取的实体和关系，支持语义检索
3. **Community 子图** - 实体聚类群组，优化检索性能

## 项目结构

```
vip-memory/
├── server/              # 后端服务
│   ├── api/            # RESTful API
│   ├── services/       # 业务逻辑服务
│   ├── models/         # 数据模型
│   ├── llm_clients/    # LLM 客户端（Gemini, Qwen）
│   └── graphiti/       # Graphiti 集成
├── sdk/                # 多语言 SDK
│   └── python/         # Python SDK
├── web/                # Web 控制台
├── evaluation/         # 评测模块
├── docs/               # 文档
└── tests/              # 测试
```

## 快速开始

### 前置要求

- Python 3.10+
- Neo4j 5.26+ 或 Amazon Neptune
- Redis (可选，用于缓存)
- LLM API Key (Google Gemini 或阿里云通义千问)

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/vip-memory.git
cd vip-memory

# 使用 uv 安装依赖（推荐）
uv sync --python 3.12

# 或使用 pip
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 运行服务

```bash
# 启动依赖服务（Neo4j, Redis）
docker-compose up -d neo4j redis

# 启动 API 服务
python -m server.main

# 或使用 uvicorn
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Docker Compose 启动所有服务
docker-compose up
```

### 验证启动

访问以下端点验证服务是否正常运行：

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 根端点：http://localhost:8000/

### 故障排查

如果遇到启动问题，请查看：

- **[启动故障排查指南](docs/startup-troubleshooting.md)** - 详细的问题诊断和解决方案
- **测试启动**：`python scripts/test_startup.py`
- **查看日志**：`docker-compose logs -f`

## 开发路线图

- [x] MVP (3 个月)
  - [x] Episode 摄入（文本和 JSON）
  - [x] 基础实体和关系提取
  - [x] 简单的语义检索
  - [x] RESTful API
  - [x] Python SDK
  - [ ] 基础 Web 控制台

- [ ] Beta 版本 (6 个月)
  - [ ] 多租户隔离
  - [ ] 混合检索
  - [ ] 时态查询
  - [ ] TypeScript SDK
  - [ ] 基础评测框架

- [ ] 正式版 (9 个月)
  - [ ] 完整评测体系
  - [ ] 企业级功能

## 文档

📚 **[文档中心](docs/README.md)** - 完整的文档导航

### 快速开始
- [快速入门](docs/quickstart.md) - 5分钟快速上手

### Qwen 集成
- [Qwen 集成指南](docs/QWEN_INTEGRATION.md) - 通义千问集成文档
- [Qwen Reranker 使用指南](docs/QWEN_RERANKER_USAGE.md) - Reranker 功能使用
- [DashScope SDK 迁移](docs/DASHSCOPE_MIGRATION.md) - SDK 迁移说明
- [环境变量统一说明](docs/ENV_VARIABLES_UNIFIED.md) - 配置规范
- [Qwen 变更日志](docs/CHANGELOG_QWEN.md) - 完整的变更记录

### 运维文档
- [启动故障排查](docs/startup-troubleshooting.md) - 常见启动问题诊断和解决
- [OpenTelemetry 指南](docs/opentelemetry-guide.md) - 可观测性配置
- [Telemetry 迁移](docs/TELEMETRY-MIGRATION.md) - Telemetry 系统迁移

### 设计文档
- [产品设计](.qoder/quests/cloud-product-creation.md) - 完整的产品设计文档

## 参考资料

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Zep 论文](https://arxiv.org/abs/2501.13956)
- [MemOS GitHub](https://github.com/MemTensor/MemOS)

## 许可证

MIT License

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。
