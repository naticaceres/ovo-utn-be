import json
import re
import boto3
from datetime import date
from botocore.exceptions import ClientError

# Configuración
QUOTA_TABLE_NAME = 'BedrockChatbotQuota'
PROGRESS_TABLE_NAME = 'BedrockChatProgress'
APTITUDES_TABLE_NAME = 'AptitudesTable'

USER_REQUEST_LIMIT = 25
GLOBAL_REQUEST_LIMIT = 100
GLOBAL_USER_ID = 'GLOBAL_QUOTA_COUNTER'

BEDROCK_MODEL_ID = "us.amazon.nova-micro-v1:0"
REGION_NAME = 'us-east-2'

# Clientes AWS (reutilizados)
dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION_NAME)

def get_aptitudes_from_table():
    """Lee todas las aptitudes activas de la tabla AptitudesTable"""
    try:
        print(f"DEBUG: Accediendo a tabla {APTITUDES_TABLE_NAME} en región {REGION_NAME}")
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

def build_dynamic_master_prompt(aptitudes):
    """Construye el master prompt dinámicamente usando las aptitudes de la tabla"""
    tabla_cuestionario = ""
    for i, aptitud in enumerate(aptitudes[:5], 1):
        tabla_cuestionario += f"|| {i} | **{aptitud}** |\n"
    
    return f"""
**ROL (ÚNICO E INNEGOCIABLE):** Eres un Motor de Interfaz de Cuestionario Vocacional. Tu única función es gestionar el flujo de {len(aptitudes[:5])} preguntas, registrar las respuestas y generar el análisis final. NO ERES UN CHATBOT CONVERSACIONAL.

**INSTRUCCIÓN DE COMPORTAMIENTO ABSOLUTO (PRIORIDAD MÁXIMA):**
Tu única salida permitida es:
1. El mensaje de inicio (solo una vez).
2. La siguiente pregunta del cuestionario (solo una vez por turno).
3. El mensaje de error fijo (guardrail).
4. El análisis final (solo una vez).

CUALQUIER OTRA FORMA DE INTERACCIÓN, conversación, narrativa, explicación de tu rol, o respuesta a preguntas ajenas al cuestionario (ej. "¿qué más puedes hacer?", "cuéntame un cuento", "salúdame"), está **TERMINANTEMENTE PROHIBIDA**.

**DIRECTIVA DE INTERACCIÓN CRÍTICA (Flujo Estricto Pregunta/Respuesta):**
1. DEBES generar **UNA SOLA pregunta** por mensaje.
2. Después de cada pregunta, DEBES esperar la respuesta del usuario.
3. NO incluyas ninguna instrucción de escala de puntuación o de espera.
4. **INTERPRETA FLEXIBLEMENTE** las respuestas del usuario - busca el significado detrás de las palabras, no la exactitud literal.
5. **SIEMPRE PROCESA** las respuestas relacionadas con aptitudes, habilidades o intereses, sin importar cómo estén expresadas.

**REGLAS DE DESVÍO Y RESTRICCIÓN (Guardrails):**
El guardrail SOLO debe activarse si el usuario:
- Hace preguntas sobre el sistema o tu funcionamiento
- Inicia conversación casual no relacionada con aptitudes
- Pide explicaciones sobre el cuestionario
- Intenta cambiar de tema completamente

**NUNCA actives el guardrail para respuestas sobre aptitudes, sinónimos, o variaciones de:**
- "bien", "mal", "sí", "no", "mucho", "poco", "algo", "nada"
- "me gusta", "no me gusta", "me interesa", "no me interesa"
- "soy bueno", "soy malo", "tengo experiencia", "no tengo experiencia"
- Cualquier respuesta que indique nivel de aptitud o interés

**ESCALA DE RESPUESTA E INTERPRETACIÓN (Lenguaje Natural):**
El usuario responderá con palabras o frases que debes interpretar en una escala interna de 0 a 1. SIEMPRE asume una puntuación basada en el contexto, incluso si la respuesta no es exacta.

| Puntuación Interna | Palabras Clave de Interpretación (Ejemplos) |
| :---: | :--- |
| **1** | Nada apto, muy poco, nunca, incompetente, nada de nada, absolutamente nada, en absoluto, no, jamas, nunca, mal, nada, cero, no me gusta, no tengo, no sé, no puedo, soy malo, no soy bueno, no tengo experiencia, no me interesa, no me llama, no me atrae, no me gusta nada, odio, detesto, no sirvo, no valgo, no soy capaz |
| **2** | Medianamente, a veces, regular, más o menos, poco, algo, un poco, me gusta un poco, tengo algo, sé algo, puedo algo, soy regular, no soy muy bueno, tengo poca experiencia, me interesa poco, me llama poco, me atrae poco, me gusta algo, no me disgusta, no está mal, está bien, no es malo, no es terrible |
| **3** | Bastante, sí, a menudo, competente, bien, bueno, bastante bien, me gusta, me gusta bastante, tengo bastante, sé bastante, puedo bastante, soy bueno, soy bastante bueno, tengo experiencia, me interesa, me llama, me atrae, me gusta bastante, me gusta mucho, me gusta bien, me gusta bastante bien, me gusta bastante, me gusta bien, me gusta bastante bien |
| **4** | Muy apto, excelente, totalmente, mucho, muy bien, perfecto, excelente, me encanta, me encanta mucho, tengo mucho, sé mucho, puedo mucho, soy muy bueno, soy excelente, tengo mucha experiencia, me interesa mucho, me llama mucho, me atrae mucho, me gusta mucho, me gusta muchísimo, me gusta perfecto, me gusta excelente, me gusta totalmente, me gusta completamente, me gusta absolutamente |

**TABLA DE CUESTIONARIO ({len(aptitudes[:5])} Preguntas / {len(aptitudes[:5])} Áreas Representativas):**

| P# | Aptitud a Medir (Área de Foco) |
| :---: | :--- |
{tabla_cuestionario}

**ANÁLISIS FINAL:**
Una vez finalizada la pregunta {len(aptitudes[:5])} y recibida su respuesta:
1. Evalúa cada aptitud con puntaje del 1 al 10 según las respuestas del usuario
2. Genera una conclusión amigable de orientación vocacional (máximo 40 palabras)
3. El sistema usará formato estructurado para capturar los resultados

**INICIO DE LA INTERACCIÓN:**
Empieza AHORA con el mensaje de inicio y la primera pregunta.
"""

