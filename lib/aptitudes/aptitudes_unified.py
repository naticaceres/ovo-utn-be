import json
import boto3
from botocore.exceptions import ClientError

# Configuración
APTITUDES_TABLE_NAME = 'AptitudesTable'
MAX_APTITUD_LENGTH = 200
MAX_APTITUDES_PER_REQUEST = 50
REGION_NAME = 'us-east-2'

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)

def handler(event, context):
    """
    Lambda unificada para gestionar aptitudes
    Endpoints:
    - POST /aptitudes/agregar
    - PUT /aptitudes/editar
    - DELETE /aptitudes/eliminar
    - GET /aptitudes/listar
    """
    try:
        # 1. Determinar la operación basada en el path
        path = event.get('path', '')
        method = event.get('httpMethod', '')
        
        if method == 'POST' and '/agregar' in path:
            return agregar_aptitudes(event, context)
        elif method == 'PUT' and '/editar' in path:
            return editar_aptitudes(event, context)
        elif method == 'DELETE' and '/eliminar' in path:
            return eliminar_aptitudes(event, context)
        elif method == 'GET' and '/listar' in path:
            return listar_aptitudes(event, context)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': 'Endpoint no encontrado'
                })
            }
            
    except Exception as e:
        print(f"Error inesperado: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Error interno del servidor'
            })
        }

def agregar_aptitudes(event, context):
    """Agregar nuevas aptitudes (solo las que no existen)"""
    body = json.loads(event.get('body', '{}'))
    
    # Manejar tanto array directo como objeto con propiedad aptitudes
    if isinstance(body, list):
        aptitudes = body
    else:
        aptitudes = body.get('aptitudes', [])
    
    # Validaciones
    if not aptitudes or not isinstance(aptitudes, list):
        return error_response(400, 'El campo "aptitudes" debe ser un array de strings')
    
    if len(aptitudes) > MAX_APTITUDES_PER_REQUEST:
        return error_response(400, f'No se pueden procesar más de {MAX_APTITUDES_PER_REQUEST} aptitudes por request')
    
    # Procesar aptitudes
    aptitudes_validas = validar_aptitudes(aptitudes)
    if not aptitudes_validas:
        return error_response(400, 'No se encontraron aptitudes válidas para procesar')
    
    table = dynamodb.Table(APTITUDES_TABLE_NAME)
    aptitudes_agregadas = []
    aptitudes_existentes = []
    
    for aptitud in aptitudes_validas:
        try:
            table.put_item(
                Item={
                    'aptitud': aptitud,
                    'fecha_creacion': context.aws_request_id,
                    'activa': True
                },
                ConditionExpression='attribute_not_exists(aptitud)'
            )
            aptitudes_agregadas.append(aptitud)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                aptitudes_existentes.append(aptitud)
    
    return success_response({
        'operacion': 'agregar',
        'aptitudes_recibidas': len(aptitudes),
        'aptitudes_validas': len(aptitudes_validas),
        'aptitudes_agregadas': len(aptitudes_agregadas),
        'aptitudes_existentes': len(aptitudes_existentes),
        'detalle_agregadas': aptitudes_agregadas,
        'detalle_existentes': aptitudes_existentes
    })

