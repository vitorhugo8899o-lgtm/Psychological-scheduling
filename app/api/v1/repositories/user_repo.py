import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.api.v1.repositories import auth_repo
from app.api.v1.util.util import CacheManager
from app.models.appointments_models import Appointment
from app.models.users_models import User
from app.schemas.custom_schema import AppointmentStatus
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate

if TYPE_CHECKING:
    from app.api.v1.dependencies import CurrentUser, DBSession, rediscon


user_cache_manager = CacheManager(model_class=UserPublic, prefix='user', ttl=600)


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
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail='Esse endereço de Email já está em uso!'
        )
    except Exception:
        await db.rollback()
        # O detalhe técnico (SQL, parâmetros, hash) vai só para o log/Sentry.
        logging.exception('[Users] Falha inesperada ao criar usuário')
        raise HTTPException(
            status_code=500, detail='Erro inesperado ao criar o usuário.'
        )


async def get_user_by_email(db: DBSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    exist = await db.execute(stmt)

    return exist.scalar_one_or_none()


async def get_user_by_id(db: DBSession, id_user: int) -> User | None:
    stmt = select(User).where(User.id == id_user)
    exist = await db.execute(stmt)

    return exist.scalar_one_or_none()


async def update_data(db: DBSession, user: CurrentUser, update: UserUpdate) -> User:

    try:
        user.email = update.email
        user.password = auth_repo.hash_password(update.password)
        # Invalida todos os tokens emitidos antes da troca de e-mail/senha.
        user.token_version += 1

        await db.commit()
        await db.refresh(user)

        return user

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail='Esse endereço de Email já está em uso!'
        )
    except Exception:
        await db.rollback()
        logging.exception('[Users] Falha inesperada ao atualizar usuário %s', user.id)
        raise HTTPException(
            status_code=500, detail='Não foi possível atualizar os dados.'
        )


async def desactive_user(db: DBSession, user: CurrentUser):
    user.is_active = False
    user.token_version += 1
    await db.commit()


async def get_all_users(db: DBSession):
    stmt = select(User).limit(100).order_by(User.id)

    result = await db.execute(stmt)

    return result.scalars().all()


async def cache_user(db: DBSession, r: rediscon, id_user: int) -> UserPublic | None:
    user_cache = await user_cache_manager.get_or_set(
        r=r, identifier=id_user, db_fallback=lambda: get_user_by_id(db, id_user)
    )

    return user_cache


async def cache_delete(r: rediscon, id_user: int) -> str | None:
    user_cache = await user_cache_manager.delete_cache(r=r, identifier=id_user)

    return user_cache


async def user_next_appoiments(db: DBSession, user: CurrentUser):
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.psychologist), joinedload(Appointment.service))
        .where(
            Appointment.id_client == user.id,
            Appointment.status == AppointmentStatus.confirmed,
            Appointment.date_time >= datetime.now(UTC),
        )
        .order_by(Appointment.date_time)
    ).limit(3)

    result = await db.execute(stmt)

    return result.scalars().all()


async def open_appoiments(db: DBSession, user: CurrentUser):
    stmt = (
        select(Appointment)
        .options(joinedload(Appointment.psychologist), joinedload(Appointment.service))
        .where(
            Appointment.id_client == user.id,
            Appointment.status == AppointmentStatus.pending,
            Appointment.date_time >= datetime.now(UTC),
        )
        .order_by(Appointment.date_time)
    )

    result = await db.execute(stmt)

    return result.scalars().all()
