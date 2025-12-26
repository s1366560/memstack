"""Configuration management for MemStack."""

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")
    api_allowed_origins: Union[str, List[str]] = Field(default=["*"], alias="API_ALLOWED_ORIGINS")

    # Database Settings
    neo4j_uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="memstack", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="password", alias="POSTGRES_PASSWORD")

    # Redis Settings
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")

    # LLM Provider Selection
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")  # 'gemini' or 'qwen'

    # LLM Provider - Gemini
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_embedding_model: str = Field(
        default="text-embedding-004", alias="GEMINI_EMBEDDING_MODEL"
    )

    # LLM Provider - Qwen (通义千问)
    qwen_api_key: Optional[str] = Field(default=None, alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field(default="qwen-plus", alias="QWEN_MODEL")
    qwen_small_model: str = Field(default="qwen-turbo", alias="QWEN_SMALL_MODEL")
    qwen_embedding_model: str = Field(default="text-embedding-v3", alias="QWEN_EMBEDDING_MODEL")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_small_model: str = Field(default="gpt-4o-mini", alias="OPENAI_SMALL_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )

    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    # API Key Settings
    require_api_key: bool = Field(default=True, alias="REQUIRE_API_KEY")
    api_key_header_name: str = Field(default="Authorization", alias="API_KEY_HEADER_NAME")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # Graphiti Settings
    graphiti_semaphore_limit: int = Field(default=10, alias="GRAPHITI_SEMAPHORE_LIMIT")
    max_async_workers: int = Field(default=20, alias="MAX_ASYNC_WORKERS")
    queue_batch_size: int = Field(default=1, alias="QUEUE_BATCH_SIZE")

    # Monitoring
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")

    # OpenTelemetry Settings
    service_name: str = Field(default="memstack", alias="SERVICE_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    otel_exporter_otlp_endpoint: Optional[str] = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    enable_telemetry: bool = Field(default=True, alias="ENABLE_TELEMETRY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def auto_select_provider(self) -> "Settings":
        """Auto-select provider based on available API keys if not explicitly set to a valid one."""
        # If provider is default (gemini) but no Gemini key, try other providers
        if self.llm_provider.lower() == "gemini" and not self.gemini_api_key:
            if self.qwen_api_key:
                self.llm_provider = "qwen"
            elif self.openai_api_key:
                self.llm_provider = "openai"

        return self

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
