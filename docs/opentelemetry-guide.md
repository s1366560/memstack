# OpenTelemetry 配置和使用指南

VIP Memory 使用 OpenTelemetry 进行分布式追踪和可观测性，替代了 Graphiti 默认的 PostHog 遥测。

## 📋 概述

### 为什么使用 OpenTelemetry？

- **标准化**：OpenTelemetry 是 CNCF 的标准可观测性框架
- **供应商中立**：支持多种后端（Jaeger、Zipkin、Prometheus、Grafana 等）
- **功能强大**：支持追踪、指标和日志
- **无外部依赖**：不需要连接到第三方服务（如 PostHog）

### 已禁用的服务

VIP Memory 自动禁用了以下遥测服务：
- **PostHog**：Graphiti 默认使用的分析服务
- **Graphiti 内置遥测**：通过环境变量禁用

## 🚀 快速开始

### 1. 基本配置

在 `.env` 文件中配置 OpenTelemetry：

```bash
# OpenTelemetry 基本设置
SERVICE_NAME=vip-memory
ENVIRONMENT=development
ENABLE_TELEMETRY=true

# 可选：配置 OTLP 导出器（生产环境）
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 2. 开发环境

开发环境默认使用控制台导出器，traces 直接输出到控制台：

```bash
# 启动应用
python -m server.main
```

您将看到类似的 trace 输出：

```json
{
  "name": "GET /api/v1/episodes/",
  "context": {
    "trace_id": "0x...",
    "span_id": "0x...",
    "trace_state": "[]"
  },
  "kind": "SpanKind.SERVER",
  "parent_id": null,
  "start_time": "2025-12-19T12:00:00.000000Z",
  "end_time": "2025-12-19T12:00:00.150000Z",
  "status": {"status_code": "UNSET"},
  "attributes": {
    "http.method": "GET",
    "http.route": "/api/v1/episodes/",
    "http.status_code": 200
  }
}
```

### 3. 生产环境

生产环境配置 OTLP 导出器，将 traces 发送到收集器：

```bash
# 配置 OTLP 端点
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317

# 或使用 Grafana Tempo
# OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317

# 设置环境
ENVIRONMENT=production
```

## 🔧 集成后端收集器

### 选项 1：Jaeger（推荐用于开发）

```yaml
# docker-compose.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

启动 Jaeger：

```bash
docker-compose up -d jaeger
```

配置应用：

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

访问 Jaeger UI：http://localhost:16686

### 选项 2：Grafana Stack（推荐用于生产）

```yaml
# docker-compose.yml
services:
  tempo:
    image: grafana/tempo:latest
    ports:
      - "4317:4317"    # OTLP gRPC
      - "3200:3200"    # Tempo HTTP
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
    command: ["-config.file=/etc/tempo.yaml"]
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
```

配置应用：

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 选项 3：Zipkin

```yaml
# docker-compose.yml
services:
  zipkin:
    image: openzipkin/zipkin:latest
    ports:
      - "9411:9411"
```

配置应用（使用 Zipkin 导出器）：

```python
# 需要修改 server/telemetry.py 使用 ZipkinExporter
from opentelemetry.exporter.zipkin.json import ZipkinExporter
```

## 💻 代码中使用 OpenTelemetry

### 基本追踪

```python
from server.telemetry import get_tracer

async def my_function():
    tracer = get_tracer(__name__)
    
    # 创建一个 span
    with tracer.start_as_current_span("my_operation") as span:
        # 添加属性
        span.set_attribute("user.id", user_id)
        span.set_attribute("operation.type", "create")
        
        # 执行操作
        result = await do_something()
        
        # 添加事件
        span.add_event("operation_completed", {
            "result_count": len(result)
        })
        
        return result
```

### 嵌套追踪

```python
async def parent_operation():
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("parent") as parent:
        parent.set_attribute("level", "parent")
        
        # 子操作 1
        with tracer.start_as_current_span("child_1"):
            await child_operation_1()
        
        # 子操作 2
        with tracer.start_as_current_span("child_2"):
            await child_operation_2()
```

### 错误追踪

```python
async def operation_with_error_handling():
    tracer = get_tracer(__name__)
    
    with tracer.start_as_current_span("risky_operation") as span:
        try:
            await risky_operation()
        except Exception as e:
            # 记录异常
            span.record_exception(e)
            span.set_attribute("error", True)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
```

### 装饰器方式

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("decorated_function")
async def my_decorated_function(param1, param2):
    # 函数会自动被追踪
    return await do_work(param1, param2)
```

## 📊 查看 Traces

### Jaeger UI

1. 访问 http://localhost:16686
2. 选择服务：`vip-memory`
3. 点击 "Find Traces"
4. 点击具体的 trace 查看详情

### Grafana + Tempo

1. 访问 http://localhost:3000
2. 配置 Tempo 数据源
3. 使用 Explore 查看 traces
4. 可以结合 Loki 查看日志

## 🧪 测试和验证

### 运行示例

```bash
# 运行 OpenTelemetry 使用示例
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

