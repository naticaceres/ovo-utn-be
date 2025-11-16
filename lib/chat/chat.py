"""
Handler principal de Lambda para el endpoint de chat vocacional.

Este módulo orquesta el flujo completo del cuestionario vocacional:
- Validación de requests
- Gestión de estado del chat
- Verificación de cuotas
- Invocación a Bedrock
- Persistencia del progreso
"""

import json
from datetime import date

# Imports de configuración
from config import (
    PROGRESS_TABLE_NAME,
    dynamodb
)

# Imports de servicios
from quota_service import (
    get_quota_table,
    check_quotas,
    revert_global_quota
)
from dynamodb_service import (
    get_chat_state,
    save_chat_progress
)
from bedrock_client import (
    build_messages_from_history,
    call_bedrock
)
from response_builder import (
    build_response,
    build_error_response,
    get_cors_headers_options
)
from utils import (
    validate_request,
    get_last_assistant_message
)


def handler(event, context):
    """
    Función principal de la Lambda.
    
    Maneja el flujo completo del cuestionario vocacional:
    1. Valida la request
    2. Obtiene/crea el estado del chat
    3. Verifica cuotas
    4. Invoca Bedrock si es necesario
    5. Persiste el progreso
    6. Retorna la respuesta
    
    Args:
        event: Evento de API Gateway
        context: Contexto de Lambda
        
    Returns:
        dict: Respuesta HTTP con statusCode, headers y body
    """
    # Manejar solicitudes OPTIONS para CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_cors_headers_options(),
            'body': ''
        }
    
    today_date = date.today().isoformat()
    quota_table = get_quota_table()
    progress_table = dynamodb.Table(PROGRESS_TABLE_NAME)

    try:
        # Validar request
        request_data, error_response = validate_request(json.loads(event.get('body', '{}')))
        if error_response:
            return error_response
        
        user_id, prompt, chat_id = request_data

        # Obtener estado del chat (antes de cuotas para poder manejar recupero sin consumir cuota)
        history, next_question, is_finished, saved_final_scores, total_questions, is_new_chat = get_chat_state(
            progress_table, chat_id
        )
        
        # Si el test ya terminó, retornar historial con final_scores
        if is_finished:
            revert_global_quota(quota_table, today_date)
            return build_response(
                "Test finalizado. Aquí está el historial completo.",
                chat_id, 'FINISHED', history, saved_final_scores
            )
        
        # Si es un chat en progreso y no se recibió prompt, devolver historial sin avanzar
        # (sin consumir cuota ni llamar a Bedrock)
        if not is_new_chat and (prompt is None or (isinstance(prompt, str) and prompt.strip() == "")):
            pending_question = get_last_assistant_message(history)
            return build_response(
                pending_question,
                chat_id,
                f'Waiting for {next_question} of {total_questions}',
                history
            )

        # Agregar respuesta del usuario al historial
        if next_question > 1 and isinstance(prompt, str) and prompt.strip() != "":
            history.append(f"Usuario: {prompt}")
        
        # Verificar cuotas (solo cuando vamos a invocar a Bedrock)
        quota_error = check_quotas(quota_table, user_id, today_date)
        if quota_error:
            return quota_error
        
        # Construir mensajes y llamar Bedrock
        messages_list = build_messages_from_history(history)
        
        # Verificar si esta es la última pregunta
        # Si next_question >= total_questions, el usuario acaba de responder la última pregunta
        is_final_question = next_question >= total_questions
        
        if is_final_question:
            # Llamar a Bedrock con structured output para obtener final_scores
            # Referencia: AWS Bedrock Structured Outputs
            # https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-structured-outputs.html
            conclusion, aptitudes_scores = call_bedrock(
                messages_list, 
                is_final_analysis=True
            )
            final_scores = aptitudes_scores
            is_finished = True
            cleaned_response = ""  # No agregamos mensaje del asistente, solo finalizamos
            
            # Guardar progreso como FINISHED con final_scores
            status = save_chat_progress(
                progress_table, chat_id, user_id, history, 
                is_finished, next_question, final_scores, total_questions
            )
            
            # Retornar respuesta con historial y final_scores
            return build_response(cleaned_response, chat_id, status, history, final_scores)
        else:
            # Generar la siguiente pregunta normalmente
            chatbot_response, _ = call_bedrock(
                messages_list, 
                is_final_analysis=False
            )
            cleaned_response = chatbot_response
            final_scores = None
            is_finished = False
            
            history.append(f"Asistente: {cleaned_response}")
            
            # Guardar progreso
            status = save_chat_progress(
                progress_table, chat_id, user_id, history, 
                is_finished, next_question, final_scores, total_questions
            )
            
            # Construir y retornar respuesta
            return build_response(cleaned_response, chat_id, status, history, final_scores)

    except Exception as e:
        print(f"Error en Lambda: {e}")
        
        # Revertir cuota global si no fue un error de cuota
        if 'Quota Exceeded' not in str(e):
            revert_global_quota(quota_table, today_date)
        
        return build_error_response(
            500,
            'Error interno del servidor',
            str(e)
        )
