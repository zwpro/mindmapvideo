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
    # 备用 key：主 key 失败（429 / 5xx / 余额不足 / 超时等）时自动重试一次，
    # 还失败才会降级到 SoCheap。留空则跳过本步重试，直接到 SoCheap。
    AIGCDESK_API_KEY_BACKUP: str = ""
    AIGCDESK_BASE_URL: str = "https://api.aigcdesk.com/v1"
    AIGCDESK_MODEL: str = ""
    AIGCDESK_TIMEOUT_SECONDS: float = 120.0

    # SoCheap（Anthropic Messages 协议）— AIGCDesk 的回退通道
    # 调用 _generate_manim_script 时若 AIGCDesk 异常会自动转走这条线路
    SOCHEAP_API_KEY: str = ""
    SOCHEAP_BASE_URL: str = "https://api.socheap.cc"
    SOCHEAP_MODEL: str = ""
    SOCHEAP_TIMEOUT_SECONDS: float = 120.0

    # 媒体存储
    MEDIA_ROOT: str = "./media"
    MEDIA_BASE_URL: str = "http://localhost:8000/media"

    # manim 渲染子进程的硬超时（秒）。
    # 经验值：720p30 下复杂思维导图脚本（8+ 场景，几十个 self.play）通常耗时
    # 5~15 分钟；30s 短脚本约 1 分钟。默认放到 30 分钟，避免正常脚本被误杀。
    # 真正卡死的脚本（死循环等）仍会被强制 kill。
    MANIM_TIMEOUT_SECONDS: int = 1800


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
