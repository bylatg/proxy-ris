from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Proxy Admin"
    app_env: str = "dev"
    secret_key: str = "change-me"
    database_url: str = "postgresql+psycopg://proxy_admin:proxy_admin@127.0.0.1:5432/proxy_admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()