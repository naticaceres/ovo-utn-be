import json
import boto3
from datetime import date
from botocore.exceptions import ClientError

# --- CONFIGURACIÓN DE LÍMITES Y RECURSOS ---
# Tablas de DynamoDB
QUOTA_TABLE_NAME = 'BedrockChatbotQuota'
PROGRESS_TABLE_NAME = 'BedrockChatProgress'
APTITUDES_TABLE_NAME = 'AptitudesTable'

# Límites
USER_REQUEST_LIMIT = 25
GLOBAL_REQUEST_LIMIT = 100
GLOBAL_USER_ID = 'GLOBAL_QUOTA_COUNTER'

# Configuración de Bedrock
BEDROCK_MODEL_ID = "us.amazon.nova-micro-v1:0"
REGION_NAME = 'us-east-2'

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION_NAME) 

# --- PROMPT MAESTRO CON GUARDRAILS ---
MASTER_PROMPT = """
**ROL (ÚNICO E INNEGOCIABLE):** Eres un Motor de Interfaz de Cuestionario Vocacional. Tu única función es gestionar el flujo de 5 preguntas, registrar las respuestas y generar el análisis final. NO ERES UN CHATBOT CONVERSACIONAL.

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
Si la entrada del usuario no es una respuesta directa y relevante a la última pregunta:
* **IGNORA** completamente el contenido de la entrada.
* **DEBES RESPONDER EXCLUSIVAMENTE** con el siguiente mensaje fijo y nada más:
    "**No estoy entrenado para responder eso. Por favor, concéntrate en responder la última pregunta con tu nivel de aptitud.**"

**ESCALA DE RESPUESTA E INTERPRETACIÓN (Lenguaje Natural):**
El usuario responderá con palabras o frases que debes interpretar en una escala interna de 1 a 4.

| Puntuación Interna | Palabras Clave de Interpretación (Ejemplos) |
| :---: | :--- |
| **1** | Nada apto, muy poco, nunca, incompetente |
| **2** | Medianamente, a veces, regular, más o menos |
| **3** | Bastante, sí, a menudo, competente |
| **4** | Muy apto, excelente, totalmente, mucho |

**TABLA DE CUESTIONARIO (5 Preguntas / 5 Áreas Representativas):**

| P# | Aptitud a Medir (Área de Foco) |
| :---: | :--- |
| 1 | **Razonamiento Lógico / Analítico** |
| 2 | **Creatividad / Artístico-Espacial** |
| 3 | **Habilidad Numérica / Organizativa** |
| 4 | **Comunicación / Persuasión (Verbal y Social)** |
| 5 | **Destreza Práctica / Tecnológica** |

**ANÁLISIS FINAL (FORMATO ESTRICTO):**
Una vez finalizada la pregunta 5 y recibida su respuesta, DEBES:
1. Interpretar y registrar la puntuación (1 a 4) para cada respuesta.
2. Presentar los 5 resultados en una lista numerada, ordenados **de mayor a menor puntuación**.
3. Identificar y nombrar el **ÁREA DOMINANTE** (la de mayor puntuación).
4. Ofrecer una **CONCLUSIÓN VOCACIONAL** de un párrafo (máximo 40 palabras) que sugiera brevemente 2-3 Áreas Ocupacionales compatibles con el Área Dominante.

**INICIO DE LA INTERACCIÓN:**
Empieza AHORA con el mensaje de inicio y la primera pregunta.
"""

# --- FUNCIONES DE AYUDA ---

def get_aptitudes_from_table():
    """
    Lee todas las aptitudes activas de la tabla AptitudesTable
    """
    try:
        aptitudes_table = dynamodb.Table(APTITUDES_TABLE_NAME)
        response = aptitudes_table.scan(
            FilterExpression='activa = :activa',
            ExpressionAttributeValues={':activa': True}
        )
        
        aptitudes = [item['aptitud'] for item in response['Items']]
        return aptitudes
    except Exception as e:
        print(f"Error al leer aptitudes: {e}")
        # Retornar aptitudes por defecto si hay error
        return [
            "Razonamiento Lógico / Analítico",
            "Creatividad / Artístico-Espacial", 
            "Habilidad Numérica / Organizativa",
            "Comunicación / Persuasión (Verbal y Social)",
            "Destreza Práctica / Tecnológica"
        ]

def extract_final_scores_from_response(chatbot_response):
    """
    Extrae el objeto JSON final_scores de la respuesta del chatbot
    """
    import re
    
    # Buscar el patrón final_scores: {...}
    pattern = r'final_scores:\s*\{([^}]+)\}'
    match = re.search(pattern, chatbot_response)
    
    if match:
        try:
            # Extraer el contenido del JSON
            json_content = match.group(1)
            # Limpiar y parsear el JSON
            json_content = json_content.strip()
            # Convertir a formato JSON válido
            json_str = "{" + json_content + "}"
            # Parsear el JSON
            final_scores = json.loads(json_str)
            return final_scores
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error al parsear final_scores: {e}")
            return None
    return None

