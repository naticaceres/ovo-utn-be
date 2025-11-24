# CP017 - Curl Requests y Respuestas Esperadas

## Caso de Prueba: Protección de acciones críticas

### Datos de Prueba
- **Usuario Institución:**
  - Email: instituciontest@ovotest.com
  - Password: testPass123456!@#
  - Rol: Institución
- **Usuario Estudiante:**
  - Email: test@ovotest.com
  - Password: testPass123456!@#
  - Rol: Estudiante
- **Endpoints Críticos:**
  - POST /api/carreras (crear carrera)
  - PUT /api/campanias/{id} (editar campaña)
  - GET /api/reportes/{id} (acceder reporte individual)
- **Base URL:** http://localhost:8000

---

## Endpoint 1: POST /api/carreras (Crear Carrera)

### Escenario 1.1: Acceso Autorizado - Usuario Institución (200 OK)

#### Paso 1: Autenticación del usuario Institución

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "instituciontest@ovotest.com",
    "password": "testPass123456!@#"
  }' \
  -v
```

#### Respuesta de Autenticación (200 OK)

```json
{
  "success": true,
  "message": "Autenticación exitosa",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789",
  "user": {
    "id": "instituciontest",
    "email": "instituciontest@ovotest.com",
    "rol": "Institución"
  },
  "expiresIn": 3600,
  "timestamp": "2024-11-23 23:00:00"
}
```

#### Paso 2: Crear carrera (con token de Institución)

```bash
curl -X POST "http://localhost:8000/api/carreras" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -d '{
    "cantidadMaterias": 42,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2025-01-01",
    "horasCursado": 480,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 50000,
    "nombreCarrera": "Ingeniería en Sistemas",
    "observaciones": "Nueva carrera de ingeniería",
    "tituloCarrera": "Ingeniero en Sistemas"
  }' \
  -v
```

#### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Carrera creada exitosamente",
  "career": {
    "id": 11,
    "cantidadMaterias": 42,
    "duracionCarrera": 5,
    "fechaFin": null,
    "fechaInicio": "2025-01-01",
    "horasCursado": 480,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 50000,
    "nombreCarrera": "Ingeniería en Sistemas",
    "observaciones": "Nueva carrera de ingeniería",
    "tituloCarrera": "Ingeniero en Sistemas",
    "institucionId": "instituciontest",
    "createdAt": "2024-11-23 23:00:15",
    "updatedAt": "2024-11-23 23:00:15"
  },
  "timestamp": "2024-11-23 23:00:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 512
```

---

### Escenario 1.2: Acceso Denegado - Usuario Estudiante (403 Forbidden)

#### Paso 1: Autenticación del usuario Estudiante

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

#### Respuesta de Autenticación (200 OK)

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
  "timestamp": "2024-11-23 23:00:30"
}
```

#### Paso 2: Intento de crear carrera (con token de Estudiante)

```bash
curl -X POST "http://localhost:8000/api/carreras" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123" \
  -d '{
    "cantidadMaterias": 42,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2025-01-01",
    "horasCursado": 480,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 50000,
    "nombreCarrera": "Ingeniería en Sistemas",
    "observaciones": "Nueva carrera de ingeniería",
    "tituloCarrera": "Ingeniero en Sistemas"
  }' \
  -v
```

#### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para realizar esta acción. Se requiere rol de Institución.",
  "requiredRole": "Institución",
  "currentRole": "Estudiante",
  "action": "crear_carrera",
  "timestamp": "2024-11-23 23:00:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 278
```

---

### Escenario 1.3: Acceso Denegado - Sin Autenticación (401 Unauthorized)

#### Request sin autenticación

```bash
curl -X POST "http://localhost:8000/api/carreras" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "cantidadMaterias": 42,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2025-01-01",
    "horasCursado": 480,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 50000,
    "nombreCarrera": "Ingeniería en Sistemas",
    "observaciones": "Nueva carrera de ingeniería",
    "tituloCarrera": "Ingeniero en Sistemas"
  }' \
  -v
```

#### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "No autenticado",
  "code": "UNAUTHORIZED",
  "message": "Se requiere autenticación para realizar esta acción.",
  "action": "crear_carrera",
  "timestamp": "2024-11-23 23:01:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Endpoint 2: PUT /api/campanias/{id} (Editar Campaña)

### Escenario 2.1: Acceso Autorizado - Usuario Institución (200 OK)

#### Editar campaña (con token de Institución)

```bash
curl -X PUT "http://localhost:8000/api/campanias/5" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -d '{
    "id": 5,
    "nombre": "Campaña de Inscripción 2025",
    "descripcion": "Campaña promocional para inscripciones del primer cuatrimestre",
    "fechaInicio": "2024-12-01",
    "fechaFin": "2025-02-28",
    "activa": true,
    "presupuesto": 500000,
    "canales": ["web", "redes_sociales", "email"],
    "objetivos": {
      "inscripciones": 200,
      "alcance": 10000
    }
  }' \
  -v
```

#### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Campaña actualizada exitosamente",
  "campania": {
    "id": 5,
    "nombre": "Campaña de Inscripción 2025",
    "descripcion": "Campaña promocional para inscripciones del primer cuatrimestre",
    "fechaInicio": "2024-12-01",
    "fechaFin": "2025-02-28",
    "activa": true,
    "presupuesto": 500000,
    "canales": ["web", "redes_sociales", "email"],
    "objetivos": {
      "inscripciones": 200,
      "alcance": 10000
    },
    "institucionId": "instituciontest",
    "updatedAt": "2024-11-23 23:01:15",
    "updatedBy": "instituciontest@ovotest.com"
  },
  "timestamp": "2024-11-23 23:01:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 512
```

---

### Escenario 2.2: Acceso Denegado - Usuario Estudiante (403 Forbidden)

#### Intento de editar campaña (con token de Estudiante)

```bash
curl -X PUT "http://localhost:8000/api/campanias/5" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123" \
  -d '{
    "id": 5,
    "nombre": "Campaña de Inscripción 2025",
    "descripcion": "Campaña promocional para inscripciones del primer cuatrimestre",
    "fechaInicio": "2024-12-01",
    "fechaFin": "2025-02-28",
    "activa": true,
    "presupuesto": 500000,
    "canales": ["web", "redes_sociales", "email"],
    "objetivos": {
      "inscripciones": 200,
      "alcance": 10000
    }
  }' \
  -v
```

#### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para realizar esta acción. Se requiere rol de Institución.",
  "requiredRole": "Institución",
  "currentRole": "Estudiante",
  "action": "editar_campania",
  "timestamp": "2024-11-23 23:01:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 278
```

---

### Escenario 2.3: Acceso Denegado - Sin Autenticación (401 Unauthorized)

#### Request sin autenticación

```bash
curl -X PUT "http://localhost:8000/api/campanias/5" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "id": 5,
    "nombre": "Campaña de Inscripción 2025",
    "descripcion": "Campaña promocional para inscripciones del primer cuatrimestre",
    "fechaInicio": "2024-12-01",
    "fechaFin": "2025-02-28",
    "activa": true,
    "presupuesto": 500000,
    "canales": ["web", "redes_sociales", "email"],
    "objetivos": {
      "inscripciones": 200,
      "alcance": 10000
    }
  }' \
  -v
```

#### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "No autenticado",
  "code": "UNAUTHORIZED",
  "message": "Se requiere autenticación para realizar esta acción.",
  "action": "editar_campania",
  "timestamp": "2024-11-23 23:01:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Endpoint 3: GET /api/reportes/{id} (Acceder Reporte Individual)

### Escenario 3.1: Acceso Autorizado - Usuario Institución (200 OK)

#### Obtener reporte individual (con token de Institución)

```bash
curl -X GET "http://localhost:8000/api/reportes/123" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -v
```

#### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Reporte obtenido exitosamente",
  "reporte": {
    "id": 123,
    "tipo": "institucional",
    "nombre": "Reporte de Inscripciones Q1 2024",
    "fechaGeneracion": "2024-11-20 10:30:00",
    "periodo": {
      "inicio": "2024-01-01",
      "fin": "2024-03-31"
    },
    "datos": {
      "totalInscripciones": 450,
      "inscripcionesPorCarrera": [
        {
          "carrera": "Ingeniería en Sistemas",
          "cantidad": 180,
          "porcentaje": 40.0
        },
        {
          "carrera": "Ingeniería Industrial",
          "cantidad": 120,
          "porcentaje": 26.7
        },
        {
          "carrera": "Ingeniería Química",
          "cantidad": 150,
          "porcentaje": 33.3
        }
      ],
      "tendencias": {
        "crecimiento": 15.5,
        "proyeccion": 520
      }
    },
    "institucionId": "instituciontest",
    "generadoPor": "instituciontest@ovotest.com"
  },
  "timestamp": "2024-11-23 23:02:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 645
```

---

### Escenario 3.2: Acceso Denegado - Usuario Estudiante (403 Forbidden)

#### Intento de obtener reporte (con token de Estudiante)

```bash
curl -X GET "http://localhost:8000/api/reportes/123" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123" \
  -v
```

#### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para acceder a este recurso. Se requiere rol de Institución o Administrador.",
  "requiredRoles": ["Institución", "Administrador"],
  "currentRole": "Estudiante",
  "action": "acceder_reporte",
  "timestamp": "2024-11-23 23:02:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 298
```

