from fastapi import HTTPException
from sqlalchemy import select

from app.api.v1.dependencies import DBSession
from app.api.v1.repositories import auth_repo
from app.models.users_models import User
from app.schemas.user_schema import UserCreate


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
