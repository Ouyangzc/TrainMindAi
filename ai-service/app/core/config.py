"""应用配置：全部从环境变量 / .env 注入（pydantic-settings）。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 应用
    app_env: str = "dev"
    app_name: str = "trainmind-ai-service"
    log_level: str = "INFO"

    # 内部鉴权（与 RuoYi 共享的强随机串）
    internal_token: str = "change-me"

    # 数据库（与 RuoYi 共享实例，独立 ai schema）
    database_url: str = "postgresql+asyncpg://postgres:123456@localhost:5432/ruoyi"
    db_schema: str = "ai"
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # 对象存储（S3 兼容）
    object_storage_endpoint: str = "http://127.0.0.1:8333"
    object_storage_access_key: str = "trainmind"
    object_storage_secret_key: str = "trainmind-secret"
    object_storage_bucket: str = "trainmind-docs"
    object_storage_region: str = "us-east-1"
    object_storage_path_style: bool = True

    # 向量库
    vector_store: str = "pgvector"  # pgvector / qdrant
    qdrant_url: str = "http://localhost:6333"

    # 模型网关（OpenAI 兼容；LLM 与 Embedding base_url 分离）
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "bge-m3"
    embedding_dim: int = 1024

    # 可选：仅当前端直连 FastAPI 流式端点时启用
    ruoyi_jwt_secret: str = ""
    ruoyi_jwt_alg: str = "HS512"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
