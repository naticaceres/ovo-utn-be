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
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION_NAME)

def get_aptitudes_from_table():
    """Lee todas las aptitudes activas de la tabla AptitudesTable"""
    aptitudes_table = dynamodb.Table(APTITUDES_TABLE_NAME)
    response = aptitudes_table.scan(
        FilterExpression='activa = :activa',
        ExpressionAttributeValues={':activa': True}
    )
    return [item['aptitud'] for item in response['Items']]

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

**REGLAS DE DESVÍO Y RESTRICCIÓN (Guardrails):**
Si la entrada del usuario NO es una respuesta sobre su nivel de aptitud (ej. preguntas sobre el sistema, conversación casual, etc.):
* **IGNORA** completamente el contenido de la entrada.
* **DEBES RESPONDER EXCLUSIVAMENTE** con el siguiente mensaje fijo y nada más:
    "**No estoy entrenado para responder eso. Por favor, concéntrate en responder la última pregunta con tu nivel de aptitud.**"

**IMPORTANTE:** Respuestas como "bien", "mal", "sí", "no", "mucho", "poco", etc. SON VÁLIDAS y deben ser procesadas normalmente.

**ESCALA DE RESPUESTA E INTERPRETACIÓN (Lenguaje Natural):**
El usuario responderá con palabras o frases que debes interpretar en una escala interna de 1 a 4.

| Puntuación Interna | Palabras Clave de Interpretación (Ejemplos) |
| :---: | :--- |
| **1** | Nada apto, muy poco, nunca, incompetente, nada de nada, absolutamente nada, en absoluto, no, jamas, nunca, mal, nada, cero |
| **2** | Medianamente, a veces, regular, más o menos, poco, algo, un poco |
| **3** | Bastante, sí, a menudo, competente, bien, bueno, bastante bien, me gusta |
| **4** | Muy apto, excelente, totalmente, mucho, muy bien, perfecto, excelente, me encanta |

**TABLA DE CUESTIONARIO ({len(aptitudes[:5])} Preguntas / {len(aptitudes[:5])} Áreas Representativas):**

| P# | Aptitud a Medir (Área de Foco) |
| :---: | :--- |
{tabla_cuestionario}

**ANÁLISIS FINAL (FORMATO ESTRICTO):**
Una vez finalizada la pregunta {len(aptitudes[:5])} y recibida su respuesta, DEBES:
1. Interpretar y registrar la puntuación (entre 0 y 1)para cada respuesta.
2. Presentar los {len(aptitudes[:5])} resultados en una lista numerada, ordenados **de mayor a menor puntuación**.
3. Identificar y nombrar el **ÁREA DOMINANTE** (la de mayor puntuación).
4. Ofrecer una **CONCLUSIÓN VOCACIONAL** de un párrafo (máximo 40 palabras) que sugiera brevemente 2-3 Áreas Ocupacionales compatibles con el Área Dominante.
5. SALIDA JSON REQUERIDA (ÚLTIMA LÍNEA): Después de la Conclusión Vocacional, en una nueva línea, DEBES generar un objeto JSON sin formato (sin markdown blocks o formato de código) llamado "final_scores" que contenga las aptitudes y sus respectivas puntuaciones normalizadas (0.0 a 1.0) calculadas en el paso 2. El objeto debe seguir estrictamente este formato: final_scores: {{aptitud_1: puntuación_normalizada,aptitud_2:puntuación_normalizada}}
Por ejemplo:  (mensaje de salida final) final_scores: {{aptitud_1: 0.5,aptitud_2:0.3}}

