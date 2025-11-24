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
    save_chat_progress,
    get_aptitudes_from_table
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
    get_last_assistant_message,
    extract_question_number_from_response
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
        # Incluir la respuesta si hay prompt y no es un chat nuevo sin respuesta
        if isinstance(prompt, str) and prompt.strip() != "":
            history.append(f"Usuario: {prompt}")
        
        # Verificar cuotas (solo cuando vamos a invocar a Bedrock)
        quota_error = check_quotas(quota_table, user_id, today_date)
        if quota_error:
            return quota_error
        
        # Construir mensajes y llamar Bedrock
        messages_list = build_messages_from_history(history)
        
        # Verificar si el usuario acaba de responder la última pregunta
        # Si next_question >= total_questions, el usuario ya respondió todas las preguntas
        # y necesitamos generar el análisis final (no otra pregunta)
        is_final_question = next_question >= total_questions
        
        if is_final_question:
            # Obtener aptitudes de la DB para construir el schema con nombres exactos
            # Esto asegura que los final_scores usen los nombres exactos de la DB
            # total_questions ya está establecido desde el inicio del chat y es igual al número de aptitudes
            aptitudes = get_aptitudes_from_table()
            
            # Agregar mensaje explícito al historial temporalmente para reforzar la evaluación
            # Esto ayuda al LLM a entender que debe revisar todas las respuestas y evaluar cada aptitud
            # NOTA: Este mensaje NO se agrega al historial persistido, solo se usa para construir messages_list
            evaluation_instruction = (
                "System: Ahora debes generar el análisis final. "
                "REVISA TODO EL HISTORIAL de respuestas del usuario. "
                "Para cada aptitud, busca la respuesta correspondiente del usuario y evalúa el nivel de evidencia (1-10). "
                "NO uses el mismo puntaje para todas. Los puntajes deben reflejar las diferencias reales en las respuestas. "
                "Si el usuario fue positivo sobre una aptitud (ej: 'me gusta', 'me encanta', 'bastante bien') asigna 7-10. "
                "Si fue negativo (ej: 'no me gusta', 'no es lo mío', 'mal') asigna 1-3. "
                "Si fue neutro (ej: 'ok', 'regular') asigna 4-6. "
                "Evalúa cada aptitud INDEPENDIENTEMENTE según la respuesta específica del usuario."
            )
            # Construir historial temporal con la instrucción (no se persiste)
            temp_history = history + [evaluation_instruction]
            messages_list = build_messages_from_history(temp_history)
            
            # Llamar a Bedrock con structured output para obtener final_scores
            # Referencia: AWS Bedrock Structured Outputs
            # https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-structured-outputs.html
            conclusion, aptitudes_scores = call_bedrock(
                messages_list, 
                is_final_analysis=True,
                aptitudes=aptitudes
            )
            final_scores = aptitudes_scores
            is_finished = True
            cleaned_response = ""  # No agregamos mensaje del asistente, solo finalizamos
            
            # Guardar progreso como FINISHED con final_scores
            # Usar history original (sin el mensaje de instrucción interna)
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
            # Limpiar texto adicional no deseado como medida de seguridad adicional
            # (la prevención principal viene de stop sequences y prompt)
            from utils import clean_response_trailing_text
            cleaned_response = clean_response_trailing_text(chatbot_response)
            final_scores = None  # No hay final_scores en preguntas intermedias
            is_finished = False
            
            # Extraer el número de pregunta de la respuesta del chatbot
            # El chatbot controla el conteo y debe incluir "Pregunta N de M:" en su respuesta
            # Esto permite manejar correctamente las reformulaciones (mismo número)
            extracted_question_num = extract_question_number_from_response(cleaned_response, total_questions)
            
            if extracted_question_num is not None:
                # Usar el número extraído de la respuesta del chatbot
                # Esto asegura sincronización: el chatbot es la fuente de verdad
                next_question = extracted_question_num
            else:
                # Fallback: si no se puede extraer, incrementar manualmente
                # Esto puede pasar si el chatbot no incluye el formato esperado
                next_question = next_question + 1
                print(f"WARNING: No se pudo extraer número de pregunta de la respuesta. Usando fallback: {next_question}")
            
            history.append(f"Asistente: {cleaned_response}")
            
            # Guardar progreso con el número de pregunta extraído (fuente de verdad del chatbot)
            # Esto asegura que no haya desincronización para detectar correctamente el análisis final
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
