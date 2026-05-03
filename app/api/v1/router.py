from fastapi import APIRouter

from app.api.v1.endpoints import administrator, users

api_router = APIRouter()

api_router.include_router(users.user_route, tags=['Users'])
api_router.include_router(administrator.adm_router, tags=['Adms'])
