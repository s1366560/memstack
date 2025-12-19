# VIP Memory 文档中心

## 📚 文档导航

### 快速开始
- **[快速入门指南](quickstart.md)** - 5分钟快速上手

### Qwen 集成文档
- **[Qwen 集成指南](QWEN_INTEGRATION.md)** - 完整的 Qwen 集成说明
- **[Qwen Reranker 使用指南](QWEN_RERANKER_USAGE.md)** - Reranker 功能使用
- **[DashScope SDK 迁移](DASHSCOPE_MIGRATION.md)** - 从 OpenAI SDK 到 DashScope SDK 的迁移说明
- **[环境变量统一说明](ENV_VARIABLES_UNIFIED.md)** - 环境变量配置规范
- **[Qwen 变更日志](CHANGELOG_QWEN.md)** - 完整的变更记录和修复历史

### 运维文档
- **[启动故障排查](startup-troubleshooting.md)** - 常见启动问题诊断和解决
- **[OpenTelemetry 指南](opentelemetry-guide.md)** - 可观测性配置
- **[Telemetry 迁移](TELEMETRY-MIGRATION.md)** - Telemetry 系统迁移

## 📖 文档说明

### Qwen 集成
项目已完成阿里云通义千问（Qwen）LLM 的集成，支持在 Gemini 和 Qwen 之间灵活切换。

**核心特性：**
- ✅ LLM 客户端（QwenClient）
- ✅ Embedding 客户端（QwenEmbedder）
- ✅ Reranker 支持（QwenRerankerClient）
- ✅ DashScope SDK 原生支持
- ✅ 异步调用优化

**快速切换：**
```bash
# 在 .env 文件中设置
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your-api-key
```

### 最新更新

**2025-12-19:**
- ✅ 修复 DashScope SDK 异步调用问题
- ✅ 使用 `asyncio.to_thread` 包装同步 API
- ✅ 统一环境变量为 `DASHSCOPE_API_KEY`
- ✅ 文档结构重构和清理

## 🔗 相关链接

- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [阿里云百炼控制台](https://dashscope.console.aliyun.com/)
- [Qwen API 文档](https://help.aliyun.com/zh/dashscope/)

## 📝 贡献文档

如需更新文档，请遵循以下原则：
1. 保持文档简洁明确
2. 使用中文撰写
3. 包含实际代码示例
4. 及时更新变更日志