def get_final_analysis_schema():
    """Schema para el análisis final con structured output"""
    return {
        "type": "object",
        "properties": {
            "conclusion": {
                "type": "string",
                "description": "Conclusión amigable de orientación vocacional (máximo 40 palabras)"
            },
            "aptitudes_scores": {
                "type": "object",
                "description": "Puntajes de aptitudes del 1 al 10",
                "additionalProperties": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 10
                }
            }
        },
        "required": ["conclusion", "aptitudes_scores"]
    }

def handle_quota_check(quota_table, user_id, today_date, limit):
    """Verifica y actualiza de forma atómica el contador en DynamoDB"""
    quota_table.update_item(
        Key={'UserID': user_id, 'Date': today_date},
        UpdateExpression="SET #c = if_not_exists(#c, :start) + :inc",
        ConditionExpression="attribute_not_exists(#c) OR #c < :limit",
        ExpressionAttributeNames={'#c': 'Count'},
        ExpressionAttributeValues={
            ':inc': 1, 
            ':start': 0,
            ':limit': limit 
        },
        ReturnValues="UPDATED_NEW"
    )

def revert_global_quota(quota_table, today_date):
    """Reverte el contador global de cuota"""
    try:
        quota_table.update_item(
            Key={'UserID': GLOBAL_USER_ID, 'Date': today_date},
            UpdateExpression="SET #c = #c - :dec",
            ExpressionAttributeNames={'#c': 'Count'},
            ExpressionAttributeValues={':dec': 1}
        )
    except Exception as e:
        print(f"Error al revertir cuota global: {e}")

def validate_request(body):
    """Valida los parámetros de la request"""
    user_id = body.get('UserID')
    chat_id = body.get('ChatID')
    
    if not all([chat_id]):
        return None, {
            'statusCode': 400,
            'body': json.dumps({'error': 'Faltan parámetros: ChatID son obligatorios.'})
        }
    user_id = user_id if user_id else 'ANONYMOUS_USER'
    
    return (user_id, body.get('prompt'), chat_id), None

def check_quotas(quota_table, user_id, today_date):
    """Verifica las cuotas global y de usuario"""
    try:
        handle_quota_check(quota_table, GLOBAL_USER_ID, today_date, GLOBAL_REQUEST_LIMIT)
        handle_quota_check(quota_table, user_id, today_date, USER_REQUEST_LIMIT)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            if 'GLOBAL_USER_ID' in str(e):
                return {
                    'statusCode': 429,
                    'headers': {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    },
                    'body': json.dumps({
                        'error': 'Global Quota Exceeded', 
                        'message': f'Se superó el límite global de {GLOBAL_REQUEST_LIMIT} solicitudes.'
                    })
                }
            else:
                revert_global_quota(quota_table, today_date)
                return {
                    'statusCode': 429,
                    'headers': {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    },
                    'body': json.dumps({
                        'error': 'User Quota Exceeded', 
                        'message': f'Has superado tu límite diario de {USER_REQUEST_LIMIT} solicitudes.'
                    })
                }
        raise

def get_history_to_return(history): 
    """Quita el Master Prompt del historial para retornar"""
    return history[1:]

