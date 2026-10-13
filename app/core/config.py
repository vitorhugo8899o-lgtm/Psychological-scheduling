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

    # --- Opções de segurança (todas com padrão compatível com o comportamento atual)
    # Origens permitidas (CORS + verificação de Origin), separadas por vírgula.
    # Vazio = usa a lista padrão definida em app/main.py.
    CORS_ORIGINS: str = ''
    # /docs, /redoc e /openapi.json ficam desligados em produção, a menos que
    # ENABLE_DOCS=true.
    ENABLE_DOCS: bool = False
    # Quantos proxies confiáveis existem na frente da aplicação (Render, Cloudflare...).
    # 0 = usa o IP do socket. Veja app/redis/limiter.py.
    TRUSTED_PROXY_HOPS: int = 0
    # Tolerância (segundos) do timestamp do webhook do Mercado Pago (anti-replay).
    WEBHOOK_TOLERANCE_SECONDS: int = 300
    # Consultas pendentes (sem pagamento) deixam de bloquear a agenda após este prazo.
    PENDING_APPOINTMENT_TTL_MINUTES: int = 30
    MAX_PENDING_APPOINTMENTS_PER_USER: int = 2
    # Antecedência mínima (horas) para cancelar/remarcar uma consulta.
    CANCEL_MIN_HOURS_BEFORE: int = 24
    # Bloqueio de login por conta após N falhas dentro da janela.
    LOGIN_MAX_FAILURES: int = 10
    LOGIN_FAILURE_WINDOW_SECONDS: int = 900
    # Assistente de IA
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
