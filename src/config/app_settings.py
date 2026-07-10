from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    MODEL_PATH: str
    VIDEO_PATH: str | None = None

    DISPLAY_MAX_WIDTH: int = 1280

    USE_WEBCAM: bool = False
    WEBCAM_INDEX: int = 0

    SAVE_OUTPUT: bool = False
    OUTPUT_PATH: str = "./output/result.mp4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
