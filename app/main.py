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
import logging

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


@app.middleware('http')
async def limit_body_size(request: Request, call_next):
    declared = request.headers.get('content-length')

    if (
        declared
        and declared.isdigit()
        and int(declared) > settings.MAX_REQUEST_BODY_BYTES
    ):
        return JSONResponse(
            status_code=413, content={'detail': 'Corpo da requisição grande demais.'}
        )

    return await call_next(request)


def _origin_from_referer(referer: str | None) -> str | None:
    if not referer:
        return None

    parts = urlsplit(referer)

    if not parts.scheme or not parts.netloc:
        return 'null'

    return f'{parts.scheme}://{parts.netloc}'

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
    expose_headers=['X-Total-Count'],
    max_age=3600,
)


CSRF_EXEMPT_PATHS = {'/api/v1/payments/webhook'}


@app.middleware('http')
async def csrf_origin_guard(request: Request, call_next):
    if (
        request.method in UNSAFE_METHODS
        and request.url.path not in CSRF_EXEMPT_PATHS
    ):
        origin = request.headers.get('origin') or _origin_from_referer(
            request.headers.get('referer')
        )
        same_origin = origin == f'{request.url.scheme}://{request.headers.get("host")}'

        if origin is not None and origin not in allowed_origins() and not same_origin:
            logging.warning(
                'CSRF 403: path=%s origin=%s referer=%s ua=%s',
                request.url.path,
                request.headers.get('origin'),
                request.headers.get('referer'),
                request.headers.get('user-agent'),
            )
            return JSONResponse(
                status_code=403, content={'detail': 'Origem não autorizada.'}
            )

    return await call_next(request)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={'detail': 'Você atingiu o limite de requisições'}
    )
