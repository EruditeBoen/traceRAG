from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://tracerag:tracerag@db:5432/tracerag"
    redis_url: str = "redis://redis:6379/0"
    app_env: str = "local"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()