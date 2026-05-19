from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from groq import Groq
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.repositories import user_repo
from app.api.v1.services import auth_service
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.users_models import User
from app.redis.session import redis_client

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONTEXT_PATH = BASE_DIR / "groq" / "groq_context.md"

client = Groq(api_key=settings.API_KEY_GROQ)


try:
    PROMPT_SYSTEM = CONTEXT_PATH.read_text(encoding="utf-8")
except FileNotFoundError:
    print(f"Erro: Arquivo não encontrado no caminho {CONTEXT_PATH}")
    PROMPT_SYSTEM = "Você é um assistente prestativo."


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis():
    return redis_client


async def get_current_user(request: Request, db: DBSession) -> User:
    token = auth_service.get_token(request)

    if not token:
        raise HTTPException(status_code=401, detail='Usuário não Autenticado.')

    user_email = auth_service.decode_token(token)

    user = await user_repo.get_user_by_email(db, user_email)

    if not user:
        raise HTTPException(status_code=409, detail='Usuário não encontrado!')

    request.state.user = user.id

    return user


async def completion(client, message: str, context_agent: str):
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": context_agent},
            {"role": "user", "content": message}
        ],
        stream=True
    )

    return completion


DBSession = Annotated[AsyncSession, Depends(get_db)]
rediscon = Annotated[aioredis.Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_user)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/login', auto_error=False)
