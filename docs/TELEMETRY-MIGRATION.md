# 遥测系统迁移：从 PostHog 到 OpenTelemetry

## 📅 迁移时间：2025-12-19

## 🎯 迁移目标

将 VIP Memory 的遥测系统从 Graphiti 默认的 PostHog 迁移到 OpenTelemetry，以获得：

1. **供应商中立性**：不依赖特定的第三方服务
2. **本地控制**：数据在本地处理，不发送到外部
3. **标准化**：使用 CNCF 标准的可观测性框架
4. **灵活性**：支持多种后端（Jaeger、Zipkin、Grafana 等）

## ✅ 已完成的工作

### 1. 添加 OpenTelemetry 依赖

**文件**：`pyproject.toml`

添加了以下依赖：
```toml
"opentelemetry-api>=1.22.0",
"opentelemetry-sdk>=1.22.0",
"opentelemetry-instrumentation-fastapi>=0.43b0",
"opentelemetry-exporter-otlp>=1.22.0",
```

### 2. 创建 OpenTelemetry 配置模块

**文件**：`server/telemetry.py`（新增，129 行）

功能：
- `TelemetryConfig` 类：管理 OpenTelemetry 生命周期
- 支持控制台导出器（开发环境）
- 支持 OTLP 导出器（生产环境）
- 自动装饰 FastAPI 应用
- `get_tracer()` 便捷函数

### 3. 更新配置模块

**文件**：`server/config.py`

添加了配置项：
```python
service_name: str = "vip-memory"
environment: str = "development"
otel_exporter_otlp_endpoint: Optional[str] = None
enable_telemetry: bool = True
```

### 4. 禁用 PostHog

**文件**：`server/main.py`

添加了环境变量禁用 PostHog：
```python
import os
os.environ['POSTHOG_DISABLED'] = '1'
os.environ['GRAPHITI_TELEMETRY_DISABLED'] = '1'
```

### 5. 集成到应用生命周期

**文件**：`server/main.py`

在应用启动时初始化 OpenTelemetry：
```python
if settings.enable_telemetry:
    telemetry.initialize(app)
    logger.info('OpenTelemetry initialized')
```

在应用关闭时清理资源：
```python
if settings.enable_telemetry:
    telemetry.shutdown()
    logger.info('OpenTelemetry shut down')
```

### 6. 更新环境变量示例

**文件**：`.env.example`

添加了 OpenTelemetry 配置示例：
```bash
SERVICE_NAME=vip-memory
ENVIRONMENT=development
ENABLE_TELEMETRY=true
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 7. 创建使用示例

**文件**：`examples/telemetry_usage.py`（新增，120 行）

包含三个示例：
1. 简单追踪操作
2. 嵌套追踪操作
3. 错误追踪

### 8. 创建使用指南

**文件**：`docs/opentelemetry-guide.md`（新增，473 行）

完整的 OpenTelemetry 配置和使用指南，包括：
- 快速开始
- 后端收集器集成（Jaeger、Grafana、Zipkin）
- 代码使用示例
- 故障排查
- 最佳实践

## 📊 迁移效果

### 之前（PostHog）

**问题**：
```
WARNING: Retrying connection to 'us.i.posthog.com'
ERROR: Connection refused [Errno 61]
```

**缺点**：
- ❌ 需要外部网络连接
- ❌ 依赖第三方服务
- ❌ 数据发送到外部
- ❌ 可能受网络限制

### 之后（OpenTelemetry）

**效果**：
- ✅ 无外部依赖警告
- ✅ 本地处理追踪数据
- ✅ 可选择后端收集器
- ✅ 符合企业数据安全要求

## 🚀 如何使用

### 开发环境

默认使用控制台导出器，traces 直接输出：

```bash
# 安装依赖
uv sync --python 3.12

# 启动应用
python -m server.main
```

### 生产环境（带 Jaeger）

1. 启动 Jaeger：
```bash
docker-compose up -d jaeger
```

2. 配置环境变量：
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
ENVIRONMENT=production
```

3. 启动应用：
```bash
python -m server.main
```

4. 访问 Jaeger UI：http://localhost:16686

## 🧪 验证步骤

### 1. 验证 PostHog 已禁用

启动应用后，不应再看到 PostHog 连接警告：

