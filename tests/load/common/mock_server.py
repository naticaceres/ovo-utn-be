#!/usr/bin/env python3

import random
import time
import hashlib
import base64
import csv
import io
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

request_count = 0
active_sessions = {}


def simulate_processing_time(min_time, max_time, distribution=None):
    if distribution == "fast":
        rand = random.random()
        if rand < 0.70:
            return random.uniform(min_time, (min_time + max_time) / 2)
        else:
            return random.uniform((min_time + max_time) / 2, max_time)
    else:
        rand = random.random()
        if rand < 0.20:
            return random.uniform(min_time, min_time + (max_time - min_time) * 0.2)
        elif rand < 0.80:
            return random.uniform(min_time + (max_time - min_time) * 0.2, min_time + (max_time - min_time) * 0.6)
        elif rand < 0.95:
            return random.uniform(min_time + (max_time - min_time) * 0.6, min_time + (max_time - min_time) * 0.9)
        else:
            return random.uniform(min_time + (max_time - min_time) * 0.9, max_time)


def generate_mock_dashboard_data(tipo_carrera, fecha_desde, fecha_hasta):
    base_count = random.randint(50, 200)
    
    return {
        "success": True,
        "filtros": {
            "tipoCarrera": tipo_carrera,
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta
        },
        "estadisticas": {
            "totalEstudiantes": base_count * 10,
            "totalTests": base_count * 5,
            "totalInstituciones": random.randint(5, 20),
            "totalCarreras": random.randint(10, 50)
        },
        "distribucionPorCarrera": [
            {
                "carrera": "Ingeniería en Sistemas",
                "cantidad": random.randint(20, 100),
                "porcentaje": round(random.uniform(15.0, 25.0), 2)
            },
            {
                "carrera": "Ingeniería Industrial",
                "cantidad": random.randint(15, 80),
                "porcentaje": round(random.uniform(10.0, 20.0), 2)
            },
            {
                "carrera": "Ingeniería Química",
                "cantidad": random.randint(10, 60),
                "porcentaje": round(random.uniform(8.0, 15.0), 2)
            },
            {
                "carrera": "Ingeniería Civil",
                "cantidad": random.randint(12, 70),
                "porcentaje": round(random.uniform(9.0, 18.0), 2)
            }
        ],
        "tendencias": {
            "crecimientoMensual": round(random.uniform(-5.0, 15.0), 2),
            "tendenciaSemanal": round(random.uniform(-2.0, 8.0), 2)
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }


def generate_jwt_token(user_id, email):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    
    header_b64 = base64.urlsafe_b64encode(str(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(str(payload).encode()).decode().rstrip('=')
    
    signature = hashlib.sha256(f"{header_b64}.{payload_b64}".encode()).hexdigest()[:32]
    token = f"{header_b64}.{payload_b64}.{signature}"
    
    return token


def generate_mock_test_report(test_id, user_id):
    aptitudes = [
        "Lógica matemática", "Pensamiento analítico", "Creatividad",
        "Comunicación", "Trabajo en equipo", "Liderazgo", "Organización",
        "Resolución de problemas", "Adaptabilidad", "Persistencia"
    ]
    
    selected_aptitudes = random.sample(aptitudes, random.randint(5, 8))
    scores = {apt: round(random.uniform(60.0, 95.0), 2) for apt in selected_aptitudes}
    
    carreras_recomendadas = [
        {
            "nombre": "Ingeniería en Sistemas",
            "match": round(random.uniform(75.0, 95.0), 2),
            "razones": ["Alta afinidad con lógica", "Buenas habilidades analíticas"]
        },
        {
            "nombre": "Ingeniería Industrial",
            "match": round(random.uniform(70.0, 90.0), 2),
            "razones": ["Habilidades organizativas", "Pensamiento sistémico"]
        },
        {
            "nombre": "Ingeniería Química",
            "match": round(random.uniform(65.0, 85.0), 2),
            "razones": ["Atención al detalle", "Capacidad analítica"]
        }
    ]
    
    return {
        "success": True,
        "testId": test_id,
        "userId": user_id,
        "fechaCompletado": time.strftime("%Y-%m-%d %H:%M:%S"),
        "aptitudesEvaluadas": scores,
        "carrerasRecomendadas": sorted(carreras_recomendadas, key=lambda x: x["match"], reverse=True),
        "resumen": {
            "aptitudDominante": max(scores, key=scores.get),
            "puntajePromedio": round(sum(scores.values()) / len(scores), 2),
            "totalAptitudes": len(scores)
        }
    }


@app.route('/api/dashboard/search', methods=['GET'])
def dashboard_search():
    global request_count
    request_count += 1
    
    tipo_carrera = request.args.get('tipoCarrera', 'Todas')
    fecha_desde = request.args.get('fechaDesde', '01/01/2024')
    fecha_hasta = request.args.get('fechaHasta', '31/12/2024')
    
    logger.info(f"Request #{request_count} - Dashboard Search - tipoCarrera={tipo_carrera}")
    
    delay = simulate_processing_time(1.0, 10.0)
    logger.info(f"Request #{request_count} - Simulando {delay:.2f}s de procesamiento")
    time.sleep(delay)
    
    data = generate_mock_dashboard_data(tipo_carrera, fecha_desde, fecha_hasta)
    logger.info(f"Request #{request_count} - Respondiendo exitosamente")
    
    return jsonify(data), 200


@app.route('/api/tests/finish', methods=['POST'])
def test_finish():
    global request_count
    request_count += 1
    
    data = request.get_json() or {}
    test_id = data.get('testId', f'test_{random.randint(1000, 9999)}')
    user_id = data.get('userId', f'user_{random.randint(100, 999)}')
    respuestas = data.get('respuestas', {})
    
    logger.info(f"Request #{request_count} - Test Finish - testId={test_id}, userId={user_id}")
    
    delay = simulate_processing_time(0.5, 3.0, "fast")
    logger.info(f"Request #{request_count} - Simulando persistencia {delay:.2f}s")
    time.sleep(delay)
    
    response_data = {
        "success": True,
        "testId": test_id,
        "userId": user_id,
        "mensaje": "Test finalizado y respuestas guardadas exitosamente",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "totalRespuestas": len(respuestas)
    }
    
    logger.info(f"Request #{request_count} - Persistencia completada")
    return jsonify(response_data), 200


@app.route('/api/tests/report', methods=['GET'])
def test_report():
    global request_count
    request_count += 1
    
    test_id = request.args.get('testId', f'test_{random.randint(1000, 9999)}')
    user_id = request.args.get('userId', f'user_{random.randint(100, 999)}')
    
    logger.info(f"Request #{request_count} - Test Report - testId={test_id}, userId={user_id}")
    
    delay = simulate_processing_time(1.0, 6.0, "fast")
    logger.info(f"Request #{request_count} - Simulando generación de informe {delay:.2f}s")
    time.sleep(delay)
    
    data = generate_mock_test_report(test_id, user_id)
    logger.info(f"Request #{request_count} - Informe generado exitosamente")
    
    return jsonify(data), 200


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    global request_count, active_sessions
    request_count += 1
    
    data = request.get_json() or {}
    email = data.get('email', '')
    password = data.get('password', '')
    
    logger.info(f"Request #{request_count} - Auth Login - email={email}")
    
    if not email or not password:
        logger.warning(f"Request #{request_count} - Credenciales faltantes")
        return jsonify({
            "success": False,
            "error": "Email y password son requeridos"
        }), 400
    
    if password != "password123":
        logger.warning(f"Request #{request_count} - Password incorrecto")
        return jsonify({
            "success": False,
            "error": "Credenciales inválidas"
        }), 401
    
    delay = simulate_processing_time(1.0, 6.0, "fast")
    logger.info(f"Request #{request_count} - Simulando autenticación {delay:.2f}s")
    time.sleep(delay)
    
    user_id = email.split('@')[0] if '@' in email else f"user_{random.randint(100, 999)}"
    token = generate_jwt_token(user_id, email)
    
    session_data = {
        "userId": user_id,
        "email": email,
        "token": token,
        "createdAt": time.time()
    }
    active_sessions[token] = session_data
    
    response_data = {
        "success": True,
        "message": "Autenticación exitosa",
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
            "rol": random.choice(["Estudiante", "Institución", "Administrador"])
        },
        "expiresIn": 3600,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    logger.info(f"Request #{request_count} - Login exitoso, token generado")
    return jsonify(response_data), 200


@app.route('/api/auth/validate', methods=['GET'])
def auth_validate():
    global request_count, active_sessions
    request_count += 1
    
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({
            "success": False,
            "error": "Token no proporcionado"
        }), 401
    
    if token in active_sessions:
        session = active_sessions[token]
        return jsonify({
            "success": True,
            "valid": True,
            "user": {
                "id": session["userId"],
                "email": session["email"]
            }
        }), 200
    else:
        return jsonify({
            "success": False,
            "valid": False,
            "error": "Token inválido o expirado"
        }), 401


def generate_report_data(institucion_id, fecha_desde, fecha_hasta, record_count=100):
    carreras = [
        "Ingeniería en Sistemas", "Ingeniería Industrial", "Ingeniería Química",
        "Ingeniería Civil", "Ingeniería Mecánica", "Ingeniería Eléctrica"
    ]
    
    datos = []
    for i in range(record_count):
        datos.append({
            "id": i + 1,
            "estudiante": f"Estudiante {i + 1}",
            "email": f"estudiante{i+1}@ejemplo.com",
            "carrera": random.choice(carreras),
            "fechaTest": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "puntajeTotal": round(random.uniform(60.0, 100.0), 2),
            "aptitudDominante": random.choice(["Lógica", "Creatividad", "Comunicación", "Liderazgo"]),
            "estado": random.choice(["Completado", "En progreso", "Pendiente"])
        })
    
    return datos


@app.route('/api/reportes/export', methods=['GET'])
def reportes_export():
    global request_count
    request_count += 1
    
    formato = request.args.get('formato', 'csv').lower()
    institucion_id = request.args.get('institucionId', '123')
    fecha_desde = request.args.get('fechaDesde', '01/01/2024')
    fecha_hasta = request.args.get('fechaHasta', '31/12/2024')
    
    record_count = min(int(request.args.get('registros', 100)), 10000)
    
    logger.info(
        f"Request #{request_count} - Reportes Export - "
        f"formato={formato}, institucionId={institucion_id}, registros={record_count}"
    )
    
    delay = simulate_processing_time(5.0, 15.0, "fast")
    logger.info(f"Request #{request_count} - Simulando generación de reporte {delay:.2f}s")
    time.sleep(delay)
    
    datos = generate_report_data(institucion_id, fecha_desde, fecha_hasta, record_count)
    
    if formato == 'csv':
        output = io.StringIO()
        if datos:
            writer = csv.DictWriter(output, fieldnames=datos[0].keys())
            writer.writeheader()
            writer.writerows(datos)
        
        csv_content = output.getvalue()
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=reporte_institucion_{institucion_id}_{time.strftime("%Y%m%d")}.csv'
            }
        )
        logger.info(f"Request #{request_count} - Reporte CSV generado con {len(datos)} registros")
        return response, 200
    
    elif formato == 'json':
        response_data = {
            "success": True,
            "institucionId": institucion_id,
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta,
            "totalRegistros": len(datos),
            "fechaGeneracion": time.strftime("%Y-%m-%d %H:%M:%S"),
            "datos": datos
        }
        logger.info(f"Request #{request_count} - Reporte JSON generado con {len(datos)} registros")
        return jsonify(response_data), 200
    
    else:
        return jsonify({
            "success": False,
            "error": f"Formato no soportado: {formato}. Use 'csv' o 'json'"
        }), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "mock-server",
        "total_requests": request_count,
        "active_sessions": len(active_sessions),
        "endpoints": [
            "/api/dashboard/search",
            "/api/tests/finish",
            "/api/tests/report",
            "/api/auth/login",
            "/api/auth/validate",
            "/api/reportes/export"
        ]
    }), 200


@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        "total_requests": request_count,
        "status": "running"
    }), 200


if __name__ == '__main__':
    port = 8000
    logger.info(f"🚀 Iniciando servidor mock en http://localhost:{port}")
    logger.info(f"📊 Endpoints disponibles:")
    logger.info(f"   GET  /api/dashboard/search")
    logger.info(f"   POST /api/tests/finish")
    logger.info(f"   GET  /api/tests/report")
    logger.info(f"   POST /api/auth/login")
    logger.info(f"   GET  /api/auth/validate")
    logger.info(f"   GET  /api/reportes/export")
    logger.info(f"   GET  /health")
    logger.info("")
    logger.info("Presiona Ctrl+C para detener el servidor")
    logger.info("")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )

