# CP015 - Curl Requests y Respuestas Esperadas

## Caso de Prueba: Verificar la autorización para ver la configuración de Parámetros Generales del administrador

### Datos de Prueba
- **Usuario Estudiante:**
  - Email: test@ovotest.com
  - Password: testPass123456!@#
  - Rol: Estudiante
- **Usuario Administrador:**
  - Email: admintest@ovotest.com
  - Password: testPass123456!@#
  - Rol: Administrador
- **Endpoint:** GET /admin/catalog/genders
- **Base URL:** http://localhost:8000

---

## Escenario 1: Acceso Denegado - Sin Autenticación (403 Forbidden)

### Request sin autenticación

```bash
curl -X GET "http://localhost:8000/admin/catalog/genders" \
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
  "timestamp": "2024-11-23 22:00:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 156
```

---

## Escenario 2: Acceso Denegado - Usuario Estudiante (403 Forbidden)

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123",
  "user": {
    "id": "test",
    "email": "test@ovotest.com",
    "rol": "Estudiante"
  },
  "expiresIn": 3600,
  "timestamp": "2024-11-23 22:00:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245
```

### Paso 2: Intento de acceso a configuración de administrador (con token de Estudiante)

```bash
curl -X GET "http://localhost:8000/admin/catalog/genders" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123" \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para acceder a este recurso. Se requiere rol de Administrador.",
  "requiredRole": "Administrador",
  "currentRole": "Estudiante",
  "timestamp": "2024-11-23 22:00:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 245
```

---

## Escenario 3: Acceso Autorizado - Usuario Administrador (200 OK)

### Paso 1: Autenticación del usuario Administrador

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "admintest@ovotest.com",
    "password": "testPass123456!@#"
  }' \
  -v
```

### Respuesta de Autenticación (200 OK)

```json
{
  "success": true,
  "message": "Autenticación exitosa",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbnRlc3QiLCJ6ZW1haWwiOiJhZG1pbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwiaWF0IjoxNzMyMzQ1ODAwLCJleHAiOjE3MzIzNDk0MDB9.admin456def789",
  "user": {
    "id": "admintest",
    "email": "admintest@ovotest.com",
    "rol": "Administrador"
  },
  "expiresIn": 3600,
  "timestamp": "2024-11-23 22:00:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 265
```

### Paso 2: Obtener configuración de Parámetros Generales (con token de Administrador)

```bash
curl -X GET "http://localhost:8000/admin/catalog/genders" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbnRlc3QiLCJ6ZW1haWwiOiJhZG1pbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwiaWF0IjoxNzMyMzQ1ODAwLCJleHAiOjE3MzIzNDk0MDB9.admin456def789" \
  -v
```

### Respuesta Esperada (200 OK) - Con configuración de géneros

```json
{
  "success": true,
  "message": "Configuración obtenida exitosamente",
  "catalog": {
    "type": "genders",
    "name": "Géneros",
    "description": "Catálogo de géneros disponibles en el sistema",
    "items": [
      {
        "id": 1,
        "code": "M",
        "name": "Masculino",
        "description": "Género masculino",
        "active": true,
        "order": 1
      },
      {
        "id": 2,
        "code": "F",
        "name": "Femenino",
        "description": "Género femenino",
        "active": true,
        "order": 2
      },
      {
        "id": 3,
        "code": "O",
        "name": "Otro",
        "description": "Otro género",
        "active": true,
        "order": 3
      },
      {
        "id": 4,
        "code": "PND",
        "name": "Prefiero no decir",
        "description": "Prefiero no especificar",
        "active": true,
        "order": 4
      }
    ],
    "totalItems": 4,
    "activeItems": 4
  },
  "metadata": {
    "lastUpdated": "2024-11-20 10:30:00",
    "updatedBy": "admin@ovotest.com",
    "version": "1.2.0"
  },
  "timestamp": "2024-11-23 22:00:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 892
```

### Respuesta Esperada (200 OK) - Catálogo vacío

Si el catálogo no tiene elementos configurados:

```json
{
  "success": true,
  "message": "Configuración obtenida exitosamente",
  "catalog": {
    "type": "genders",
    "name": "Géneros",
    "description": "Catálogo de géneros disponibles en el sistema",
    "items": [],
    "totalItems": 0,
    "activeItems": 0
  },
  "metadata": {
    "lastUpdated": null,
    "updatedBy": null,
    "version": "1.0.0"
  },
  "timestamp": "2024-11-23 22:00:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245
```

---

## Escenario 4: Token Inválido o Expirado (401 Unauthorized)

### Request con token inválido

```bash
curl -X GET "http://localhost:8000/admin/catalog/genders" \
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
  "timestamp": "2024-11-23 22:01:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 5: Acceso con Rol Intermedio (403 Forbidden)

### Ejemplo: Usuario con rol "Institución" intentando acceder

Si un usuario con rol "Institución" (que no es Administrador) intenta acceder:

```bash
curl -X GET "http://localhost:8000/admin/catalog/genders" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbiIsInJvbCI6Ikluc3RpdHVjaW9uIiwiaWF0IjoxNzMyMzQ1ODAwLCJleHAiOjE3MzIzNDk0MDB9.institucion123" \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para acceder a este recurso. Se requiere rol de Administrador.",
  "requiredRole": "Administrador",
  "currentRole": "Institución",
  "timestamp": "2024-11-23 22:01:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 245
```

---

## Notas de Implementación

1. **Autenticación:** El sistema debe validar el token JWT en el header `Authorization: Bearer <token>`

2. **Autorización RBAC:** El sistema debe verificar que:
   - El usuario esté autenticado (token válido)
   - El rol del usuario sea "Administrador" para acceder a endpoints `/admin/*`
   - Cualquier otro rol (Estudiante, Institución, etc.) debe recibir 403 Forbidden

3. **Auditoría:** Todos los intentos de acceso denegado (403) deben registrarse en el sistema de auditoría con:
   - Timestamp
   - Usuario (si está autenticado)
   - Rol del usuario
   - IP de origen
   - Endpoint intentado
   - Razón de denegación (rol insuficiente, falta de autenticación, etc.)

4. **Respuestas:** Las respuestas exitosas (200) deben incluir:
   - La estructura completa del catálogo solicitado
   - Metadatos sobre la última actualización
   - Información sobre el total de items y items activos

5. **Estructura del Catálogo:** El endpoint `/admin/catalog/genders` debe retornar:
   - Lista de items con código, nombre, descripción
   - Estado activo/inactivo de cada item
   - Orden de visualización
   - Metadatos de versión y actualización

