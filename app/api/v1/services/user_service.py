from app.models.users_models import User
from app.api.v1.dependencies import DBSession
from app.schemas.user_schema import UserCreate

from app.api.v1.repositories import user_repo
from fastapi import HTTPException


async def create_user_service(db:DBSession,user_data:UserCreate) -> User: 
    existing = await user_repo.get_user_by_email(db, user_data.email)

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Esse endereço de Email já está em uso!"
        )
    
    return await user_repo.new_user(db,user_data)