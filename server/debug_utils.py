"""调试工具模块"""

import json
import time
from functools import wraps
from typing import Any, Callable

from server.logging_config import get_logger

logger = get_logger(__name__)


def debug_timer(func: Callable) -> Callable:
    """函数执行时间装饰器

    用法:
        @debug_timer
        async def my_function():
            ...
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.debug(f"开始执行: {func.__name__}")

        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"完成执行: {func.__name__} (耗时: {elapsed:.3f}秒)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"执行失败: {func.__name__} (耗时: {elapsed:.3f}秒) - {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.debug(f"开始执行: {func.__name__}")

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"完成执行: {func.__name__} (耗时: {elapsed:.3f}秒)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"执行失败: {func.__name__} (耗时: {elapsed:.3f}秒) - {e}")
            raise

    # 根据函数类型返回对应的包装器
    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def debug_log_args(func: Callable) -> Callable:
    """记录函数参数装饰器

    用法:
        @debug_log_args
        def my_function(arg1, arg2):
            ...
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"{func.__name__} 调用参数: args={args}, kwargs={kwargs}")
        return await func(*args, **kwargs)

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"{func.__name__} 调用参数: args={args}, kwargs={kwargs}")
        return func(*args, **kwargs)

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def pretty_print_json(data: Any, indent: int = 2) -> None:
    """美化打印 JSON 数据

    Args:
        data: 要打印的数据
        indent: 缩进空格数
    """
    try:
        if isinstance(data, str):
            data = json.loads(data)
        print(json.dumps(data, indent=indent, ensure_ascii=False))
    except Exception as e:
        logger.error(f"JSON 打印失败: {e}")
        print(data)


class DebugContext:
    """调试上下文管理器

    用法:
        with DebugContext('操作名称'):
            # 你的代码
            ...
    """

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f">>> 开始: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if exc_type:
            logger.error(f"<<< 失败: {self.name} (耗时: {elapsed:.3f}秒) - {exc_val}")
        else:
            logger.debug(f"<<< 完成: {self.name} (耗时: {elapsed:.3f}秒)")
        return False


def log_exception(func: Callable) -> Callable:
    """异常日志装饰器

    用法:
        @log_exception
        def my_function():
            ...
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"{func.__name__} 发生异常: {e}")
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"{func.__name__} 发生异常: {e}")
            raise

    import asyncio

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
