from typing import Annotated

from fastapi import Depends, HTTPException, Request
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.services import auth_service
from app.db.session import AsyncSessionLocal
from app.models.users_models import User
from app.redis.session import redis_client


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

    stmt = select(User).where(User.email == user_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=409, detail='Usuário não encontrado!')

    return user


DBSession = Annotated[AsyncSession, Depends(get_db)]
rediscon = Annotated[aioredis.Redis, Depends(get_redis)]
