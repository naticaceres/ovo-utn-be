import json
import re
import boto3
from datetime import date
from botocore.exceptions import ClientError

# Configuración
QUOTA_TABLE_NAME = 'BedrockChatbotQuota'
PROGRESS_TABLE_NAME = 'BedrockChatProgress'
APTITUDES_TABLE_NAME = 'AptitudesTable'

USER_REQUEST_LIMIT = 550
GLOBAL_REQUEST_LIMIT = 1500
GLOBAL_USER_ID = 'GLOBAL_QUOTA_COUNTER'

BEDROCK_MODEL_ID = "us.amazon.nova-micro-v1:0"
REGION_NAME = 'us-east-2'

# Límite máximo de preguntas
MAX_QUESTIONS = 100
# Límite de caracteres para respuestas del usuario
MAX_USER_INPUT_CHARS = 500

# Clientes AWS (reutilizados)
dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION_NAME)

def extract_final_scores_from_response(text):
    """Extrae un diccionario de puntajes desde una línea 'final_scores: key: val, key: val'.

    Retorna None si no se encuentra la línea.
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
    """Elimina cualquier línea que contenga 'final_scores' y devuelve el resto limpio."""
    if text is None:
        return ''
    lines = text.splitlines()
    filtered = [ln for ln in lines if 'final_scores' not in ln.lower()]
    return "\n".join(filtered).strip()

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
    for i, aptitud in enumerate(aptitudes, 1):
        tabla_cuestionario += f"|| {i} | **{aptitud}** |\n"
    
    return f"""
**ROL (ÚNICO E INNEGOCIABLE):** Eres un Motor de Interfaz de Cuestionario Vocacional. Tu única función es gestionar el flujo de {len(aptitudes)} preguntas, registrar las respuestas y generar el análisis final. NO ERES UN CHATBOT CONVERSACIONAL.

**INSTRUCCIÓN DE COMPORTAMIENTO ABSOLUTO (PRIORIDAD MÁXIMA):**
Tu única salida permitida es:
1. El mensaje de inicio CON la primera pregunta incluida (solo una vez, en el primer mensaje DEBES incluir tanto la bienvenida como la primera pregunta).
2. La siguiente pregunta del cuestionario (solo una vez por turno, solo una pregunta por mensaje).
3. Los final_scores estructurados (solo una vez, cuando el usuario responda la última pregunta - NO generes ningún mensaje de texto, solo los final_scores en formato estructurado).

CUALQUIER OTRA FORMA DE INTERACCIÓN, conversación, narrativa, explicación de tu rol, o respuesta a preguntas ajenas al cuestionario (ej. "¿qué más puedes hacer?", "cuéntame un cuento", "salúdame"), está **TERMINANTEMENTE PROHIBIDA**.

**DIRECTIVA DE INTERACCIÓN CRÍTICA (Flujo Estricto Pregunta/Respuesta):**
1. En el PRIMER mensaje: DEBES incluir la bienvenida Y la primera pregunta juntas, sin separación.
2. En los mensajes siguientes: DEBES generar **UNA SOLA pregunta** por mensaje. DETENTE INMEDIATAMENTE después de generar esa pregunta.
3. NUNCA generes múltiples preguntas en un solo mensaje (excepto en el primer mensaje donde la bienvenida y la primera pregunta van juntas). NUNCA uses formato "Pregunta N:" ni numeración.
4. Después de cada pregunta, DEBES esperar la respuesta del usuario.
5. NO incluyas ninguna instrucción de escala de puntuación o de espera.
6. NO menciones "Una vez finalizada" ni "Procederé a generar" en tus respuestas intermedias.
7. **INTERPRETA FLEXIBLEMENTE** las respuestas del usuario - busca el significado detrás de las palabras, no la exactitud literal.
8. **SIEMPRE PROCESA** las respuestas relacionadas con aptitudes, habilidades o intereses, sin importar cómo estén expresadas.

**PERFIL DEL USUARIO (CONTEXTO CRÍTICO):**
- El usuario es un ESTUDIANTE con muy poca o NULA experiencia profesional.
- NO asumas que tiene experiencia laboral, ventas, trabajo en empresas, o situaciones profesionales.
- Enfócate en situaciones ACADÉMICAS, ESCOLARES, proyectos estudiantiles, actividades extracurriculares, trabajos grupales, tareas escolares, hobbies, intereses personales, y experiencias de vida cotidiana.
- Las preguntas deben ser accesibles para alguien que está explorando su vocación sin haber trabajado aún.