---

### Escenario 3.3: Acceso Denegado - Sin Autenticación (401 Unauthorized)

#### Request sin autenticación

```bash
curl -X GET "http://localhost:8000/api/reportes/123" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -v
```

#### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "No autenticado",
  "code": "UNAUTHORIZED",
  "message": "Se requiere autenticación para realizar esta acción.",
  "action": "acceder_reporte",
  "timestamp": "2024-11-23 23:02:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 4: Consultar Carreras después de Logout (401 Unauthorized)

### Paso 1: Logout del usuario

```bash
curl -X POST "http://localhost:8000/api/auth/logout" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -v
```

#### Respuesta Esperada (200 OK)

```json
{
  "success": true,
  "message": "Sesión cerrada exitosamente",
  "timestamp": "2024-11-23 23:02:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 78
```

### Paso 2: Consultar carreras de institución (sin token o con token invalidado)

```bash
curl -X GET "http://localhost:8000/api/carreras?institucionId=instituciontest" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -v
```

#### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "No autenticado",
  "code": "UNAUTHORIZED",
  "message": "Se requiere autenticación para realizar esta acción.",
  "action": "consultar_carreras",
  "timestamp": "2024-11-23 23:03:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 5: Token Expirado (401 Unauthorized)

### Request con token expirado

```bash
curl -X POST "http://localhost:8000/api/carreras" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJleHAiOjE3MzIzNDU4MDB9.token_expirado" \
  -d '{
    "cantidadMaterias": 42,
    "duracionCarrera": 5,
    "nombreCarrera": "Ingeniería en Sistemas"
  }' \
  -v
```

#### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido o expirado",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación proporcionado no es válido o ha expirado.",
  "action": "crear_carrera",
  "timestamp": "2024-11-23 23:03:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 198
```

---

## Notas de Implementación

1. **Autenticación JWT:** Todos los endpoints críticos deben validar el token JWT en el header `Authorization: Bearer <token>`

2. **Autorización RBAC:** El sistema debe verificar que:
   - El usuario esté autenticado (token válido y no expirado)
   - El rol del usuario tenga permisos para la acción solicitada
   - Para endpoints de creación/edición de carreras y campañas: se requiere rol "Institución"
   - Para endpoints de reportes: se requiere rol "Institución" o "Administrador"

3. **Protección de Acciones Críticas:**
   - **POST /api/carreras**: Solo usuarios con rol "Institución"
   - **PUT /api/campanias/{id}**: Solo usuarios con rol "Institución" y propietarios de la campaña
   - **GET /api/reportes/{id}**: Solo usuarios con rol "Institución" o "Administrador"

4. **Validación de Propiedad:** Para edición de recursos:
   - Verificar que el recurso pertenezca a la institución del usuario autenticado
   - Si el recurso pertenece a otra institución, devolver 403 Forbidden

5. **Auditoría y Trazabilidad:** Todos los intentos de acceso (exitosos y fallidos) deben registrarse en el sistema de auditoría con:
   - Timestamp preciso
   - Usuario autenticado (si aplica)
   - Rol del usuario
   - IP de origen
   - Endpoint intentado
   - Método HTTP
   - Acción realizada
   - Resultado (éxito o denegación)
   - Código de respuesta HTTP
   - Razón de denegación (si aplica)
   - Cambios realizados (en caso de edición exitosa)

6. **Protección de Base de Datos:**
   - No se deben realizar modificaciones en la base de datos ante intentos no autorizados
   - Las validaciones de autorización deben ocurrir ANTES de cualquier operación de escritura
   - Usar transacciones para asegurar atomicidad en operaciones críticas

7. **Logs de Seguridad:** Registrar en logs de seguridad:
   - Intentos de acceso no autorizados (401, 403)
   - Patrones sospechosos (múltiples intentos fallidos desde la misma IP)
   - Acciones críticas exitosas (para trazabilidad completa)

8. **Respuestas de Error:** Las respuestas de error deben:
   - No exponer información sensible sobre la estructura del sistema
   - Proporcionar suficiente información para debugging (en logs, no en respuesta al cliente)
   - Incluir código de error y mensaje descriptivo pero genérico

9. **Invalidación de Tokens:** Al hacer logout:
   - Invalidar el token en el servidor (si se mantiene una lista de tokens activos)
   - O marcar el token como expirado
   - Cualquier request posterior con ese token debe devolver 401 Unauthorized

10. **Middleware de Seguridad:** Implementar middleware que:
    - Valide tokens JWT antes de procesar cualquier request
    - Verifique permisos RBAC según el endpoint y método HTTP
    - Registre eventos de auditoría automáticamente
    - Bloquee requests no autorizados antes de llegar al controlador

