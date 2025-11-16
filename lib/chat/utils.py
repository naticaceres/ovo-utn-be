"""
Funciones de utilidad para el módulo de chat.

Este módulo contiene funciones auxiliares reutilizables
para procesamiento de texto, validación y parsing.
"""

import json
import re
from config import MAX_USER_INPUT_CHARS, HISTORY_PREFIX_SYSTEM, HISTORY_PREFIX_USER, HISTORY_PREFIX_ASSISTANT


def extract_final_scores_from_response(text):
    """
    Extrae un diccionario de puntajes desde una línea 'final_scores: key: val, key: val'.
    
    NOTA: Esta función parece ser legacy y no se usa actualmente.
    Se mantiene por compatibilidad.
    
    Args:
        text: Texto que puede contener final_scores
        
    Returns:
        dict: Diccionario con los scores o None si no se encuentra
    """
    if not text:
        return None
    match = re.search(r"final_scores\s*:\s*(.*)", text, flags=re.IGNORECASE)
    if not match:
        return None
    payload = match.group(1)
    results = {}
    for part in payload.split(','):
        key_val = part.strip()
        if not key_val:
            continue
        m = re.match(r"([^:]+)\s*:\s*([-+]?\d*\.\d+|\d+)", key_val)
        if m:
            key = m.group(1).strip()
            try:
                val = float(m.group(2))
            except ValueError:
                continue
            results[key] = val
    return results if results else None


def clean_chatbot_response(text):
    """
    Elimina cualquier línea que contenga 'final_scores' y devuelve el resto limpio.
    
    NOTA: Esta función parece ser legacy y no se usa actualmente.
    Se mantiene por compatibilidad.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        str: Texto limpio sin líneas de final_scores
    """
    if text is None:
        return ''
    lines = text.splitlines()
    filtered = [ln for ln in lines if 'final_scores' not in ln.lower()]
    return "\n".join(filtered).strip()


def validate_request(body):
    """
    Valida los parámetros de la request HTTP.
    
    Args:
        body: Diccionario con el body de la request
        
    Returns:
        tuple: (user_id, prompt, chat_id) si es válido, o (None, error_response) si hay error
    """
    from response_builder import build_error_response
    
    user_id = body.get('UserID')
    chat_id = body.get('ChatID')
    prompt = body.get('prompt')
    
    if not chat_id:
        return None, build_error_response(
            400,
            'Faltan parámetros: ChatID es obligatorio.'
        )
    
    user_id = user_id if user_id else 'ANONYMOUS_USER'
    
    if isinstance(prompt, str) and len(prompt) > MAX_USER_INPUT_CHARS:
        return None, build_error_response(
            400,
            f'La respuesta excede el máximo de {MAX_USER_INPUT_CHARS} caracteres.'
        )
    
    return (user_id, prompt, chat_id), None


def get_last_assistant_message(history):
    """
    Obtiene el último mensaje del asistente del historial.
    
    Args:
        history: Lista de strings con el historial del chat
        
    Returns:
        str: Último mensaje del asistente o string vacío si no hay
    """
    for line in reversed(history):
        if line.startswith(HISTORY_PREFIX_ASSISTANT):
            # Extraer el texto después del prefijo
            return line[len(HISTORY_PREFIX_ASSISTANT):].strip()
    return ""


def extract_question_number_from_response(response_text, total_questions):
    """
    Extrae el número de pregunta de la respuesta del chatbot.
    
    El chatbot debe incluir el número en formato "Pregunta N de M:" o variaciones.
    Esta función busca patrones como:
    - "Pregunta 4 de 14:"
    - "Pregunta 4/14:"
    - "Pregunta 4 de 14"
    - etc.
    
    Args:
        response_text: Texto de la respuesta del chatbot
        total_questions: Total de preguntas (para validación)
        
    Returns:
        int: Número de pregunta extraído, o None si no se encuentra
    """
    if not response_text:
        return None
    
    # Patrones para buscar el número de pregunta
    patterns = [
        r'Pregunta\s+(\d+)\s+de\s+\d+',  # "Pregunta 4 de 14"
        r'Pregunta\s+(\d+)/\d+',  # "Pregunta 4/14"
        r'Pregunta\s+(\d+):',  # "Pregunta 4:"
        r'pregunta\s+(\d+)',  # "pregunta 4" (case insensitive)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            try:
                question_num = int(match.group(1))
                # Validar que esté en rango válido (1 a total_questions)
                # El chatbot maneja reformulaciones manteniendo el mismo número
                if 1 <= question_num <= total_questions:
                    return question_num
            except (ValueError, IndexError):
                continue
    
    return None