**GUÍA DE REDACCIÓN DE PREGUNTAS (Calidad Clínica, Estilo Psicología Vocacional):**
- Tu tono es profesional, cálido y focalizado, como un psicólogo especializado en orientación vocacional.
- Cada pregunta debe explorar comportamientos observables, decisiones concretas, preferencias y experiencias reales relacionadas con la aptitud objetivo.
- **CONTEXTO ESTUDIANTIL OBLIGATORIO:** Todas las preguntas deben referirse a situaciones escolares, académicas, proyectos estudiantiles, trabajos grupales, actividades extracurriculares, hobbies, intereses personales, o experiencias de vida cotidiana. NUNCA uses ejemplos de trabajo profesional, ventas, empresas, o experiencia laboral.
- Evita preguntas genéricas del tipo "¿Cómo te sientes acerca de X?". En su lugar, usa mini-escenarios, ejemplos situacionales y recordatorios de experiencias estudiantiles o personales.
- Varía la forma de las preguntas entre turnos para evitar repetición de patrones. No uses encabezados como "Pregunta N:" ni formato de lista; formula una frase clara y corta.
- Mantén cada pregunta en UNA oración. No agregues agradecimientos ni transiciones ("gracias por tu respuesta", "vamos a la siguiente").
- Acepta respuestas elaboradas en múltiples oraciones.
 
 **ESTRATEGIA DE GENERACIÓN ESPONTÁNEA (Adaptación al usuario):**
 - Genera preguntas de forma libre, sin plantillas fijas ni fórmulas repetidas.
 - Adapta tono, vocabulario y longitud a cómo se expresa el usuario (espeja su estilo comunicativo).
 - Prioriza preguntas conductuales y situacionales basadas en contexto estudiantil; referencia elementos concretos mencionados por el usuario cuando existan.
 - Cuando sea útil para evidenciar la aptitud, plantea decisiones breves o pequeños dilemas realistas en contextos escolares, académicos o de vida estudiantil.
 - Evita repetir el mismo inicio o estructura en preguntas consecutivas.
 - **NUNCA** uses ejemplos de: trabajo profesional, ventas, clientes, empresas, jefes, colegas profesionales, o cualquier situación laboral.

Prohibiciones estrictas para cada pregunta:
- No uses plantillas fijas ni fórmulas repetidas para formular preguntas, cada pregunta debe ser distinta de la anterior.
- No antepongas "Pregunta N:" ni mensajes de transición.
- No menciones escalas ni pidas que el usuario se puntúe.
- **PROHIBIDO:** Asumir experiencia profesional, laboral, de ventas, o situaciones empresariales. El usuario es un estudiante sin experiencia profesional.

**MANEJO DE DESVÍOS Y REPREGUNTAS DEL USUARIO:**
- Si el usuario formula una pregunta, pide explicaciones, intenta conversar, o se desvía del tema, RESPONDE EXCLUSIVAMENTE con el siguiente mensaje fijo (sin agregar nada más): “Para continuar, responde la ultima pregunta. No puedo atender otras consultas.”\n- Después del guardrail, en el siguiente turno, retoma con una nueva pregunta válida solo si el usuario vuelve a responder sobre la aptitud.

**REGLAS DE DESVÍO Y RESTRICCIÓN (Guardrails):**
El guardrail SOLO debe activarse si el usuario:
- Hace preguntas sobre el sistema o tu funcionamiento
- Inicia conversación casual no relacionada con aptitudes
- Pide explicaciones sobre el cuestionario
- Intenta cambiar de tema completamente
- Responde con una pregunta

**NUNCA actives el guardrail para respuestas sobre aptitudes o cualquier respuesta que indique nivel de aptitud o interés**

**CRITERIOS DE INTERPRETACIÓN DE RESPUESTAS (Semántica sobre palabras clave):**
- Interpreta el significado completo de la respuesta.
- Considera: intensidad, frecuencia, autonomía, consistencia temporal, evidencia conductual y recencia.
- Tolera ambigüedad y varianza cultural; infiere con prudencia a partir del propio contexto del usuario.
- No menciones escalas ni pidas auto-puntuación en ningún momento.
- Mantén una evaluación latente interna. En el análisis final, transforma esa evaluación a una escala 1–10 por aptitud, proporcional a la evidencia observada.

**TABLA DE CUESTIONARIO ({len(aptitudes)} Preguntas / {len(aptitudes)} Áreas Representativas):**

