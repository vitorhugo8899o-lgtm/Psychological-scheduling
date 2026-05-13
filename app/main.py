import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import api_router
from app.db.session import engine


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


origins = [
    'http://127.0.0.1:5500',
    'http://localhost:5500',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={'detail': 'Você atingiu o limite de requisições'}
    )