示例 2：嵌套追踪操作
------------------------------------------------------------
开始父操作...
  执行子操作 1...
  执行子操作 2...
父操作完成！

示例 3：错误追踪
------------------------------------------------------------
尝试可能失败的操作...
捕获到错误: 这是一个示例错误

============================================================
所有示例执行完成！
============================================================
```

### 验证追踪

```bash
# 启动应用
python -m server.main

# 在另一个终端发送请求
curl http://localhost:8000/health

# 检查控制台输出的 traces
```

## ⚙️ 高级配置

### 采样配置

```python
# server/telemetry.py
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

# 50% 采样率
sampler = ParentBasedTraceIdRatio(0.5)
tracer_provider = TracerProvider(
    resource=resource,
    sampler=sampler
)
```

### 批量导出配置

```python
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 配置批量处理器
processor = BatchSpanProcessor(
    exporter,
    max_queue_size=2048,
    schedule_delay_millis=5000,
    max_export_batch_size=512
)
```

### 资源属性

```python
from opentelemetry.sdk.resources import Resource

resource = Resource.create({
    "service.name": "vip-memory",
    "service.version": "0.1.0",
    "deployment.environment": "production",
    "host.name": socket.gethostname(),
    "cloud.provider": "aws",
    "cloud.region": "us-east-1",
})
```

## 🔍 故障排查

### 问题 1：PostHog 连接警告

**现象**：
```
WARNING: Retrying connection to 'us.i.posthog.com'
```

**解决**：
✅ 已自动禁用！应用启动时自动设置：
```python
os.environ['POSTHOG_DISABLED'] = '1'
os.environ['GRAPHITI_TELEMETRY_DISABLED'] = '1'
```

### 问题 2：没有看到 traces

**检查清单**：
1. `ENABLE_TELEMETRY=true` 在 `.env` 中设置
2. 应用成功启动
3. 发送了一些请求到 API
4. 检查控制台输出（开发环境）
5. 检查收集器状态（生产环境）

### 问题 3：OTLP 导出失败

**错误**：
```
Failed to export traces to OTLP endpoint
```

**解决方案**：
1. 检查 `OTEL_EXPORTER_OTLP_ENDPOINT` 配置
2. 确认收集器正在运行
3. 检查网络连接
4. 验证端口正确（gRPC: 4317, HTTP: 4318）

## 📚 最佳实践

### 1. Span 命名

```python
# ✓ 好的命名
"GET /api/v1/episodes"
"database.query"
"llm.generate_embedding"

# ✗ 避免
"operation"
"process"
"handle"
```

### 2. 属性添加

```python
# 添加有意义的属性
span.set_attribute("user.id", user_id)
span.set_attribute("episode.count", count)
span.set_attribute("llm.model", "gpt-4")
span.set_attribute("database.operation", "insert")
```

### 3. 错误处理

```python
# 总是记录异常
try:
    await operation()
except Exception as e:
    span.record_exception(e)
    span.set_status(Status(StatusCode.ERROR))
    raise
```

### 4. 避免过度追踪

```python
# ✗ 不要追踪太细粒度的操作
with tracer.start_as_current_span("add_numbers"):
    return a + b

# ✓ 追踪有意义的业务操作
with tracer.start_as_current_span("process_episode"):
    # 包含多个步骤的复杂操作
    await extract_entities()
    await build_relationships()
    await update_graph()
```

## 🔗 相关资源

- **OpenTelemetry 官方文档**：https://opentelemetry.io/docs/
- **Python SDK 文档**：https://opentelemetry-python.readthedocs.io/
- **Jaeger 文档**：https://www.jaegertracing.io/docs/
- **Grafana Tempo 文档**：https://grafana.com/docs/tempo/

## 💡 示例：与 Graphiti 集成

在 `server/services/graphiti_service.py` 中添加追踪：

```python
from server.telemetry import get_tracer

class GraphitiService:
    def __init__(self):
        self._tracer = get_tracer(__name__)
    
    async def add_episode(self, episode_data: EpisodeCreate) -> Episode:
        with self._tracer.start_as_current_span("graphiti.add_episode") as span:
            span.set_attribute("episode.source_type", episode_data.source_type)
            span.set_attribute("episode.tenant_id", episode_data.tenant_id)
            
            try:
                episode = await self.client.add_episode(...)
                span.add_event("episode_created", {"episode_id": str(episode.id)})
                return episode
            except Exception as e:
                span.record_exception(e)
                raise
```

---

**最后更新**：2025-12-19  
**状态**：✅ PostHog 已禁用，OpenTelemetry 已启用
