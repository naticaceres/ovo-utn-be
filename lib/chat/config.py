"""
Configuración centralizada para el módulo de chat.

Este módulo contiene todas las constantes, configuraciones y clientes AWS
que se utilizan en el sistema de chat vocacional.
"""

import boto3

# Nombres de tablas DynamoDB
QUOTA_TABLE_NAME = 'BedrockChatbotQuota'
PROGRESS_TABLE_NAME = 'BedrockChatProgress'
APTITUDES_TABLE_NAME = 'AptitudesTable'

# Límites de cuota
USER_REQUEST_LIMIT = 550
GLOBAL_REQUEST_LIMIT = 1500
GLOBAL_USER_ID = 'GLOBAL_QUOTA_COUNTER'

# Configuración de Bedrock
BEDROCK_MODEL_ID = "us.amazon.nova-micro-v1:0"
REGION_NAME = 'us-east-2'

# Límites del cuestionario
MAX_QUESTIONS = 100
MAX_USER_INPUT_CHARS = 500

# Clientes AWS (inicializados una vez, reutilizados)
dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION_NAME)

# Headers CORS estándar (reutilizables)
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization"
}

# Prefijos para parsing del historial
HISTORY_PREFIX_SYSTEM = "System:"
HISTORY_PREFIX_USER = "Usuario:"
HISTORY_PREFIX_ASSISTANT = "Asistente:"