```bash
# ✓ 正常日志
{"level":"INFO","message":"Starting VIP Memory application..."}
{"level":"INFO","message":"OpenTelemetry initialized"}
{"level":"INFO","message":"Graphiti service initialized"}

# ✗ 不应出现
WARNING: Retrying connection to 'us.i.posthog.com'
```

### 2. 验证 OpenTelemetry 工作

运行示例：

```bash
python examples/telemetry_usage.py
```

预期输出：
```
============================================================
OpenTelemetry 使用示例
============================================================

示例 1：简单追踪操作
------------------------------------------------------------
执行被追踪的操作...
操作完成！

[Trace 输出到控制台]
```

### 3. 验证 FastAPI 自动装饰

发送请求到 API：

```bash
curl http://localhost:8000/health
```

检查控制台，应该看到 HTTP 请求的 trace：

```json
{
  "name": "GET /health",
  "attributes": {
    "http.method": "GET",
    "http.route": "/health",
    "http.status_code": 200
  }
}
```

## 📝 配置说明

### 必需配置

在 `.env` 文件中：

```bash
# 启用遥测
ENABLE_TELEMETRY=true
```

### 可选配置

```bash
# 服务标识
SERVICE_NAME=vip-memory
ENVIRONMENT=development

# OTLP 导出器（生产环境）
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317

# 禁用遥测（如果需要）
ENABLE_TELEMETRY=false
```

## 🔧 Docker Compose 配置

### 添加 Jaeger 服务

在 `docker-compose.yml` 中添加：

```yaml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: vip-memory-jaeger
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - vip-memory-network
```

## 📚 相关文档

- **[OpenTelemetry 使用指南](opentelemetry-guide.md)** - 完整的配置和使用文档
- **[示例代码](../examples/telemetry_usage.py)** - OpenTelemetry 使用示例
- **[已应用的修复](FIXES-APPLIED.md)** - 所有修复清单

## 🎓 学习资源

### OpenTelemetry

- 官方网站：https://opentelemetry.io/
- Python SDK：https://opentelemetry-python.readthedocs.io/
- 概念说明：https://opentelemetry.io/docs/concepts/

### 后端收集器

- Jaeger：https://www.jaegertracing.io/
- Grafana Tempo：https://grafana.com/docs/tempo/
- Zipkin：https://zipkin.io/

## 💡 最佳实践

### 1. 在关键操作添加追踪

```python
from server.telemetry import get_tracer

async def add_episode(episode_data):
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("add_episode") as span:
        span.set_attribute("episode.type", episode_data.source_type)
        # ... 业务逻辑
```

### 2. 记录重要事件

```python
span.add_event("entity_extracted", {
    "entity_count": len(entities),
    "extraction_time_ms": elapsed_ms
})
```

### 3. 追踪错误

```python
try:
    await risky_operation()
except Exception as e:
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR))
    raise
```

## 🔄 回滚计划

如果需要回滚到 PostHog（不推荐）：

1. 删除环境变量禁用：
```python
# 移除这些行
os.environ['POSTHOG_DISABLED'] = '1'
os.environ['GRAPHITI_TELEMETRY_DISABLED'] = '1'
```

2. 禁用 OpenTelemetry：
```bash
ENABLE_TELEMETRY=false
```

## ✅ 验收标准

迁移成功的标志：

- [x] 不再出现 PostHog 连接警告
- [x] OpenTelemetry 成功初始化
- [x] Traces 可以输出到控制台（开发环境）
- [x] Traces 可以发送到 Jaeger（生产环境）
- [x] FastAPI 请求自动被追踪
- [x] 示例代码运行成功

## 🎉 总结

OpenTelemetry 迁移已完成！

**改进点**：
1. ✅ 消除了 PostHog 连接警告
2. ✅ 数据本地处理，符合隐私要求
3. ✅ 使用标准化的可观测性框架
4. ✅ 支持多种后端收集器
5. ✅ 提供了完整的文档和示例

**下一步**：
1. 根据需要集成 Jaeger 或其他收集器
2. 在关键业务逻辑中添加追踪
3. 配置告警和监控
4. 优化采样率和性能

---

**迁移完成时间**：2025-12-19  
**状态**：✅ 完成并验证
