import asyncio
import hashlib
import logging

from fastapi import HTTPException
from groq import APIError

from app.api.v1.dependencies import CurrentUser, completion, rediscon
from app.groq.ai_safety import (
    CRISIS_REPLY,
    is_crisis_message,
    normalize_message,
    sanitize_model_output,
)
from app.groq.faq_service import search_predefined_answer
from app.groq.groq_cache import cache_respost, create_cache_response
from app.schemas.custom_schema import UserRole


def _user_ref(user: CurrentUser) -> str:
    return hashlib.sha256(f'mira-user:{user.id}'.encode()).hexdigest()[:24]


async def send_message(
    client, context_user: str, context_system: str, r: rediscon, user: CurrentUser
):
    if user.role != UserRole.client:
        raise HTTPException(
            status_code=403,
            detail='O usuário não tem permissão para realizar essa ação.',
        )

    message = normalize_message(context_user)

    if not message:
        raise HTTPException(status_code=422, detail='Digite uma mensagem válida.')

    # Segurança do paciente vem ANTES de FAQ, cache e IA, e não depende do modelo.
    if is_crisis_message(message):
        return {'source': 'safety', 'response': CRISIS_REPLY}

    result = search_predefined_answer(message)

    if result['found']:
        return {'source': 'faq', 'response': result['response']}

    cache_response = await cache_respost(message, r)

    if cache_response:
        return {'source': 'redis', 'response': cache_response}

    try:
        chat_response = await completion(
            client, message, context_system, user_ref=_user_ref(user)
        )
    except APIError, asyncio.TimeoutError:
        # O erro bruto do provedor (URL, request-id, trechos de payload) fica no log.
        logging.exception('[IA] Falha ao consultar o provedor de IA')
        raise HTTPException(
            status_code=503,
            detail='O assistente está indisponível no momento. Tente novamente.',
        )

    if not chat_response or not chat_response.choices:
        raise HTTPException(
            status_code=409, detail='Erro ao mandar mensagem ao agente.'
        )

    reply = sanitize_model_output(chat_response.choices[0].message.content)

    if reply.cacheable:
        await create_cache_response(message, reply.text, r)

    return {'source': 'ai', 'response': reply.text}
