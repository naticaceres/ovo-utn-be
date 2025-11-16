"""
Servicio de acceso a DynamoDB para el módulo de chat.

Este módulo encapsula toda la lógica de acceso a DynamoDB,
incluyendo lectura de aptitudes, gestión del estado del chat
y persistencia del progreso.
"""

from config import (
    dynamodb, 
    APTITUDES_TABLE_NAME, 
    PROGRESS_TABLE_NAME, 
    MAX_QUESTIONS
)
from prompt_builder import build_dynamic_master_prompt


def get_aptitudes_from_table():
    """
    Lee todas las aptitudes activas de la tabla AptitudesTable.
    
    Returns:
        list: Lista de strings con los nombres de las aptitudes activas
        
    Raises:
        Exception: Si hay error al acceder a la tabla
    """
    try:
        print(f"DEBUG: Accediendo a tabla {APTITUDES_TABLE_NAME} en región {dynamodb.meta.client.meta.region_name}")
        aptitudes_table = dynamodb.Table(APTITUDES_TABLE_NAME)
        response = aptitudes_table.scan(
            FilterExpression='activa = :activa',
            ExpressionAttributeValues={':activa': True}
        )
        aptitudes = [item['aptitud'] for item in response['Items']]
        print(f"DEBUG: Aptitudes encontradas: {aptitudes}")
        return aptitudes
    except Exception as e:
        print(f"DEBUG: Error al obtener aptitudes: {e}")
        raise


def get_chat_state(progress_table, chat_id):
    """
    Obtiene el estado actual del chat desde DynamoDB.
    
    Si el chat no existe, crea un nuevo estado inicial con el prompt maestro.
    
    Args:
        progress_table: Tabla de DynamoDB para progreso
        chat_id: ID del chat
        
    Returns:
        tuple: (history, next_question, is_finished, final_scores, total_questions, is_new_chat)
        
    Raises:
        Exception: Si no se pueden obtener las aptitudes para iniciar el cuestionario
    """
    progress_response = progress_table.get_item(Key={'ChatID': chat_id})
    
    if 'Item' not in progress_response:
        # Chat nuevo: crear estado inicial
        try:
            aptitudes = get_aptitudes_from_table()
            if not aptitudes:
                raise Exception("No hay aptitudes disponibles en la tabla")
            # Limitar la cantidad de preguntas a MAX_QUESTIONS
            limited_aptitudes = aptitudes[:MAX_QUESTIONS]
            dynamic_master_prompt = build_dynamic_master_prompt(limited_aptitudes)
            total_questions = len(limited_aptitudes)
            return [f"System: {dynamic_master_prompt}"], 1, False, None, total_questions, True
        except Exception as e:
            print(f"Error al obtener aptitudes: {e}")
            raise Exception("No se pueden obtener las aptitudes para iniciar el cuestionario")
    
    # Chat existente: recuperar estado
    item = progress_response['Item']
    current_status = item.get('Status', 'IN_PROGRESS')
    history = item.get('History', [])
    next_question = int(item.get('QuestionNumber', 1))
    final_scores = item.get('FinalScores', None)
    
    # Intentar recuperar cantidad total de preguntas persistida
    total_questions = int(item.get('TotalQuestions', 0)) if item.get('TotalQuestions') is not None else 0
    if total_questions <= 0:
        # Fallback: recalcular desde la tabla (cap MAX_QUESTIONS). Esto evita romper chats antiguos
        try:
            aptitudes = get_aptitudes_from_table()
            total_questions = len(aptitudes[:MAX_QUESTIONS]) if aptitudes else 5
        except Exception:
            total_questions = 5
    
    return history, next_question, current_status == 'FINISHED', final_scores, total_questions, False


def save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores, total_questions):
    """
    Guarda el progreso del chat en DynamoDB.
    
    Args:
        progress_table: Tabla de DynamoDB para progreso
        chat_id: ID del chat
        user_id: ID del usuario
        history: Historial completo del chat
        is_finished: Si el chat está finalizado
        next_question: Número de la siguiente pregunta
        final_scores: Diccionario con scores finales (opcional)
        total_questions: Total de preguntas del cuestionario
        
    Returns:
        str: Estado del chat ('FINISHED' o 'Waiting for N of M')
    """
    if is_finished:
        # Convertir final_scores a strings para evitar problemas de serialización
        final_scores_as_strings = {}
        if final_scores:
            for key, value in final_scores.items():
                final_scores_as_strings[key] = str(value)
        
        progress_table.put_item(
            Item={
                'ChatID': chat_id,
                'UserID': user_id,
                'QuestionNumber': total_questions + 1,
                'History': history,
                'Status': 'FINISHED',
                'FinalScores': final_scores_as_strings,
                'TotalQuestions': total_questions
            }
        )
        return 'FINISHED'
    else:
        # Usar el número de pregunta recibido directamente (viene del chatbot)
        # Esto permite manejar reformulaciones correctamente (mismo número)
        progress_table.put_item(
            Item={
                'ChatID': chat_id,
                'UserID': user_id,
                'QuestionNumber': next_question,
                'History': history,
                'Status': 'IN_PROGRESS',
                'TotalQuestions': total_questions
            }
        )
        return f'Waiting for {next_question} of {total_questions}'