def clean_chatbot_response(chatbot_response):
    """
    Remueve el objeto JSON final_scores de la respuesta del chatbot
    """
    import re
    
    # Remover el patrón final_scores: {...}
    pattern = r'final_scores:\s*\{[^}]+\}'
    cleaned_response = re.sub(pattern, '', chatbot_response).strip()
    
    return cleaned_response

def build_dynamic_master_prompt(aptitudes):
    """
    Construye el master prompt dinámicamente usando las aptitudes de la tabla
    """
    # Crear la tabla de cuestionario dinámicamente
    tabla_cuestionario = ""
    for i, aptitud in enumerate(aptitudes[:5], 1):  # Máximo 5 aptitudes
        tabla_cuestionario += f"|| {i} | **{aptitud}** |\n"
    
    master_prompt = f"""
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
Si la entrada del usuario no es una respuesta directa y relevante a la última pregunta:
* **IGNORA** completamente el contenido de la entrada.
* **DEBES RESPONDER EXCLUSIVAMENTE** con el siguiente mensaje fijo y nada más:
    "**No estoy entrenado para responder eso. Por favor, concéntrate en responder la última pregunta con tu nivel de aptitud.**"

**ESCALA DE RESPUESTA E INTERPRETACIÓN (Lenguaje Natural):**
El usuario responderá con palabras o frases que debes interpretar en una escala interna de 1 a 4.

| Puntuación Interna | Palabras Clave de Interpretación (Ejemplos) |
| :---: | :--- |
| **1** | Nada apto, muy poco, nunca, incompetente |
| **2** | Medianamente, a veces, regular, más o menos |
| **3** | Bastante, sí, a menudo, competente |
| **4** | Muy apto, excelente, totalmente, mucho |

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

**INICIO DE LA INTERACCIÓN:**
Empieza AHORA con el mensaje de inicio y la primera pregunta.
"""
    return master_prompt

