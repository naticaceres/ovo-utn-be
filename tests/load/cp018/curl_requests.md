# CP018 - Curl Requests y Respuestas Esperadas

## Caso de Prueba: Validación de tokens y gestión de sesiones

### Datos de Prueba
- **Usuario Estudiante:**
  - Email: test@ovotest.com
  - Password: testPass123456!@#
  - Rol: Estudiante
- **Configuración de Token:**
  - Tiempo de expiración: 1 hora (3600 segundos)
  - Algoritmo: HS256
- **Endpoints:**
  - GET /api/usuario/perfil (recurso protegido)
  - POST /api/auth/logout (revocación de sesión)
  - POST /api/auth/revoke (revocación de token)
  - POST /api/auth/refresh (rotación de token)
- **Base URL:** http://localhost:8000

---

## Escenario 1: Token Válido - Acceso Autorizado (200 OK)

### Paso 1: Iniciar sesión y obtener token JWT válido

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM1MTQwMH0.refresh_signature",
  "user": {
    "id": "test",
    "email": "test@ovotest.com",
    "rol": "Estudiante"
  },
  "expiresIn": 3600,
  "tokenType": "Bearer",
  "timestamp": "2024-11-23 23:30:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 385
```

### Paso 2: Usar el token para acceder a recursos protegidos

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here" \
  -v
```

### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Datos del perfil obtenidos exitosamente",
  "usuario": {
    "id": "test",
    "email": "test@ovotest.com",
    "nombre": "Usuario",
    "apellido": "Prueba",
    "rol": "Estudiante",
    "fechaRegistro": "2024-01-15",
    "ultimoAcceso": "2024-11-23 23:30:15",
    "estado": "activo",
    "preferencias": {
      "notificaciones": true,
      "idioma": "es"
    }
  },
  "timestamp": "2024-11-23 23:30:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 345
```

---

## Escenario 2: Token Expirado - Acceso Denegado (401 Unauthorized)

### Request con token expirado

**Nota:** Este token tiene un `exp` (expiración) en el pasado. En la práctica, el token expiraría después de 1 hora desde su emisión.

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0NTgwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.expired_signature" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token expirado",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación ha expirado. Por favor, inicie sesión nuevamente.",
  "errorCode": "TOKEN_EXPIRED",
  "expiredAt": "2024-11-23 22:30:00",
  "currentTime": "2024-11-23 23:30:30",
  "timestamp": "2024-11-23 23:30:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Token expired"
Content-Length: 298
```

---

## Escenario 3: Token Alterado o Inválido - Acceso Denegado (401 Unauthorized)

### Request con token alterado (firma modificada)

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.ALTERED_INVALID_SIGNATURE" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación proporcionado no es válido. La firma del token no coincide.",
  "errorCode": "TOKEN_INVALID",
  "timestamp": "2024-11-23 23:30:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Invalid token signature"
Content-Length: 245
```

---

### Request con token malformado (formato incorrecto)

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer token_malformado_sin_formato_jwt" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido",
  "code": "UNAUTHORIZED",
  "message": "El formato del token de autenticación no es válido. Se espera un token JWT.",
  "errorCode": "TOKEN_MALFORMED",
  "timestamp": "2024-11-23 23:31:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Malformed token"
Content-Length: 245
```

---

### Request con token sin firma (solo header y payload)

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUifQ" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación no tiene una firma válida.",
  "errorCode": "TOKEN_INVALID",
  "timestamp": "2024-11-23 23:31:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Token missing signature"
Content-Length: 198
```

---

## Escenario 4: Token Revocado Manualmente - Acceso Denegado (401 Unauthorized)

### Paso 1: Revocar token mediante logout

```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here" \
  -v
```

### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Sesión cerrada exitosamente",
  "tokenRevoked": true,
  "revokedAt": "2024-11-23 23:31:30",
  "timestamp": "2024-11-23 23:31:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 178
```

### Paso 2: Intentar usar el token revocado

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token revocado",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación ha sido revocado. Por favor, inicie sesión nuevamente.",
  "errorCode": "TOKEN_REVOKED",
  "revokedAt": "2024-11-23 23:31:30",
  "timestamp": "2024-11-23 23:31:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Token revoked"
Content-Length: 245
```

---

### Alternativa: Revocar token mediante endpoint específico

```bash
curl -X POST "http://localhost:8000/api/auth/revoke" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here"
  }' \
  -v
```

### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Token revocado exitosamente",
  "tokenRevoked": true,
  "revokedAt": "2024-11-23 23:32:00",
  "timestamp": "2024-11-23 23:32:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 5: Rotación de Tokens - Renovación antes de Expiración (200 OK)

### Paso 1: Obtener token inicial

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMCwianRpIjoiYWJjMTIzZGVmNDU2In0.valid_signature_here",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM1MTQwMH0.refresh_signature",
  "user": {
    "id": "test",
    "email": "test@ovotest.com",
    "rol": "Estudiante"
  },
  "expiresIn": 3600,
  "tokenType": "Bearer",
  "timestamp": "2024-11-23 23:32:15"
}
```

### Paso 2: Renovar token antes de expiración usando refresh token

```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM1MTQwMH0.refresh_signature"
  }' \
  -v
```

### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Token renovado exitosamente",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDY4MDAsImV4cCI6MTczMjM1MDQwMCwianRpIjoieHl6Nzg5YWJjMTIzIn0.new_valid_signature",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MzIzNDY4MDAsImV4cCI6MTczMjM1MjQwMH0.new_refresh_signature",
  "expiresIn": 3600,
  "tokenType": "Bearer",
  "timestamp": "2024-11-23 23:33:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 385
