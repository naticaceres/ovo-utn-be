#!/usr/bin/env python3
"""
Script para probar las protecciones de la API
"""
import requests
import time
import json

API_URL = "https://8qvyqx6px1.execute-api.us-east-2.amazonaws.com/prod/"

def test_without_api_key():
    """Probar la API sin API Key (debería funcionar pero con throttling)"""
    print("🔓 Probando API sin API Key...")
    
    try:
        response = requests.get(API_URL)
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_throttling():
    """Probar throttling enviando muchas requests rápidamente"""
    print("\n🚀 Probando throttling (enviando 10 requests rápidas)...")
    
    responses = []
    for i in range(10):
        try:
            response = requests.get(API_URL)
            responses.append({
                'request': i+1,
                'status': response.status_code,
                'headers': dict(response.headers)
            })
            print(f"Request {i+1}: Status {response.status_code}")
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")
        
        # Pequeña pausa para no saturar
        time.sleep(0.1)
    
    # Analizar respuestas
    success_count = sum(1 for r in responses if r['status'] == 200)
    throttled_count = sum(1 for r in responses if r['status'] == 429)
    
    print(f"\n📈 Resultados:")
    print(f"  - Requests exitosos: {success_count}")
    print(f"  - Requests throttled: {throttled_count}")
    
    if throttled_count > 0:
        print("🛡️ ¡Throttling funcionando! Algunas requests fueron limitadas.")
    else:
        print("⚠️ No se detectó throttling. Puede que necesites más requests o el límite sea más alto.")

def test_with_api_key():
    """Probar con API Key (necesitarás obtener la key desde AWS Console)"""
    print("\n🔑 Para probar con API Key:")
    print("1. Ve a AWS Console → API Gateway → API Keys")
    print("2. Busca la key con ID: cwcdjloigk")
    print("3. Copia el valor de la API Key")
    print("4. Usa este comando:")
    print("   curl -H 'x-api-key: TU_API_KEY_AQUI' https://8qvyqx6px1.execute-api.us-east-2.amazonaws.com/prod/")

def main():
    print("🛡️ PROBANDO PROTECCIONES DE LA API")
    print("=" * 50)
    
    # Test básico
    test_without_api_key()
    
    # Test de throttling
    test_throttling()
    
    # Instrucciones para API Key
    test_with_api_key()
    
    print("\n📋 RESUMEN DE PROTECCIONES ACTIVAS:")
    print("✅ Throttling: 50 requests/segundo, burst de 100")
    print("✅ Quota: 5,000 requests por día")
    print("✅ API Key: Requerida para acceso completo")
    print("✅ CloudWatch Logs: Monitoreo automático")

if __name__ == "__main__":
    main()