def handle_quota_check(quota_table, user_id, today_date, limit, is_global):
    """
    Verifica y actualiza de forma atómica el contador en DynamoDB.
    Lanza ConditionalCheckFailedException si el límite se ha superado.
    """
    key = {'UserID': user_id, 'Date': today_date}
    
    # Simplemente intentamos la actualización. Si falla la condición, se lanza la excepción.
    quota_table.update_item(
        Key=key,
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
    return True

# --- FUNCIÓN PRINCIPAL ---

def handler(event, context):
    today_date = date.today().isoformat()
    quota_table = dynamodb.Table(QUOTA_TABLE_NAME)
    progress_table = dynamodb.Table(PROGRESS_TABLE_NAME)

    try: 
        # 1. Extracción de datos
        body = json.loads(event.get('body', '{}'))
        user_id = body.get('UserID')
        prompt = body.get('prompt')
        chat_id = body.get('ChatID')

        if not all([user_id, chat_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Faltan parámetros: UserID, prompt y ChatID son obligatorios.'})
            }

        # --- 2. VERIFICACIÓN DE CUOTAS ---
        
        # 2a. Chequeo y Actualización Global
        try:
            handle_quota_check(quota_table, GLOBAL_USER_ID, today_date, GLOBAL_REQUEST_LIMIT, True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return {'statusCode': 429, 'body': json.dumps({'error': 'Global Quota Exceeded', 'message': f'Se superó el límite global de {GLOBAL_REQUEST_LIMIT} solicitudes.'})}
            raise # Relanzar cualquier otro ClientError

        # 2b. Chequeo y Actualización por Usuario
        try:
            handle_quota_check(quota_table, user_id, today_date, USER_REQUEST_LIMIT, False)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # Si falla el límite de usuario, revertimos la cuota global que ya incrementamos
                quota_table.update_item(
                    Key={'UserID': GLOBAL_USER_ID, 'Date': today_date},
                    UpdateExpression="SET #c = #c - :dec",
                    ExpressionAttributeNames={'#c': 'Count'},
                    ExpressionAttributeValues={':dec': 1}
                )
                return {'statusCode': 429, 'body': json.dumps({'error': 'User Quota Exceeded', 'message': f'Has superado tu límite diario de {USER_REQUEST_LIMIT} solicitudes.'})}
            raise # Relanzar cualquier otro ClientError


        # --- 3. GESTIÓN DEL ESTADO DEL CHAT ---
        progress_response = progress_table.get_item(Key={'ChatID': chat_id})
    
        # 3a. Inicializar o cargar el estado
        if 'Item' not in progress_response:
            # Nuevo chat - construir master prompt dinámicamente con aptitudes
            aptitudes = get_aptitudes_from_table()
            dynamic_master_prompt = build_dynamic_master_prompt(aptitudes)
            history = [f"System: {dynamic_master_prompt}"]
            next_question = 1
        else:
            # Chat existente
            item = progress_response['Item']
            current_status = item.get('Status', 'IN_PROGRESS')
            history = item.get('History', [])
            next_question = int(item.get('QuestionNumber', 1))

            # --- LÓGICA DE TEST FINALIZADO (RETORNO RÁPIDO) ---
            if current_status == 'FINISHED':
                # Si el test ya terminó, retornamos el historial inmediatamente sin Bedrock.
                # Revertir la cuota global (ya que no se usará el recurso caro de Bedrock)
                quota_table.update_item(
                    Key={'UserID': GLOBAL_USER_ID, 'Date': today_date},
                    UpdateExpression="SET #c = #c - :dec",
                    ExpressionAttributeNames={'#c': 'Count'},
                    ExpressionAttributeValues={':dec': 1}
                )
                return {
                    'statusCode': 200,
                    'headers': { "Content-Type": "application/json" },
                    'body': json.dumps({
                        'chatbot_response': "Test finalizado. Aquí está el historial completo.",
                        'chat_id': chat_id,
                        'status': 'FINISHED',
                        'full_history': history
                    })
                }
            # ---------------------------------------

            # Si no ha terminado, procedemos con la lógica de conversación
            
            # 3b. Actualizar historial con la ÚLTIMA respuesta del usuario
            if next_question > 1:
                history.append(f"Usuario: {prompt}")

        # --- 4. INVOCACIÓN DE BEDROCK ---
        
        messages_list = []
        
        # Reconstruir la lista de mensajes de conversación a partir del historial
        for line in history:
            if line.startswith("System:"):
                # El master prompt guardado se envía como mensaje de usuario (System Prompt Trick)
                role = "user"
                text_content = line[7:].strip()  # Remover "System: " del inicio
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
        
        # 3. Definir el payload con la lista de mensajes
        payload_bedrock = {
            "messages": messages_list,
            "inferenceConfig": {
                "maxTokens": 512,
                "temperature": 0.1,
                "topP": 0.9,
                "stopSequences": ["Usuario:", "Asistente:"]
            }
        }
        
        # 4. Invocación
        bedrock_response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(payload_bedrock),
            accept='application/json',
            contentType='application/json'
        )
        
        # --- 5. PROCESAMIENTO DE RESPUESTA ---
        
        response_body = json.loads(bedrock_response.get('body').read())
        
        # Extraer el texto de la estructura del API de Mensajes
        try:
            chatbot_response = response_body['output']['message']['content'][0]['text'].strip()
        except (KeyError, IndexError):
            print(f"Error al leer la respuesta de Bedrock. Cuerpo recibido: {response_body}")
            raise Exception("Respuesta de Bedrock mal formada o vacía.")

        
        # 5a. Procesar la respuesta del chatbot
        final_scores = None
        cleaned_response = chatbot_response
        
        # Si es el análisis final, extraer el JSON y limpiar la respuesta
        if "ANÁLISIS FINAL" in chatbot_response.upper() or next_question >= 6:
            final_scores = extract_final_scores_from_response(chatbot_response)
            cleaned_response = clean_chatbot_response(chatbot_response)
        
        # Agregar la respuesta limpia al historial
        history.append(f"Asistente: {cleaned_response}")

        # 5b. Determinar el siguiente paso
        
        if "ANÁLISIS FINAL" in chatbot_response.upper() or next_question >= 6:
            # Chat terminado: GUARDAR el progreso con status FINISHED 
            progress_table.put_item(
                Item={
                    'ChatID': chat_id,
                    'UserID': user_id,
                    'QuestionNumber': 6,
                    'History': history,
                    'Status': 'FINISHED' 
                }
            )
            status_message = 'FINISHED'

        else:
            # Chat continúa: Guardar nuevo estado con status IN_PROGRESS
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
            status_message = f'Waiting for Q{new_question_number}'

        # 6. Construir la respuesta
        response_data = {
            'chatbot_response': cleaned_response,
            'chat_id': chat_id,
            'status': status_message,
            'full_history': history
        }
        
        # Agregar final_scores si existe
        if final_scores is not None:
            response_data['final_scores'] = final_scores
        
        # Retornar la respuesta del chatbot
        return {
            'statusCode': 200,
            'headers': { "Content-Type": "application/json" },
            'body': json.dumps(response_data)
        }


    except Exception as e:
        print(f"Error en Lambda: {e}")
        # Revertir el contador global en caso de cualquier error (excepto límite excedido)
        try:
           # Revertir solo si no fue un error de cuota capturado antes
           if 'Quota Exceeded' not in str(e):
               quota_table.update_item(
                   Key={'UserID': GLOBAL_USER_ID, 'Date': today_date},
                   UpdateExpression="SET #c = #c - :dec",
                   ExpressionAttributeNames={'#c': 'Count'},
                   ExpressionAttributeValues={':dec': 1}
               )
        except Exception as revert_e:
           print(f"Error al intentar revertir el contador global: {revert_e}")

        # Retorna el error 500
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Error interno del servidor', 'detail': str(e)})
        }