| P# | Aptitud a Medir (Área de Foco) |
| :---: | :--- |
{tabla_cuestionario}

**ANÁLISIS FINAL:**
Una vez finalizada la pregunta {len(aptitudes)} y recibida su respuesta del usuario:
1. Evalúa cada aptitud con puntaje del 1 al 10 según las respuestas del usuario
2. El sistema usará formato estructurado para capturar SOLO los final_scores (aptitudes_scores)
3. NO generes ningún mensaje de texto, conclusión ni respuesta visible al usuario
4. Solo proporciona los final_scores en el formato estructurado requerido

**INICIO DE LA INTERACCIÓN:**
Empieza AHORA con un mensaje que incluya:
1. Una breve bienvenida al cuestionario vocacional (máximo 2 oraciones).
2. Inmediatamente después, sin saltos de línea ni separación, la PRIMERA PREGUNTA del cuestionario relacionada con la primera aptitud de la tabla.

IMPORTANTE: El mensaje de inicio y la primera pregunta DEBEN estar en el mismo mensaje, sin separación. No generes solo la bienvenida y esperes; incluye ambos elementos juntos.
"""

def get_final_analysis_schema():
    """
    Schema para el análisis final con structured output.
    Solo retorna los final_scores (aptitudes_scores), sin conclusión de texto.
    
    Referencia: AWS Bedrock Structured Outputs
    https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-structured-outputs.html
    """
    return {
        "type": "object",
        "properties": {
            "aptitudes_scores": {
                "type": "object",
                "description": "Puntajes de aptitudes del 1 al 10. Debe incluir todas las aptitudes evaluadas.",
                "additionalProperties": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 10
                }
            }
        },
        "required": ["aptitudes_scores"]
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
    prompt = body.get('prompt')
    
    if not all([chat_id]):
        return None, {
            'statusCode': 400,
            'headers': {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            'body': json.dumps({'error': 'Faltan parámetros: ChatID es obligatorio.'})
        }
    user_id = user_id if user_id else 'ANONYMOUS_USER'
    if isinstance(prompt, str) and len(prompt) > MAX_USER_INPUT_CHARS:
        return None, {
            'statusCode': 400,
            'headers': {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            },
            'body': json.dumps({'error': f'La respuesta excede el máximo de {MAX_USER_INPUT_CHARS} caracteres.'})
        }
    
    return (user_id, prompt, chat_id), None

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
            # Limitar la cantidad de preguntas a MAX_QUESTIONS
            limited_aptitudes = aptitudes[:MAX_QUESTIONS]
            dynamic_master_prompt = build_dynamic_master_prompt(limited_aptitudes)
            total_questions = len(limited_aptitudes)
            return [f"System: {dynamic_master_prompt}"], 1, False, None, total_questions, True
        except Exception as e:
            print(f"Error al obtener aptitudes: {e}")
            raise Exception("No se pueden obtener las aptitudes para iniciar el cuestionario")
    
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

def get_last_assistant_message(history):
    """Obtiene el último mensaje del asistente del historial."""
    for line in reversed(history):
        if line.startswith("Asistente:"):
            return line[11:].strip()
    return ""

def extract_first_question(text):
    """
    Extrae solo la primera pregunta o mensaje del texto generado por el modelo.
    Detiene en la primera pregunta que encuentre o en patrones que indiquen múltiples preguntas.
    
    Esta función implementa un post-procesamiento defensivo para asegurar que solo
    se devuelva una pregunta, incluso si el modelo genera múltiples.
    
    Referencia: AWS Bedrock Inference Parameters
    https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
    """
    if not text:
        return text
    
    # Dividir por líneas para analizar
    lines = text.split('\n')
    first_question_parts = []
    found_content = False
    
    # Patrones que indican inicio de una nueva pregunta (stop patterns)
    stop_patterns = [
        r'^\*\*Pregunta\s+\d+:\*\*',  # **Pregunta N:**
        r'^Pregunta\s+\d+:',  # Pregunta N:
        r'^\d+\.\s+',  # Número seguido de punto
        r'^Una vez finalizada',  # "Una vez finalizada..."
        r'^Procederé a generar',  # "Procederé a generar..."
    ]
    
    for line in lines:
        line_stripped = line.strip()
        
        # Si encontramos una línea vacía después de contenido, es un separador - detener
        if not line_stripped:
            if found_content:
                break
            continue
        
        # Verificar si esta línea coincide con un patrón de stop
        should_stop = False
        for pattern in stop_patterns:
            if re.match(pattern, line_stripped, re.IGNORECASE):
                should_stop = True
                break
        
        if should_stop:
            break
        
        first_question_parts.append(line_stripped)
        found_content = True
        
        # Si la línea termina con "?" y ya tenemos contenido, probablemente es el final de la pregunta
        if line_stripped.endswith('?'):
            break
    
    result = ' '.join(first_question_parts).strip()
    
    # Si no encontramos nada útil, devolver el texto original truncado en la primera oración
    if not result:
        # Buscar la primera oración que termine con "?"
        match = re.search(r'^[^?]*\?', text)
        if match:
            result = match.group(0).strip()
        else:
            # Si no hay "?", tomar la primera oración hasta el primer punto
            match = re.search(r'^[^.]*\.', text)
            if match:
                result = match.group(0).strip()
            else:
                # Fallback: primeros 200 caracteres
                result = text[:200].strip()
    
    return result

def call_bedrock(messages_list, is_final_analysis=False):
    """
    Invoca el modelo de Bedrock con configuración optimizada para generar una sola pregunta.
    
    Referencia: AWS Bedrock Runtime API - InvokeModel
    https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html
    """
    payload = {
        "messages": messages_list,
        "inferenceConfig": {
            # Reducido a 200 tokens para forzar una sola pregunta
            # Referencia: AWS Bedrock Inference Parameters - maxTokens
            # https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
            "maxTokens": 200,
            "temperature": 0.1,
            "topP": 0.9,
            # Stop sequences mejoradas para capturar patrones de múltiples preguntas
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
    raw_response = response_body['output']['message']['content'][0]['text'].strip()
    
    # Post-procesar para extraer solo la primera pregunta (no aplica para análisis final)
    if not is_final_analysis:
        raw_response = extract_first_question(raw_response)
    
    return raw_response, None



def save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores, total_questions):
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
                'QuestionNumber': total_questions + 1,
                'History': history,
                'Status': 'FINISHED',
                'FinalScores': final_scores_as_strings,
                'TotalQuestions': total_questions
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
                'Status': 'IN_PROGRESS',
                'TotalQuestions': total_questions
            }
        )
        return f'Waiting for {new_question_number} of {total_questions}'

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

        # Obtener estado del chat (antes de cuotas para poder manejar recupero sin consumir cuota)
        history, next_question, is_finished, saved_final_scores, total_questions, is_new_chat = get_chat_state(progress_table, chat_id)
        
        # Si el test ya terminó, retornar historial con final_scores
        if is_finished:
            revert_global_quota(quota_table, today_date)
            return build_response(
                "Test finalizado. Aquí está el historial completo.",
                chat_id, 'FINISHED', history, saved_final_scores
            )
        
        # Si es un chat en progreso y no se recibió prompt, devolver historial sin avanzar (sin consumir cuota ni llamar a Bedrock)
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
        
        # Verificar si esta es la última pregunta (después de agregar la respuesta del usuario)
        # Si next_question >= total_questions, significa que el usuario acaba de responder la última pregunta
        is_final_question = next_question >= total_questions
        
        if is_final_question:
            # Llamar a Bedrock con structured output para obtener final_scores
            # Referencia: AWS Bedrock Structured Outputs
            # https://docs.aws.amazon.com/bedrock/latest/userguide/model-customization-structured-outputs.html
            conclusion, aptitudes_scores = call_bedrock(messages_list, is_final_analysis=True)
            final_scores = aptitudes_scores  # Los aptitudes_scores son los final_scores que necesitamos
            is_finished = True
            cleaned_response = ""  # No agregamos mensaje del asistente al historial, solo finalizamos
            
            # Guardar progreso como FINISHED con final_scores
            status = save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores, total_questions)
            
            # Retornar respuesta con historial y final_scores
            return build_response(cleaned_response, chat_id, status, history, final_scores)
        else:
            # Si no es la última pregunta, generar la siguiente pregunta normalmente
            chatbot_response, _ = call_bedrock(messages_list, is_final_analysis=False)
            cleaned_response = chatbot_response
            final_scores = None
            is_finished = False
            
            history.append(f"Asistente: {cleaned_response}")
            
            # Guardar progreso
            status = save_chat_progress(progress_table, chat_id, user_id, history, is_finished, next_question, final_scores, total_questions)
            
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