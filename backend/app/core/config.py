from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TraceLedger API"
    app_version: str = "0.1.0"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://traceledger:traceledger"
        "@localhost:5432/traceledger"
    )
    gemini_api_key: str

    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()