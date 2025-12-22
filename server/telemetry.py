"""OpenTelemetry 配置模块"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from server.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelemetryConfig:
    """OpenTelemetry 配置类"""

    def __init__(self):
        """初始化遥测配置"""
        self._tracer_provider: Optional[TracerProvider] = None
        self._is_initialized = False

    def initialize(self, app=None):
        """
        初始化 OpenTelemetry

        Args:
            app: FastAPI 应用实例（可选）
        """
        if self._is_initialized:
            logger.warning("Telemetry already initialized")
            return

        try:
            # 创建资源（标识服务）
            resource = Resource(
                attributes={
                    SERVICE_NAME: settings.service_name,
                    "environment": settings.environment,
                    "version": "0.1.0",
                }
            )

            # 创建 TracerProvider
            self._tracer_provider = TracerProvider(resource=resource)

            # 根据环境选择导出器
            if settings.otel_exporter_otlp_endpoint:
                # 使用 OTLP 导出器（生产环境）
                logger.info(f"Using OTLP exporter: {settings.otel_exporter_otlp_endpoint}")
                otlp_exporter = OTLPSpanExporter(
                    endpoint=settings.otel_exporter_otlp_endpoint,
                    # headers={"authorization": f"Bearer {settings.otel_api_key}"}  # 如果需要
                )
                self._tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            else:
                # 使用控制台导出器（开发环境）
                logger.info("Using console exporter for traces")
                console_exporter = ConsoleSpanExporter()
                self._tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))

            # 设置全局 TracerProvider
            trace.set_tracer_provider(self._tracer_provider)

            # 如果提供了 FastAPI app，自动装饰
            if app is not None:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI instrumented with OpenTelemetry")

            self._is_initialized = True
            logger.info("OpenTelemetry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            raise

    def shutdown(self):
        """关闭遥测系统"""
        if self._tracer_provider and self._is_initialized:
            try:
                # 刷新和关闭所有 span 处理器
                self._tracer_provider.shutdown()
                logger.info("OpenTelemetry shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down OpenTelemetry: {e}")

    def get_tracer(self, name: str = __name__):
        """
        获取 Tracer 实例

        Args:
            name: tracer 名称

        Returns:
            Tracer 实例
        """
        if not self._is_initialized:
            logger.warning("Telemetry not initialized, initializing now...")
            self.initialize()

        return trace.get_tracer(name)


# 全局遥测实例
telemetry = TelemetryConfig()


def get_tracer(name: str = __name__):
    """
    获取 Tracer 的便捷函数

    Args:
        name: tracer 名称

    Returns:
        Tracer 实例
    """
    return telemetry.get_tracer(name)
