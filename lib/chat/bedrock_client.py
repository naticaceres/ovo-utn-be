"""
Cliente para integración con AWS Bedrock.

Este módulo encapsula toda la lógica de comunicación con Bedrock,
incluyendo la construcción del payload e invocación del modelo.

El control de la generación se realiza mediante:
- Configuración de inference parameters (stopSequences, maxTokens, temperature, topP)
- System prompt cuidadosamente diseñado

Referencia: AWS Bedrock Inference Parameters
https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
"""

import json
from config import (
    bedrock, 
    BEDROCK_MODEL_ID,
    HISTORY_PREFIX_SYSTEM,
    HISTORY_PREFIX_USER,
    HISTORY_PREFIX_ASSISTANT
)
from prompt_builder import get_final_analysis_schema


def build_messages_from_history(history):
    """
    Construye la lista de mensajes para Bedrock desde el historial.
    El system prompt se incluye como el primer mensaje en el array.
    
    Referencia: AWS Bedrock Messages API Format
    https://docs.aws.amazon.com/bedrock/latest/userguide/api-messages.html
    
    Args:
        history: Lista de strings con el historial del chat
        
    Returns:
        list: Lista de mensajes en formato Bedrock
    """
    messages_list = []
    
    for line in history:
        if line.startswith(HISTORY_PREFIX_SYSTEM):
            # El system prompt se incluye como primer mensaje de usuario
            system_prompt = line[len(HISTORY_PREFIX_SYSTEM):].strip()
            messages_list.append({
                "role": "user",
                "content": [{"text": system_prompt}]
            })
        elif line.startswith(HISTORY_PREFIX_USER):
            role = "user"
            text_content = line[len(HISTORY_PREFIX_USER):].strip()
            messages_list.append({
                "role": role,
                "content": [{"text": text_content}]
            })
        elif line.startswith(HISTORY_PREFIX_ASSISTANT):
            role = "assistant"
            text_content = line[len(HISTORY_PREFIX_ASSISTANT):].strip()
            messages_list.append({
                "role": role,
                "content": [{"text": text_content}]
            })
        else:
            continue
    
    return messages_list


def call_bedrock(messages_list, is_final_analysis=False):
    """
    Invoca el modelo de Bedrock con configuración optimizada.
    
    Referencia: AWS Bedrock Runtime API - InvokeModel
    https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html
    
    Args:
        messages_list: Lista de mensajes en formato Bedrock (el system prompt ya está incluido como primer mensaje)
        system_prompt: Parámetro obsoleto, mantenido por compatibilidad (ignorado)
        is_final_analysis: Si es True, usa structured output para análisis final
        
    Returns:
        tuple: (text_response, final_scores_dict) o (text_response, None)
        
    Raises:
        Exception: Si el structured output no se genera correctamente
    """
    # Construir payload base según formato original que funcionaba
    # El modelo Nova no requiere schemaVersion ni campo system separado
    payload = {
        "messages": messages_list,
        "inferenceConfig": {
            # maxTokens reducido a 200 como en la versión original que funcionaba
            # Referencia: AWS Bedrock Inference Parameters - maxTokens
            # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
            "maxTokens": 200,
            # Temperature bajo para respuestas más deterministas y consistentes
            # Referencia: AWS Bedrock Inference Parameters - Temperature
            # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
            "temperature": 0.1,
            # topP para controlar diversidad de tokens considerados
            # Referencia: AWS Bedrock Inference Parameters - Top P
            # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
            "topP": 0.9,
            # Stop sequences según versión original que funcionaba
            # Referencia: AWS Bedrock Inference Parameters - stopSequences
            # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
            "stopSequences": [
                "Usuario:",
                "Asistente:",
                "\n\n**Pregunta",
                "\nPregunta ",
                "Una vez finalizada",
                "Procederé a generar"
            ]
        }
    }
    
    # Bedrock requiere al menos un mensaje en el array messages
    # Si messages_list está vacío (chat nuevo), agregar un mensaje de usuario mínimo
    if not messages_list:
        payload["messages"] = [{
            "role": "user",
            "content": [{"text": "Inicia el cuestionario vocacional."}]
        }]
    
    # Usar structured output para análisis final
    if is_final_analysis:
        payload["toolConfig"] = {
            "toolChoice": {"tool": {"name": "final_analysis"}},
            "tools": [{
                "toolSpec": {
                    "name": "final_analysis",
                    "description": "Análisis final de orientación vocacional",
                    "inputSchema": {
                        "json": get_final_analysis_schema()
                    }
                }
            }]
        }
    
    # Logging del payload para debugging (sin el contenido completo de mensajes para no saturar logs)
    payload_for_logging = {
        "messages_count": len(payload["messages"]),
        "first_message_role": payload["messages"][0]["role"] if payload["messages"] else None,
        "first_message_preview": payload["messages"][0]["content"][0]["text"][:100] + "..." if payload["messages"] and payload["messages"][0]["content"] else None,
        "inferenceConfig": payload["inferenceConfig"],
        "has_toolConfig": "toolConfig" in payload
    }
    print(f"DEBUG: Bedrock payload structure: {json.dumps(payload_for_logging, indent=2)}")
    
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(payload),
        accept='application/json',
        contentType='application/json'
    )
    
    response_body = json.loads(response.get('body').read())
    
    if is_final_analysis and 'output' in response_body and 'message' in response_body['output']:
        # Extraer datos estructurados del tool use
        # Referencia: AWS Bedrock Structured Outputs - Tool Use Response Format
        # https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-structured-outputs.html
        message = response_body['output']['message']
        if 'content' in message:
            for content in message['content']:
                if content.get('toolUse'):
                    tool_input = content['toolUse']['input']
                    # Retornar solo aptitudes_scores (que son los final_scores)
                    # No retornamos conclusion ya que no se necesita mensaje visible
                    return '', tool_input.get('aptitudes_scores', {})
        
        # Si llegamos aquí, el structured output no se generó correctamente
        raise Exception("No se pudo obtener structured output del análisis final. La respuesta no contiene toolUse.")
    
    # Extraer texto de la respuesta (solo para preguntas normales, no análisis final)
    # El control de generación se realiza mediante stopSequences y el prompt,
    # no mediante post-procesamiento, para evitar truncar respuestas incompletas
    raw_response = response_body['output']['message']['content'][0]['text'].strip()
    
    return raw_response, None

