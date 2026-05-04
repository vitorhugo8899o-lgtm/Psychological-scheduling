from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    InvalidRequestError,
    OperationalError,
)

from app.api.v1.repositories import auth_repo
from app.models.users_models import User
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate

if TYPE_CHECKING:
    from app.api.v1.dependencies import CurrentUser, DBSession, rediscon


async def new_user(db: DBSession, user_data: UserCreate) -> User:
    user = User(
        fullname=user_data.fullname,
        email=user_data.email,
        password=auth_repo.hash_password(user_data.password),
    )
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail={'message': 'Error inesperado', 'contexto': str(e)},
        )


async def get_user_by_email(db: DBSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    exist = await db.execute(stmt)

    return exist.scalar_one_or_none()


async def get_user_by_id(db: DBSession, id_user: int) -> User | None:
    stmt = select(User).where(User.id == id_user)
    exist = await db.execute(stmt)

    return exist.scalar_one_or_none()


async def update_data(
    db: DBSession, user: CurrentUser, update: UserUpdate
) -> User:

    try:
        user.email = update.email
        user.password = auth_repo.hash_password(update.password)

        await db.commit()
        await db.refresh(user)

        return user

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'{e}')
    except OperationalError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'{e}')
    except InvalidRequestError as e:
        raise HTTPException(status_code=500, detail=f'{e}')
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f'{e}')


async def delete_user(db: DBSession, r: rediscon, user: CurrentUser):
    try:
        await db.delete(user)
        await db.commit()
    except OperationalError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f'{e}')
    except InvalidRequestError as e:
        await db.rollback()
        raise HTTPException(status_code=409, detail=f'{e}')


async def cache_user(
    db: DBSession, r: rediscon, id_user: int
) -> UserPublic | None:

    cache_key = f'user:{id_user}'
    user_cached = await r.get(cache_key)

    if user_cached:
        return UserPublic.model_validate_json(user_cached)

    user_obj = await get_user_by_id(db, id_user)

    if user_obj:
        user_schema = UserPublic.model_validate(user_obj)

        await r.set(cache_key, user_schema.model_dump_json(), ex=600)

        return user_schema

    return None


async def cache_delete(r: rediscon, id_user: int) -> str | None:
    cache_key = f'user:{id_user}'
    user_cached = await r.exists(cache_key)

    if not user_cached:
        return None

    await r.delete(cache_key)

    return 'Cache deletado!'
