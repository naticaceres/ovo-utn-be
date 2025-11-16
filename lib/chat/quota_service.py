"""
Servicio de gestión de cuotas para el módulo de chat.

Este módulo encapsula toda la lógica de verificación y gestión de cuotas
para limitar el número de requests por usuario y globalmente.
"""

import json
from botocore.exceptions import ClientError
from config import (
    dynamodb,
    QUOTA_TABLE_NAME,
    GLOBAL_USER_ID,
    USER_REQUEST_LIMIT,
    GLOBAL_REQUEST_LIMIT
)


def handle_quota_check(quota_table, user_id, today_date, limit):
    """
    Verifica y actualiza de forma atómica el contador en DynamoDB.
    
    Usa ConditionalCheckFailedException para detectar cuando se excede el límite.
    
    Args:
        quota_table: Tabla de DynamoDB para cuotas
        user_id: ID del usuario
        today_date: Fecha en formato ISO (YYYY-MM-DD)
        limit: Límite máximo de requests
        
    Raises:
        ClientError: Si se excede el límite (ConditionalCheckFailedException)
    """
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
    """
    Revierte el contador global de cuota (decrementa en 1).
    
    Se usa cuando hay un error y se necesita revertir el incremento
    que se hizo al verificar la cuota global.
    
    Args:
        quota_table: Tabla de DynamoDB para cuotas
        today_date: Fecha en formato ISO (YYYY-MM-DD)
    """
    try:
        quota_table.update_item(
            Key={'UserID': GLOBAL_USER_ID, 'Date': today_date},
            UpdateExpression="SET #c = #c - :dec",
            ExpressionAttributeNames={'#c': 'Count'},
            ExpressionAttributeValues={':dec': 1}
        )
    except Exception as e:
        print(f"Error al revertir cuota global: {e}")


def check_quotas(quota_table, user_id, today_date):
    """
    Verifica las cuotas global y de usuario de forma atómica.
    
    Primero verifica la cuota global, luego la de usuario.
    Si la de usuario falla, revierte la global.
    
    Args:
        quota_table: Tabla de DynamoDB para cuotas
        user_id: ID del usuario
        today_date: Fecha en formato ISO (YYYY-MM-DD)
        
    Returns:
        dict: Respuesta HTTP de error si se excede la cuota, None si está OK
        
    Raises:
        ClientError: Si hay un error inesperado de DynamoDB
    """
    from response_builder import build_error_response
    
    try:
        handle_quota_check(quota_table, GLOBAL_USER_ID, today_date, GLOBAL_REQUEST_LIMIT)
        handle_quota_check(quota_table, user_id, today_date, USER_REQUEST_LIMIT)
        return None  # Cuotas OK
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Determinar si fue cuota global o de usuario
            # (esto es una heurística, podría mejorarse)
            if GLOBAL_USER_ID in str(e.response):
                return build_error_response(
                    429,
                    'Global Quota Exceeded',
                    f'Se superó el límite global de {GLOBAL_REQUEST_LIMIT} solicitudes.'
                )
            else:
                # Fue cuota de usuario, revertir la global
                revert_global_quota(quota_table, today_date)
                return build_error_response(
                    429,
                    'User Quota Exceeded',
                    f'Has superado tu límite diario de {USER_REQUEST_LIMIT} solicitudes.'
                )
        raise


def get_quota_table():
    """
    Retorna la tabla de DynamoDB para cuotas.
    
    Returns:
        Table: Recurso de tabla DynamoDB
    """
    return dynamodb.Table(QUOTA_TABLE_NAME)

