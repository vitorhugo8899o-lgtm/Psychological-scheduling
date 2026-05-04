from fastapi import APIRouter

from app.api.v1.endpoints import administrator, psychologist, services, users

api_router = APIRouter()

api_router.include_router(users.user_route, tags=['Users'])
api_router.include_router(administrator.adm_router, tags=['Adms'])
api_router.include_router(psychologist.psych_router, tags=['Psych'])
api_router.include_router(services.service_route, tags=['Services'])
