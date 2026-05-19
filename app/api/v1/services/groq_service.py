from fastapi import HTTPException

from app.api.v1.dependencies import CurrentUser, completion, rediscon
from app.groq.faq_service import search_predefined_answer
from app.groq.groq_cache import cache_respost, create_cache_response


async def send_message(
    client,
    context_user: str,
    context_system: str,
    r: rediscon,
    user: CurrentUser
):
    if user.role != 'cliente':
        raise HTTPException(
            status_code="O usuário não tem permissão para realizar essa ação."
        )

    result = search_predefined_answer(context_user)

    if result['found']:
        return {
            'source': 'faq',
            'response': result['response']
        }

    cache_response = await cache_respost(context_user, r)

    if cache_response:
        return {
            'source': 'redis',
            'response': cache_response
        }

    chat_response = await completion(client, context_user, context_system)

    if not chat_response:
        raise HTTPException(
            status_code=409,
            detail="Erro ao mandar mensagem ao agente."
        )

    response_completed = ""
    for chunk in chat_response:
        if chunk.choices[0].delta.content:
            response_completed += chunk.choices[0].delta.content

    await create_cache_response(context_user, response_completed, r)

    return {
        'source': 'ai',
        'response': response_completed
    }
