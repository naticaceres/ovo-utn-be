#!/usr/bin/env python3
"""
Script para obtener la API Key de AWS API Gateway
"""
import boto3
import sys

def get_api_key():
    try:
        # Crear cliente de API Gateway
        apigateway = boto3.client('apigateway', region_name='us-east-2')
        
        # Obtener la API Key
        api_key_id = 'cwcdjloigk'  # ID de la API Key del output
        
        response = apigateway.get_api_key(
            apiKey=api_key_id,
            includeValue=True
        )
        
        api_key_value = response['value']
        
        print("🔑 API Key obtenida exitosamente:")
        print(f"API Key ID: {api_key_id}")
        print(f"API Key Value: {api_key_value}")
        print()
        print("📋 Cómo usar la API Key:")
        print("1. Para requests con API Key:")
        print(f"   curl -H 'x-api-key: {api_key_value}' https://8qvyqx6px1.execute-api.us-east-2.amazonaws.com/prod/")
        print()
        print("2. Para requests sin API Key (serán limitados):")
        print("   curl https://8qvyqx6px1.execute-api.us-east-2.amazonaws.com/prod/")
        print()
        print("🛡️ Protecciones activas:")
        print("- Throttling: 50 requests/segundo, burst de 100")
        print("- Quota: 5,000 requests por día")
        print("- API Key requerida para acceso completo")
        
        return api_key_value
        
    except Exception as e:
        print(f"❌ Error obteniendo API Key: {e}")
        return None

if __name__ == "__main__":
    get_api_key()
