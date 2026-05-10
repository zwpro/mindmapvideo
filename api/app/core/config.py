"""应用配置：从环境变量 / .env 加载。"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 应用
    APP_NAME: str = "mindmap-api"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # CORS
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    # 数据库（开发与生产均使用 MySQL，保持一致性）
    DATABASE_URL: str = (
        "mysql+asyncmy://mindmap:mindmap@localhost:3306/mindmap?charset=utf8mb4"
    )

    # Redis / 队列
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "please-change-this-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # LLM - OpenAI 兼容
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # 火山引擎方舟 Responses API
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_MODEL: str = "doubao-seed-1-6-251015"
    ARK_TIMEOUT_SECONDS: float = 120.0

    # AIGCDesk（OpenAI 兼容 Chat Completions）
    AIGCDESK_API_KEY: str = ""
    AIGCDESK_BASE_URL: str = "https://api.aigcdesk.com/v1"
    AIGCDESK_MODEL: str = ""
    AIGCDESK_TIMEOUT_SECONDS: float = 120.0

    # 媒体存储
    MEDIA_ROOT: str = "./media"
    MEDIA_BASE_URL: str = "http://localhost:8000/media"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