def editar_aptitudes(event, context):
    """Reemplazar todas las aptitudes (eliminar existentes y agregar nuevas)"""
    body = json.loads(event.get('body', '{}'))
    
    # Manejar tanto array directo como objeto con propiedad aptitudes
    if isinstance(body, list):
        aptitudes = body
    else:
        aptitudes = body.get('aptitudes', [])
    
    # Validaciones
    if not aptitudes or not isinstance(aptitudes, list):
        return error_response(400, 'El campo "aptitudes" debe ser un array de strings')
    
    if len(aptitudes) > MAX_APTITUDES_PER_REQUEST:
        return error_response(400, f'No se pueden procesar más de {MAX_APTITUDES_PER_REQUEST} aptitudes por request')
    
    aptitudes_validas = validar_aptitudes(aptitudes)
    if not aptitudes_validas:
        return error_response(400, 'No se encontraron aptitudes válidas para procesar')
    
    table = dynamodb.Table(APTITUDES_TABLE_NAME)
    
    try:
        # 1. Eliminar todas las aptitudes existentes
        response = table.scan()
        for item in response['Items']:
            table.delete_item(Key={'aptitud': item['aptitud']})
        
        # 2. Agregar las nuevas aptitudes
        for aptitud in aptitudes_validas:
            table.put_item(
                Item={
                    'aptitud': aptitud,
                    'fecha_creacion': context.aws_request_id,
                    'activa': True
                }
            )
        
        return success_response({
            'operacion': 'editar',
            'aptitudes_recibidas': len(aptitudes),
            'aptitudes_validas': len(aptitudes_validas),
            'aptitudes_procesadas': len(aptitudes_validas),
            'detalle_procesadas': aptitudes_validas
        })
        
    except Exception as e:
        return error_response(500, f'Error al editar aptitudes: {str(e)}')

def eliminar_aptitudes(event, context):
    """Eliminar aptitudes específicas"""
    body = json.loads(event.get('body', '{}'))
    
    # Manejar tanto array directo como objeto con propiedad aptitudes
    if isinstance(body, list):
        aptitudes = body
    else:
        aptitudes = body.get('aptitudes', [])
    
    if not aptitudes or not isinstance(aptitudes, list):
        return error_response(400, 'El campo "aptitudes" debe ser un array de strings')
    
    if len(aptitudes) > MAX_APTITUDES_PER_REQUEST:
        return error_response(400, f'No se pueden procesar más de {MAX_APTITUDES_PER_REQUEST} aptitudes por request')
    
    aptitudes_validas = validar_aptitudes(aptitudes)
    if not aptitudes_validas:
        return error_response(400, 'No se encontraron aptitudes válidas para procesar')
    
    table = dynamodb.Table(APTITUDES_TABLE_NAME)
    aptitudes_eliminadas = []
    aptitudes_no_encontradas = []
    
    for aptitud in aptitudes_validas:
        try:
            response = table.delete_item(
                Key={'aptitud': aptitud},
                ReturnValues='ALL_OLD'
            )
            if 'Attributes' in response:
                aptitudes_eliminadas.append(aptitud)
            else:
                aptitudes_no_encontradas.append(aptitud)
        except Exception as e:
            aptitudes_no_encontradas.append(aptitud)
    
    return success_response({
        'operacion': 'eliminar',
        'aptitudes_recibidas': len(aptitudes),
        'aptitudes_validas': len(aptitudes_validas),
        'aptitudes_eliminadas': len(aptitudes_eliminadas),
        'aptitudes_no_encontradas': len(aptitudes_no_encontradas),
        'detalle_eliminadas': aptitudes_eliminadas,
        'detalle_no_encontradas': aptitudes_no_encontradas
    })

def listar_aptitudes(event, context):
    """Listar todas las aptitudes existentes"""
    try:
        table = dynamodb.Table(APTITUDES_TABLE_NAME)
        response = table.scan(
            FilterExpression='activa = :activa',
            ExpressionAttributeValues={':activa': True}
        )
        
        aptitudes = [item['aptitud'] for item in response['Items']]
        
        return success_response({
            'operacion': 'listar',
            'total_aptitudes': len(aptitudes),
            'aptitudes': aptitudes
        })
        
    except Exception as e:
        return error_response(500, f'Error al listar aptitudes: {str(e)}')

def validar_aptitudes(aptitudes):
    """Validar y limpiar lista de aptitudes"""
    aptitudes_validas = []
    for aptitud in aptitudes:
        if not isinstance(aptitud, str):
            continue
        
        aptitud_clean = aptitud.strip()
        if not aptitud_clean or len(aptitud_clean) > MAX_APTITUD_LENGTH:
            continue
        
        aptitudes_validas.append(aptitud_clean)
    
    return aptitudes_validas

def success_response(data):
    """Respuesta exitosa"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(data)
    }

def error_response(status_code, message):
    """Respuesta de error"""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'error': 'Bad Request' if status_code == 400 else 'Internal Server Error',
            'message': message
        })
    }
