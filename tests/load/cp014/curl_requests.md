# CP014 - Curl Requests y Respuestas Esperadas

## Caso de Prueba: Verificar la autorización para ver los resultados del cuestionario tomado por un usuario

### Datos de Prueba
- **Usuario:** test@ovotest.com
- **Password:** testPass123456!@#
- **Rol:** Estudiante
- **Endpoint:** GET /user/tests
- **Base URL:** http://localhost:8000

---

## Escenario 1: Acceso Denegado (403 Forbidden)

### Request sin autenticación

```bash
curl -X GET "http://localhost:8000/user/tests" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado. Se requiere autenticación.",
  "code": "FORBIDDEN",
  "message": "No se proporcionó token de autenticación o el token es inválido.",
  "timestamp": "2024-11-23 21:30:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 156
```

---

## Escenario 2: Acceso Autorizado (200 OK)

### Paso 1: Autenticación del usuario Estudiante

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test@ovotest.com",
    "password": "testPass123456!@#"
  }' \
  -v
```

### Respuesta de Autenticación (200 OK)

```json
{
  "success": true,
  "message": "Autenticación exitosa",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwfQ.abc123def456",
  "user": {
    "id": "test",
    "email": "test@ovotest.com",
    "rol": "Estudiante"
  },
  "expiresIn": 3600,
  "timestamp": "2024-11-23 21:30:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245
```

### Paso 2: Obtener resultados del test (con token)

```bash
curl -X GET "http://localhost:8000/user/tests" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwfQ.abc123def456" \
  -v
```

### Respuesta Esperada (200 OK) - Con resultados

```json
{
  "success": true,
  "message": "Resultados obtenidos exitosamente",
  "userId": "test",
  "tests": [
    {
      "testId": "test_1234",
      "fechaCompletado": "2024-11-20 15:30:00",
      "estado": "completado",
      "aptitudesEvaluadas": {
        "Lógica matemática": 87.5,
        "Pensamiento analítico": 92.3,
        "Creatividad": 78.9,
        "Comunicación": 85.2,
        "Trabajo en equipo": 90.1,
        "Liderazgo": 76.4,
        "Organización": 88.7
      },
      "carrerasRecomendadas": [
        {
          "nombre": "Ingeniería en Sistemas",
          "match": 91.5,
          "razones": [
            "Alta afinidad con lógica matemática",
            "Excelentes habilidades analíticas"
          ]
        },
        {
          "nombre": "Ingeniería Industrial",
          "match": 85.2,
          "razones": [
            "Habilidades organizativas destacadas",
            "Pensamiento sistémico desarrollado"
          ]
        },
        {
          "nombre": "Ingeniería Química",
          "match": 78.9,
          "razones": [
            "Atención al detalle",
            "Capacidad analítica"
          ]
        }
      ],
      "resumen": {
        "aptitudDominante": "Pensamiento analítico",
        "puntajePromedio": 85.6,
        "totalAptitudes": 7
      }
    }
  ],
  "totalTests": 1,
  "timestamp": "2024-11-23 21:30:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 892
```

### Respuesta Esperada (200 OK) - Sin tests completados

Si el usuario no tiene tests completados, la respuesta sería:

```json
{
  "success": true,
  "message": "No se encontraron tests completados para este usuario",
  "userId": "test",
  "tests": [],
  "totalTests": 0,
  "timestamp": "2024-11-23 21:30:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 145
```

---

## Escenario 3: Token Inválido o Expirado (401 Unauthorized)

### Request con token inválido

```bash
curl -X GET "http://localhost:8000/user/tests" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer token_invalido_o_expirado" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido o expirado",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación proporcionado no es válido o ha expirado.",
  "timestamp": "2024-11-23 21:30:20"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 4: Intento de acceso a resultados de otro usuario (403 Forbidden)

### Request con token válido pero intentando acceder a otro usuario

Si el sistema detecta que el usuario intenta acceder a resultados que no le pertenecen:

```bash
curl -X GET "http://localhost:8000/user/tests?userId=otro_usuario" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwfQ.abc123def456" \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos para acceder a los resultados de otro usuario. Solo puede ver sus propios resultados.",
  "timestamp": "2024-11-23 21:30:25"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 198
```

---

## Notas de Implementación

1. **Autenticación:** El sistema debe validar el token JWT en el header `Authorization: Bearer <token>`

2. **Autorización:** El sistema debe verificar que:
   - El usuario esté autenticado (token válido)
   - El usuario solo pueda ver sus propios resultados (no los de otros usuarios)
   - El rol del usuario tenga permisos para acceder al endpoint

3. **Auditoría:** Todos los intentos de acceso denegado (403) deben registrarse en el sistema de auditoría con:
   - Timestamp
   - Usuario (si está autenticado)
   - IP de origen
   - Endpoint intentado
   - Razón de denegación

4. **Respuestas:** Las respuestas exitosas (200) deben incluir solo los tests completados por el usuario autenticado, identificado por el token JWT.

