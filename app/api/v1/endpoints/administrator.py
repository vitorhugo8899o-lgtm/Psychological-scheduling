from http import HTTPStatus

from fastapi import APIRouter

from app.api.v1.dependencies import CurrentUser, DBSession
from app.api.v1.services import adm_service
from app.schemas.psychologist_schema import (
    PsychologistCreate,
    PsychologistPublic,
)

adm_router = APIRouter()


@adm_router.post(
        '/psychologist', status_code=HTTPStatus.CREATED,
        response_model=PsychologistPublic
)
async def create_psychologist(
    db: DBSession, user: CurrentUser, psych: PsychologistCreate
):
    return await adm_service.create_psychologist_service(db, user, psych)
