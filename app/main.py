import sys
from contextlib import asynccontextmanager

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


app = FastAPI(lifespan=lifespan)

app.include_router(api_router, prefix='/api/v1')


origins_test = ['http://localhost:5173', 'http://127.0.0.1:5173']


origins_production = [
    'https://frontend-psychological-scheduling-o21c5ujfl.vercel.app',
    'https://frontend-psychological-scheduling.vercel.app',
    'https://frontend-psychological-scheduling-o21c5ujfl.vercel.app',
    'https://frontend-psychological-scheduling-vitor-hugos-projects-411fbd87.vercel.app',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_production,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
    expose_headers=['X-Total-Count'],
    max_age=3600,
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={'detail': 'Você atingiu o limite de requisições'}
    )
