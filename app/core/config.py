from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_JWT_ALGORITHMS = {'HS256', 'HS384', 'HS512'}
MIN_SECRET_KEY_LENGTH = 32
PLACEHOLDER_SECRETS = {'sua_chave', 'secret', 'changeme', 'change_me', 'senha'}


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
    MERCADO_PAGO_SECRET: str

    CORS_ORIGINS: str = ''
    ENABLE_DOCS: bool = False
    TRUSTED_PROXY_HOPS: int = 0
    WEBHOOK_TOLERANCE_SECONDS: int = 300
    PENDING_APPOINTMENT_TTL_MINUTES: int = 30
    MAX_PENDING_APPOINTMENTS_PER_USER: int = 2
    CANCEL_MIN_HOURS_BEFORE: int = 24

    LOGIN_MAX_FAILURES: int = 10
    LOGIN_FAILURE_WINDOW_SECONDS: int = 900
    MAX_REQUEST_BODY_BYTES: int = 1_000_000

    GROQ_MODEL: str = 'openai/gpt-oss-20b'
    GROQ_MAX_COMPLETION_TOKENS: int = 512
    GROQ_TIMEOUT_SECONDS: float = 20.0

    @property
    def is_production(self) -> bool:
        return self.ENV == 'production'

    @model_validator(mode='after')
    def validate_security_settings(self):
        if self.ALGORITHM not in ALLOWED_JWT_ALGORITHMS:
            raise ValueError(
                f'ALGORITHM inválido: use um de {sorted(ALLOWED_JWT_ALGORITHMS)}.'
            )

        weak_secret = (
            len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH
            or self.SECRET_KEY.lower() in PLACEHOLDER_SECRETS
        )
        if weak_secret and self.is_production:
            raise ValueError(
                'SECRET_KEY fraca: use pelo menos 32 caracteres aleatórios '
                '(ex.: python -c "import secrets; print(secrets.token_urlsafe(48))").'
            )

        return self


settings = Settings()
