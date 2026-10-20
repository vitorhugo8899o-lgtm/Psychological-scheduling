from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from groq import AsyncGroq
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.repositories import user_repo
from app.api.v1.services import auth_service
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.users_models import User
from app.redis.session import redis_client

BASE_DIR = Path(__file__).resolve().parent.parent.parent

CONTEXT_PATH = BASE_DIR / 'groq' / 'groq_context.md'

client = AsyncGroq(
    api_key=settings.API_KEY_GROQ,
    timeout=settings.GROQ_TIMEOUT_SECONDS,
    max_retries=1,
)

GROQ_TEMPERATURE = 0.4


try:
    PROMPT_SYSTEM = CONTEXT_PATH.read_text(encoding='utf-8')
except FileNotFoundError:
    print(f'Erro: Arquivo não encontrado no caminho {CONTEXT_PATH}')
    PROMPT_SYSTEM = 'Você é um assistente prestativo.'


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_redis():
    return redis_client


async def get_current_user(request: Request, db: DBSession, r: rediscon) -> User:
    token = auth_service.get_token(request)

    if not token:
        raise HTTPException(status_code=401, detail='Usuário não Autenticado.')

    payload = auth_service.decode_token_payload(token)

    user = await user_repo.get_user_by_email(db, payload['sub'])

    if not user:
        raise HTTPException(status_code=409, detail='Usuário não encontrado!')

    if (
        not user.is_active
        or payload.get('tv', 0) != user.token_version
        or await auth_service.is_token_revoked(r, payload)
    ):
        raise HTTPException(
            status_code=401, detail='Sessão inválida ou expirada. Faça login novamente.'
        )

    request.state.user = user.id
    request.state.token_payload = payload

    return user


async def completion(
    client, message: str, context_agent: str, user_ref: str | None = None
):
    params = {
        'model': settings.GROQ_MODEL,
        'messages': [
            {'role': 'system', 'content': context_agent},
            {'role': 'user', 'content': message},
        ],
        'temperature': GROQ_TEMPERATURE,
        'max_completion_tokens': settings.GROQ_MAX_COMPLETION_TOKENS,
        'stream': False,
    }

    if 'gpt-oss' in settings.GROQ_MODEL:
        params['reasoning_effort'] = 'low'

    if user_ref:
        params['user'] = user_ref

    return await client.chat.completions.create(**params)


DBSession = Annotated[AsyncSession, Depends(get_db)]
rediscon = Annotated[aioredis.Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_user)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/login', auto_error=False)
