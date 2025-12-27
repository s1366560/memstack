# 分离 API 服务与后台任务队列计划

您提到的问题是由于后台任务（Episode 处理、Embedding 生成等）与 API 服务运行在同一个进程和事件循环中，导致资源争抢（CPU/Redis 连接）阻塞了 API 响应。

为了彻底解决这个问题，我计划将**任务处理逻辑（Worker）与 API 服务分离**，并提供灵活的配置选项。

## 1. 配置增强 (`server/config.py`)
*   新增配置项 `RUN_BACKGROUND_WORKERS` (默认 `True`)。
    *   `True`: 保持当前行为（单体模式），API 服务启动时同时也启动后台 Worker。
    *   `False`: 仅作为 API 服务运行（Producer 模式），只负责接收请求并推入队列，不处理任务。

## 2. 代码重构
*   **`server/services/queue_service.py`**:
    *   修改 `initialize` 方法，增加 `run_workers` 参数。
    *   只有当 `run_workers=True` 时，才启动 `_worker_loop` 和 `_recovery_loop`。
*   **`server/services/graphiti_service.py`**:
    *   在 `initialize` 中读取 `settings.RUN_BACKGROUND_WORKERS`，并将其传递给 `queue_service.initialize`。

## 3. 新增独立 Worker 入口 (`server/worker.py`)
*   创建一个新的启动脚本 `server/worker.py`。
*   该脚本将专门用于启动后台处理进程。它会初始化 `GraphitiService`（强制开启 Worker 模式），并保持进程运行以处理队列任务。

## 4. 部署方案（解决性能问题）
完成上述修改后，您将有两种选择来解决 API 响应慢的问题：

### 方案 A：快速缓解（无需架构调整）
*   调整 `.env` 中的配置：
    *   `MAX_ASYNC_WORKERS=2` (默认是 20，降低并发数以减少对主线程的阻塞)
    *   `RUN_BACKGROUND_WORKERS=True`

### 方案 B：彻底解决（推荐生产环境）
*   **API 服务**: 启动时设置 `RUN_BACKGROUND_WORKERS=False`。
    ```bash
    RUN_BACKGROUND_WORKERS=False uvicorn server.main:app
    ```
*   **Worker 服务**: 单独启动一个进程处理任务。
    ```bash
    # 新增的脚本
    python -m server.worker
    ```
这样，繁重的后台任务将完全独立于 API 进程，不再影响接口响应速度。

我将执行以上代码变更。