**INICIO DE LA INTERACCIÓN:**
Empieza AHORA con el mensaje de inicio y la primera pregunta.
"""

def extract_final_scores_from_response(chatbot_response):
    """Extrae el objeto JSON final_scores de la respuesta del chatbot"""
    pattern = r'final_scores:\s*\{([^}]+)\}'
    match = re.search(pattern, chatbot_response)
    
    if match:
        try:
            json_content = match.group(1).strip()
            json_str = "{" + json_content + "}"
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error al parsear final_scores: {e}")
            return None
    return None

def clean_chatbot_response(chatbot_response):
    """Remueve el objeto JSON final_scores de la respuesta del chatbot"""
    pattern = r'final_scores:\s*\{[^}]+\}'
    return re.sub(pattern, '', chatbot_response).strip()

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
    
    if not all([user_id, chat_id]):
        return None, {
            'statusCode': 400,
            'body': json.dumps({'error': 'Faltan parámetros: UserID y ChatID son obligatorios.'})
        }
    
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
                    'body': json.dumps({
                        'error': 'Global Quota Exceeded', 
                        'message': f'Se superó el límite global de {GLOBAL_REQUEST_LIMIT} solicitudes.'
                    })
                }
            else:
                revert_global_quota(quota_table, today_date)
                return {
                    'statusCode': 429, 
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
            return [f"System: {dynamic_master_prompt}"], 1, False
        except Exception as e:
            print(f"Error al obtener aptitudes: {e}")
            raise Exception("No se pueden obtener las aptitudes para iniciar el cuestionario")
    
    item = progress_response['Item']
    current_status = item.get('Status', 'IN_PROGRESS')
    history = item.get('History', [])
    next_question = int(item.get('QuestionNumber', 1))
    
    return history, next_question, current_status == 'FINISHED'

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

def call_bedrock(messages_list):
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
    
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(payload),
        accept='application/json',
        contentType='application/json'
    )
    
    response_body = json.loads(response.get('body').read())
    return response_body['output']['message']['content'][0]['text'].strip()

def process_chatbot_response(chatbot_response, next_question):
    """Procesa la respuesta del chatbot y extrae final_scores si es necesario"""
    final_scores = None
    cleaned_response = chatbot_response
    
    if "ANÁLISIS FINAL" in chatbot_response.upper() or next_question >= 6:
        final_scores = extract_final_scores_from_response(chatbot_response)
        cleaned_response = clean_chatbot_response(chatbot_response)
    
    return final_scores, cleaned_response

def save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question):
    """Guarda el progreso del chat en DynamoDB"""
    if is_finished:
        progress_table.put_item(
            Item={
                'ChatID': chat_id,
                'UserID': user_id,
                'QuestionNumber': 6,
                'History': history,
                'Status': 'FINISHED' 
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
        'headers': {"Content-Type": "application/json"},
        'body': json.dumps(response_data)
    }

def handler(event, context):
    """Función principal de la Lambda"""
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
        history, next_question, is_finished = get_chat_state(progress_table, chat_id)
        
        # Si el test ya terminó, retornar historial
        if is_finished:
            revert_global_quota(quota_table, today_date)
            return build_response(
                "Test finalizado. Aquí está el historial completo.",
                chat_id, 'FINISHED', history
            )
        
        # Agregar respuesta del usuario al historial
        if next_question > 1:
            history.append(f"Usuario: {prompt}")
        
        # Construir mensajes y llamar Bedrock
        messages_list = build_messages_from_history(history)
        chatbot_response = call_bedrock(messages_list)
        
        # Procesar respuesta
        final_scores, cleaned_response = process_chatbot_response(chatbot_response, next_question)
        history.append(f"Asistente: {cleaned_response}")
        
        # Determinar si terminó
        is_finished = "ANÁLISIS FINAL" in chatbot_response.upper() or next_question >= 6
        
        # Guardar progreso
        status = save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question)
        
        # Construir y retornar respuesta
        return build_response(cleaned_response, chat_id, status, history, final_scores)

    except Exception as e:
        print(f"Error en Lambda: {e}")
        
        # Revertir cuota global si no fue un error de cuota
        if 'Quota Exceeded' not in str(e):
            revert_global_quota(quota_table, today_date)
        
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error interno del servidor', 'detail': str(e)})
        }