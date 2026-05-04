from typing import List

from fastapi import HTTPException
from sqlalchemy import select

from app.api.v1.dependencies import CurrentUser, DBSession, rediscon
from app.api.v1.repositories import service_repo, user_repo
from app.models.users_models import User
from app.schemas.service_schema import ServiceQuery
from app.schemas.user_schema import UserCreate, UserPublic, UserUpdate


async def create_user_service(db: DBSession, user_data: UserCreate) -> User:
    existing = await user_repo.get_user_by_email(db, user_data.email)

    if existing:
        raise HTTPException(
            status_code=409, detail='Esse endereço de Email já está em uso!'
        )

    return await user_repo.new_user(db, user_data)


async def get_users(db: DBSession, user: CurrentUser) -> List[UserPublic]:
    if user.role != 'adm':
        raise HTTPException(
            status_code=403,
            detail='Usuário não tem permissão para realizar essa ação.',
        )

    stmt = select(User).limit(100).order_by(User.id)

    result = await db.execute(stmt)

    return result.scalars().all()


async def get_user(
    db: DBSession, r: rediscon, user: CurrentUser, id_user: int
) -> UserPublic:
    if user.role == 'cliente':
        raise HTTPException(
            status_code=403,
            detail='Usuário não tem permissão para realizar essa ação',
        )

    user_cache = await user_repo.cache_user(db, r, id_user)

    if not user_cache:
        raise HTTPException(
            status_code=404,
            detail='Usuário não encontrado. Verifique se digitou o id correto!'
        )

    return user_cache


async def update_user_data(
    db: DBSession, r: rediscon, user: CurrentUser, uptade: UserUpdate
):
    email_exist = await user_repo.get_user_by_email(db, uptade.email)

    if email_exist and email_exist.id != user.id:
        raise HTTPException(
            status_code=409, detail='Esse endereço de Email já está em uso!'
        )

    await user_repo.update_data(db, user, uptade)

    await user_repo.cache_delete(r, user.id)

    user_cache = await user_repo.cache_user(db, r, user.id)

    return user_cache


async def delete_user(db: DBSession, user: CurrentUser, r: rediscon):
    await user_repo.delete_user(db, r, user)
    await user_repo.cache_delete(r, user.id)


async def get_services(db: DBSession):
    services = await service_repo.get_services(db)

    if not services:
        return 'Nenhum serviço encontrado.'

    return services


async def get_service(db: DBSession, r: rediscon, service_id: int):
    service = await service_repo.cache_service(db, r, service_id)
    if not service:
        raise HTTPException(status_code=404, detail='Serviço não encontrado.')

    return service


async def get_service_customized(db: DBSession, filter: ServiceQuery):
    service = await service_repo.filter_services(db, filter)

    if not service:
        raise HTTPException(
            status_code=404, detail='Nenhum serviço encontrado!'
        )

    return service
