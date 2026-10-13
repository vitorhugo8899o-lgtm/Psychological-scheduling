import sys
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import engine

sentry_sdk.init(dsn=settings.SENTRY_DSN, send_default_pii=False, traces_sample_rate=0.1)


async def check_database_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except Exception as e:
        raise ConnectionError(f'Falha de conexão com o banco de dados: {e}')


@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        await check_database_connection()

    except Exception:
        sys.exit(1)

    yield

    await engine.dispose()


def docs_kwargs() -> dict:
    """/docs, /redoc e /openapi.json entregam o mapa completo da API a quem estiver
    procurando falhas: ficam desligados em produção (ENABLE_DOCS=true reativa)."""
    if settings.is_production and not settings.ENABLE_DOCS:
        return {'docs_url': None, 'redoc_url': None, 'openapi_url': None}

    return {}


app = FastAPI(lifespan=lifespan, **docs_kwargs())

app.include_router(api_router, prefix='/api/v1')


origins_test = ['http://localhost:5173', 'http://127.0.0.1:5173']


origins_production = [
    'https://frontend-psychological-scheduling-o21c5ujfl.vercel.app',
    'https://frontend-psychological-scheduling.vercel.app',
    'https://frontend-psychological-scheduling-vitor-hugos-projects-411fbd87.vercel.app',
]


def allowed_origins() -> list[str]:
    if settings.CORS_ORIGINS.strip():
        return [
            o.strip().rstrip('/') for o in settings.CORS_ORIGINS.split(',') if o.strip()
        ]

    if settings.is_production:
        return origins_production

    return origins_production + origins_test


UNSAFE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None

    parts = urlsplit(referer)

    if not parts.scheme or not parts.netloc:
        return 'null'

    return f'{parts.scheme}://{parts.netloc}'


@app.middleware('http')
async def csrf_origin_guard(request: Request, call_next):
    """Defesa contra CSRF (o cookie de sessão é SameSite=None em produção).

    Navegadores SEMPRE enviam `Origin` (ou `Referer`) em requisições que alteram
    estado vindas de outro site. Se vier uma origem que não é a do front-end, a
    requisição é recusada ANTES de chegar na rota. Clientes que não são navegadores
    (curl, app mobile, webhook do Mercado Pago) não enviam Origin e seguem normal.
    """
    if request.method in UNSAFE_METHODS:
        origin = request.headers.get('origin') or _origin_from_referer(
            request.headers.get('referer')
        )
        same_origin = origin == f'{request.url.scheme}://{request.headers.get("host")}'

        if origin is not None and origin not in allowed_origins() and not same_origin:
            return JSONResponse(
                status_code=403, content={'detail': 'Origem não autorizada.'}
            )

    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
    expose_headers=['X-Total-Count'],
    max_age=3600,
)


@app.middleware('http')
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault('X-Frame-Options', 'DENY')

    if request.url.path.startswith('/api/'):
        # Respostas autenticadas (prontuários, dados pessoais) não podem ser
        # guardadas por proxies/CDNs/navegadores compartilhados.
        response.headers.setdefault('Cache-Control', 'no-store')
        response.headers.setdefault(
            'Content-Security-Policy', "default-src 'none'; frame-ancestors 'none'"
        )

    if settings.is_production:
        response.headers.setdefault(
            'Strict-Transport-Security', 'max-age=31536000; includeSubDomains'
        )

    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={'detail': 'Você atingiu o limite de requisições'}
    )
