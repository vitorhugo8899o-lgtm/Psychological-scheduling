from fastapi import HTTPException
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.api.v1.repositories import user_repo
from app.models.users_models import User
from app.schemas.user_schema import UserCreate
from app.api.v1.dependencies import CurrentUser

async def create_user_service(db: DBSession, user_data: UserCreate) -> User:
    existing = await user_repo.get_user_by_email(db, user_data.email)

    if existing:
        raise HTTPException(
            status_code=409, detail='Esse endereço de Email já está em uso!'
        )

    return await user_repo.new_user(db, user_data)

async def get_users(db:DBSession, user:CurrentUser):
    if user.role != 'adm':
        raise HTTPException(
            status_code=403,
            detail="Usuário não tem permissão para realizar essa ação."
        )
    
    stmt = select(User).limit(100).order_by(User.id)

    result = await db.execute(stmt)

    return result.scalars().all()
