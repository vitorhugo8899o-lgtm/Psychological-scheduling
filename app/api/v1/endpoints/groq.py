from http import HTTPStatus

from fastapi import APIRouter, Request

from app.api.v1.dependencies import PROMPT_SYSTEM, CurrentUser, client, rediscon
from app.api.v1.services.groq_service import send_message
from app.redis.limiter import limiter
from app.schemas.custom_schema import MessagePrompt

groq_route = APIRouter()


@groq_route.post('/chat-user', status_code=HTTPStatus.OK)
@limiter.limit('3/minute')
async def chat_user(
    request: Request, user: CurrentUser, user_message: MessagePrompt, r: rediscon
):
    return await send_message(client, user_message.message, PROMPT_SYSTEM, r, user)
