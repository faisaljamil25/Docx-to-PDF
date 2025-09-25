from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "docx-to-pdf"
    API_V1_PREFIX: str = "/api/v1"
    ENV: str = Field("development", validation_alias="ENV")

    # Storage paths (shared volume)
    STORAGE_ROOT: str = Field("/data", validation_alias="STORAGE_ROOT")
    INPUT_DIR: str = Field("inputs", validation_alias="INPUT_DIR")
    OUTPUT_DIR: str = Field("outputs", validation_alias="OUTPUT_DIR")
    ARCHIVE_DIR: str = Field("archives", validation_alias="ARCHIVE_DIR")

    # Database
    POSTGRES_HOST: str = Field("postgres", validation_alias="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, validation_alias="POSTGRES_PORT")
    POSTGRES_DB: str = Field("docx2pdf", validation_alias="POSTGRES_DB")
    POSTGRES_USER: str = Field("docx2pdf", validation_alias="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field("docx2pdf", validation_alias="POSTGRES_PASSWORD")
    DATABASE_URL_RAW: Optional[str] = Field(
        default=None, validation_alias="DATABASE_URL"
    )

    # Broker/Queue
    REDIS_HOST: str = Field("redis", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(6379, validation_alias="REDIS_PORT")
    REDIS_DB: int = Field(0, validation_alias="REDIS_DB")
    REDIS_URL_RAW: Optional[str] = Field(default=None, validation_alias="REDIS_URL")

    # Conversion
    SOFFICE_BIN: str = Field("soffice", validation_alias="SOFFICE_BIN")

    model_config = SettingsConfigDict(
        case_sensitive=False, env_file=".env", extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_RAW:
            return self.DATABASE_URL_RAW
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_URL_RAW:
            return self.REDIS_URL_RAW
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def STORAGE_INPUT(self) -> str:
        return f"{self.STORAGE_ROOT}/{self.INPUT_DIR}"

    @property
    def STORAGE_OUTPUT(self) -> str:
        return f"{self.STORAGE_ROOT}/{self.OUTPUT_DIR}"

    @property
    def STORAGE_ARCHIVES(self) -> str:
        return f"{self.STORAGE_ROOT}/{self.ARCHIVE_DIR}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