```

### Paso 3: Verificar persistencia de sesión con nuevo token

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDY4MDAsImV4cCI6MTczMjM1MDQwMCwianRpIjoieHl6Nzg5YWJjMTIzIn0.new_valid_signature" \
  -v
```

### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Datos del perfil obtenidos exitosamente",
  "usuario": {
    "id": "test",
    "email": "test@ovotest.com",
    "nombre": "Usuario",
    "apellido": "Prueba",
    "rol": "Estudiante",
    "fechaRegistro": "2024-01-15",
    "ultimoAcceso": "2024-11-23 23:33:15",
    "estado": "activo",
    "preferencias": {
      "notificaciones": true,
      "idioma": "es"
    }
  },
  "timestamp": "2024-11-23 23:33:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 345
```

---

## Escenario 6: Refresh Token Expirado o Inválido (401 Unauthorized)

### Request con refresh token expirado

```bash
curl -X POST "http://localhost:8000/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidHlwZSI6InJlZnJlc2giLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0NTgwMH0.expired_refresh_signature"
  }' \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Refresh token expirado",
  "code": "UNAUTHORIZED",
  "message": "El refresh token ha expirado. Por favor, inicie sesión nuevamente.",
  "errorCode": "REFRESH_TOKEN_EXPIRED",
  "timestamp": "2024-11-23 23:33:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 245
```

---

## Escenario 7: Token sin Header de Authorization (401 Unauthorized)

### Request sin header Authorization

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "No autenticado",
  "code": "UNAUTHORIZED",
  "message": "Se requiere token de autenticación en el header Authorization.",
  "errorCode": "TOKEN_MISSING",
  "timestamp": "2024-11-23 23:33:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer
Content-Length: 198
```

---

## Escenario 8: Token con Payload Alterado (401 Unauthorized)

### Request con token que tiene el payload modificado

```bash
curl -X GET "http://localhost:8000/api/usuario/perfil" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbCI6IkFkbWluaXN0cmFkb3IifQ.original_signature" \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación proporcionado no es válido. La firma del token no coincide con el contenido.",
  "errorCode": "TOKEN_INVALID",
  "timestamp": "2024-11-23 23:34:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
WWW-Authenticate: Bearer error="invalid_token", error_description="Invalid token signature"
Content-Length: 245
```

---

## Notas de Implementación

1. **Validación de Tokens JWT:**
   - Verificar la estructura del token (header.payload.signature)
   - Validar la firma usando la clave secreta
   - Verificar la expiración (`exp` claim)
   - Verificar el tiempo de emisión (`iat` claim)
   - Validar que el token no esté en la lista de tokens revocados

2. **Gestión de Sesiones:**
   - Mantener una lista de tokens activos (opcional, para revocación)
   - Almacenar tokens revocados hasta su expiración natural
   - Implementar limpieza automática de tokens expirados

3. **Rotación de Tokens:**
   - Emitir refresh tokens con mayor tiempo de vida que access tokens
   - Al renovar, invalidar el refresh token anterior (opcional, según política)
   - Mantener la sesión del usuario durante la rotación

4. **Mensajes de Error:**
   - **Token expirado:** "Token expired" o "El token de autenticación ha expirado"
   - **Token inválido:** "Token inválido" o "Invalid token"
   - **Token revocado:** "Token revoked" o "El token ha sido revocado"
   - Incluir código de error específico para facilitar el manejo en el cliente

5. **Headers de Respuesta:**
   - Incluir `WWW-Authenticate: Bearer` en respuestas 401
   - Especificar `error` y `error_description` en el header cuando sea apropiado
   - Proporcionar información suficiente para que el cliente sepa cómo proceder

6. **Seguridad:**
   - Almacenar tokens de forma segura (no en localStorage si es posible)
   - Usar HTTPS para todas las comunicaciones
   - Implementar rate limiting en endpoints de autenticación
   - Registrar intentos de acceso con tokens inválidos para detección de ataques

7. **Revocación de Tokens:**
   - Al hacer logout, marcar el token como revocado
   - Mantener tokens revocados en memoria/cache hasta su expiración
   - Opcionalmente, invalidar todos los tokens de un usuario (en caso de compromiso)

8. **Refresh Tokens:**
   - Emitir refresh tokens con mayor tiempo de vida (ej: 7 días)
   - Validar refresh tokens antes de emitir nuevos access tokens
   - Rotar refresh tokens periódicamente para mayor seguridad

9. **Validación de Claims:**
   - Verificar que el token contenga claims requeridos (`sub`, `email`, `rol`, etc.)
   - Validar que el usuario aún existe y está activo
   - Verificar que el rol del usuario no haya cambiado

10. **Logging y Auditoría:**
    - Registrar todos los intentos de acceso con tokens inválidos
    - Loggear renovaciones de tokens
    - Registrar revocaciones de tokens
    - Mantener logs de seguridad para análisis forense

11. **Configuración:**
    - Tiempo de expiración de access token: 1 hora (3600 segundos)
    - Tiempo de expiración de refresh token: 7 días (604800 segundos)
    - Algoritmo de firma: HS256
    - Clave secreta almacenada de forma segura (variables de entorno)

12. **Manejo de Errores en Cliente:**
    - Cliente debe detectar 401 y redirigir a login
    - Cliente debe intentar renovar token automáticamente si recibe TOKEN_EXPIRED
    - Cliente debe limpiar tokens almacenados localmente al recibir TOKEN_REVOKED

