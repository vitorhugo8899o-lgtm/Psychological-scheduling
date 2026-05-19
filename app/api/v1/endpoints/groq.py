from fastapi import APIRouter, Request
from http import HTTPStatus
from app.api.v1.dependencies import CurrentUser, client, PROMPT_SYSTEM, completion
from app.groq.faq_service import search_predefined_answer
from app.schemas.custom_schema import MessagePrompt
from app.api.v1.services.groq_service import send_message

groq_route = APIRouter()



@groq_route.post('/chat-user', status_code=HTTPStatus.OK)
async def chat_user(user:CurrentUser, user_message: MessagePrompt):
    return await send_message(client, user_message.message, PROMPT_SYSTEM)