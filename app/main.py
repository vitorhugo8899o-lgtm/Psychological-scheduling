import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
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
