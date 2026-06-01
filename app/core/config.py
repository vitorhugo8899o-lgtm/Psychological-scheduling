from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    DATABASE_URL: str
    SECRET_KEY: str
    ACESSES_TOKEN_EXPIRE_MINUTES: int
    ALGORITHM: str
    REDIS_URL: str
    API_KEY_MERCADO_PAGO: str
    TESTING: bool = False
    ENV: str
    API_KEY_GROQ: str
    LINK_FRONTEND: str
    SENTRY_DSN: str


settings = Settings()