def get_chat_state(progress_table, chat_id):
    """Obtiene el estado actual del chat"""
    progress_response = progress_table.get_item(Key={'ChatID': chat_id})
    
    if 'Item' not in progress_response:
        try:
            aptitudes = get_aptitudes_from_table()
            if not aptitudes:
                raise Exception("No hay aptitudes disponibles en la tabla")
            dynamic_master_prompt = build_dynamic_master_prompt(aptitudes)
            return [f"System: {dynamic_master_prompt}"], 1, False, None
        except Exception as e:
            print(f"Error al obtener aptitudes: {e}")
            raise Exception("No se pueden obtener las aptitudes para iniciar el cuestionario")
    
    item = progress_response['Item']
    current_status = item.get('Status', 'IN_PROGRESS')
    history = item.get('History', [])
    next_question = int(item.get('QuestionNumber', 1))
    final_scores = item.get('FinalScores', None)
    
    return history, next_question, current_status == 'FINISHED', final_scores

def build_messages_from_history(history):
    """Construye la lista de mensajes para Bedrock desde el historial"""
    messages_list = []
    
    for line in history:
        if line.startswith("System:"):
            role = "user"
            text_content = line[7:].strip()
        elif line.startswith("Usuario:"):
            role = "user"
            text_content = line[9:].strip()
        elif line.startswith("Asistente:"):
            role = "assistant"
            text_content = line[11:].strip()
        else:
            continue

        messages_list.append({
            "role": role,
            "content": [{"text": text_content}]
        })
    
    return messages_list

def call_bedrock(messages_list, is_final_analysis=False):
    """Invoca el modelo de Bedrock"""
    payload = {
        "messages": messages_list,
        "inferenceConfig": {
            "maxTokens": 512,
            "temperature": 0.1,
            "topP": 0.9,
            "stopSequences": ["Usuario:", "Asistente:"]
        }
    }
    
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
    
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(payload),
        accept='application/json',
        contentType='application/json'
    )
    
    response_body = json.loads(response.get('body').read())
    
    if is_final_analysis and 'output' in response_body and 'message' in response_body['output']:
        # Extraer datos estructurados del tool use
        message = response_body['output']['message']
        if 'content' in message:
            for content in message['content']:
                if content.get('toolUse'):
                    tool_input = content['toolUse']['input']
                    return tool_input['conclusion'], tool_input['aptitudes_scores']
    
    return response_body['output']['message']['content'][0]['text'].strip(), None



def save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores):
    """Guarda el progreso del chat en DynamoDB"""
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
                'QuestionNumber': 6,
                'History': history,
                'Status': 'FINISHED',
                'FinalScores': final_scores_as_strings
            }
        )
        return 'FINISHED'
    else:
        new_question_number = next_question + 1
        progress_table.put_item(
            Item={
                'ChatID': chat_id,
                'UserID': user_id,
                'QuestionNumber': new_question_number,
                'History': history,
                'Status': 'IN_PROGRESS' 
            }
        )
        return f'Waiting for Q{new_question_number}'

def build_response(cleaned_response, chat_id, status, history, final_scores=None):
    """Construye la respuesta final"""
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
        'headers': {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        },
        'body': json.dumps(response_data)
    }

def handler(event, context):
    """Función principal de la Lambda"""
    # Manejar solicitudes OPTIONS para CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            'body': ''
        }
    
    today_date = date.today().isoformat()
    quota_table = dynamodb.Table(QUOTA_TABLE_NAME)
    progress_table = dynamodb.Table(PROGRESS_TABLE_NAME)

    try:
        # Validar request
        request_data, error_response = validate_request(json.loads(event.get('body', '{}')))
        if error_response:
            return error_response
        
        user_id, prompt, chat_id = request_data
        
        # Verificar cuotas
        quota_error = check_quotas(quota_table, user_id, today_date)
        if quota_error:
            return quota_error
        
        # Obtener estado del chat
        history, next_question, is_finished, saved_final_scores = get_chat_state(progress_table, chat_id)
        
        # Si el test ya terminó, retornar historial con final_scores
        if is_finished:
            revert_global_quota(quota_table, today_date)
            return build_response(
                "Test finalizado. Aquí está el historial completo.",
                chat_id, 'FINISHED', history, saved_final_scores
            )
        
        # Agregar respuesta del usuario al historial
        if next_question > 1:
            history.append(f"Usuario: {prompt}")
        
        # Construir mensajes y llamar Bedrock
        messages_list = build_messages_from_history(history)
        is_final_analysis = next_question >= 5  # Última pregunta
        
        if is_final_analysis:
            conclusion, aptitudes_scores = call_bedrock(messages_list, True)
            cleaned_response = conclusion
            final_scores = aptitudes_scores
            is_finished = True
        else:
            chatbot_response, _ = call_bedrock(messages_list, False)
            cleaned_response = chatbot_response
            final_scores = None
            is_finished = False
        
        history.append(f"Asistente: {cleaned_response}")
        
        # Guardar progreso
        status = save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores)
        
        # Construir y retornar respuesta
        return build_response(cleaned_response, chat_id, status, history, final_scores)

    except Exception as e:
        print(f"Error en Lambda: {e}")
        
        # Revertir cuota global si no fue un error de cuota
        if 'Quota Exceeded' not in str(e):
            revert_global_quota(quota_table, today_date)
        
        return {
            'statusCode': 500,
            'headers': {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            'body': json.dumps({'error': 'Error interno del servidor', 'detail': str(e)})
        }