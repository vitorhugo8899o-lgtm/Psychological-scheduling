from app.api.v1.dependencies import  completion
from app.groq.faq_service import search_predefined_answer
from app.schemas.custom_schema import MessagePrompt
from fastapi import HTTPException



async def send_message(client, context_user: str, context_system: str):
    result = search_predefined_answer(context_user)

    if result['found']:
        return {
            'source': 'faq',
            'response': result['response']
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
            
    return {
        'source': 'ai',
        'response': response_completed
    }
