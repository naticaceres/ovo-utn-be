"""
Construcción de respuestas HTTP para el API.

Este módulo se encarga de construir las respuestas HTTP consistentes
y manejar los headers CORS.
"""

import json
from config import CORS_HEADERS


def get_cors_headers():
    """
    Retorna los headers CORS estándar.
    
    Returns:
        dict: Headers CORS para respuestas HTTP
    """
    return CORS_HEADERS.copy()


def get_cors_headers_options():
    """
    Retorna headers CORS para respuestas OPTIONS (sin Content-Type).
    
    Returns:
        dict: Headers CORS para preflight requests
    """
    headers = CORS_HEADERS.copy()
    headers.pop("Content-Type", None)
    return headers


def get_history_to_return(history):
    """
    Quita el Master Prompt del historial para retornar al cliente.
    
    El historial completo incluye el system prompt como primer elemento,
    pero el cliente solo necesita ver la conversación real.
    
    Args:
        history: Lista completa del historial incluyendo system prompt
        
    Returns:
        list: Historial sin el system prompt
    """
    return history[1:]


def build_response(cleaned_response, chat_id, status, history, final_scores=None):
    """
    Construye la respuesta HTTP final para el cliente.
    
    Args:
        cleaned_response: Respuesta del chatbot (texto limpio)
        chat_id: ID del chat
        status: Estado del chat ('FINISHED', 'Waiting for N of M', etc.)
        history: Historial completo del chat
        final_scores: Diccionario con los scores finales (opcional)
        
    Returns:
        dict: Respuesta HTTP con statusCode, headers y body
    """
    response_data = {
        'chatbot_response': cleaned_response,
        'chat_id': chat_id,
        'status': status,
        'full_history': get_history_to_return(history)
    }
    
    if final_scores is not None:
        response_data['final_scores'] = final_scores
    
    return {
        'statusCode': 200,
        'headers': get_cors_headers(),
        'body': json.dumps(response_data)
    }


def build_error_response(status_code, error_message, detail=None):
    """
    Construye una respuesta de error HTTP.
    
    Args:
        status_code: Código HTTP de error (400, 429, 500, etc.)
        error_message: Mensaje de error para el cliente
        detail: Detalle adicional del error (opcional)
        
    Returns:
        dict: Respuesta HTTP de error
    """
    body_data = {'error': error_message}
    if detail:
        body_data['detail'] = detail
    
    return {
        'statusCode': status_code,
        'headers': get_cors_headers(),
        'body': json.dumps(body_data)
    }

