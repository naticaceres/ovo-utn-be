# CP016 - Curl Requests y Respuestas Esperadas

## Caso de Prueba: Verificar la autorización para editar una carrera de una institución

### Datos de Prueba
- **Usuario Institución:**
  - Email: instituciontest@ovotest.com
  - Password: testPass123456!@#
  - Rol: Institución
- **Usuario Estudiante:**
  - Email: test@ovotest.com
  - Password: testPass123456!@#
  - Rol: Estudiante
- **Usuario Administrador:**
  - Email: admintest@ovotest.com
  - Password: testPass123456!@#
  - Rol: Administrador
- **Endpoint:** PUT /institutions/me/careers/10
- **Base URL:** http://localhost:8000
- **Carrera de prueba:**
  - ID: 10
  - Nombre: "Pruebas"
  - Pertenece a: Usuario Institución (instituciontest@ovotest.com)

---

## Escenario 1: Acceso Denegado - Sin Autenticación (403 Forbidden)

### Request sin autenticación

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado. Se requiere autenticación.",
  "code": "FORBIDDEN",
  "message": "No se proporcionó token de autenticación o el token es inválido.",
  "timestamp": "2024-11-23 22:30:00"
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
  "timestamp": "2024-11-23 22:30:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 245
```

### Paso 2: Intento de editar carrera (con token de Estudiante)

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwiemVtYWlsIjoidGVzdEBvdm90ZXN0LmNvbSIsInJvbCI6IkVzdHVkaWFudGUiLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.xyz789abc123" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos suficientes para acceder a este recurso. Se requiere rol de Institución.",
  "requiredRole": "Institución",
  "currentRole": "Estudiante",
  "timestamp": "2024-11-23 22:30:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 245
```

---

## Escenario 3: Acceso Autorizado - Usuario Institución (200 OK)

### Paso 1: Autenticación del usuario Institución

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

### Respuesta de Autenticación (200 OK)

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
  "timestamp": "2024-11-23 22:30:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 275
```

### Paso 2: Editar carrera (con token de Institución)

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (200 OK) - Edición exitosa

```json
{
  "success": true,
  "message": "Carrera actualizada exitosamente",
  "career": {
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": null,
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas",
    "institucionId": "instituciontest",
    "updatedAt": "2024-11-23 22:30:45"
  },
  "changes": {
    "observaciones": {
      "old": "",
      "new": "esto es un cambio"
    }
  },
  "timestamp": "2024-11-23 22:30:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 512
```

---

## Escenario 4: Token Inválido o Expirado (401 Unauthorized)

### Request con token inválido

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer token_invalido_o_expirado" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (401 Unauthorized)

```json
{
  "success": false,
  "error": "Token inválido o expirado",
  "code": "UNAUTHORIZED",
  "message": "El token de autenticación proporcionado no es válido o ha expirado.",
  "timestamp": "2024-11-23 22:31:00"
}
```

**Headers de respuesta:**
```
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Content-Length: 178
```

---

## Escenario 5: Intento de editar carrera de otra institución (403 Forbidden)

### Request con token de Institución A intentando editar carrera de Institución B

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJvdHJhaW5zdGl0dWNpb24iLCJ6ZW1haWwiOiJvdHJhQG92b3Rlc3QuY29tIiwicm9sIjoiSW5zdGl0dWNpb24iLCJpYXQiOjE3MzIzNDU4MDAsImV4cCI6MTczMjM0OTQwMH0.otra456institucion" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (403 Forbidden)

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "No tiene permisos para editar esta carrera. La carrera pertenece a otra institución.",
  "careerId": 10,
  "careerOwner": "instituciontest",
  "currentUser": "otrainstitucion",
  "timestamp": "2024-11-23 22:31:15"
}
```

**Headers de respuesta:**
```
HTTP/1.1 403 Forbidden
Content-Type: application/json
Content-Length: 278
```

---

## Escenario 6: Carrera no encontrada (404 Not Found)

### Request con token válido pero carrera inexistente

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/999" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -d '{
    "id": 999,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (404 Not Found)

```json
{
  "success": false,
  "error": "Carrera no encontrada",
  "code": "NOT_FOUND",
  "message": "La carrera con ID 999 no existe o no pertenece a su institución.",
  "careerId": 999,
  "timestamp": "2024-11-23 22:31:30"
}
```

**Headers de respuesta:**
```
HTTP/1.1 404 Not Found
Content-Type: application/json
Content-Length: 198
```

---

## Escenario 7: Validación de datos - Payload inválido (400 Bad Request)

### Request con datos inválidos (campos requeridos faltantes o valores inválidos)

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnN0aXR1Y2lvbnRlc3QiLCJ6ZW1haWwiOiJpbnN0aXR1Y2lvbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJJbnN0aXR1Y2lvbiIsImlhdCI6MTczMjM0NTgwMCwiZXhwIjoxNzMyMzQ5NDAwf0.institucion456def789" \
  -d '{
    "id": 10,
    "nombreCarrera": "",
    "duracionCarrera": -1
  }' \
  -v
```

### Respuesta Esperada (400 Bad Request)

```json
{
  "success": false,
  "error": "Datos de validación inválidos",
  "code": "BAD_REQUEST",
  "message": "Los datos proporcionados no son válidos.",
  "validationErrors": [
    {
      "field": "nombreCarrera",
      "message": "El nombre de la carrera es requerido y no puede estar vacío"
    },
    {
      "field": "duracionCarrera",
      "message": "La duración de la carrera debe ser un número positivo"
    },
    {
      "field": "cantidadMaterias",
      "message": "La cantidad de materias es requerida"
    },
    {
      "field": "idCarrera",
      "message": "El ID de carrera es requerido"
    }
  ],
  "timestamp": "2024-11-23 22:31:45"
}
```

**Headers de respuesta:**
```
HTTP/1.1 400 Bad Request
Content-Type: application/json
Content-Length: 445
```

---

## Escenario 8: Acceso con Rol Administrador (403 Forbidden o 200 OK según política)

### Nota: Este escenario depende de la política de negocio

Si los administradores NO pueden editar carreras de instituciones:

```bash
curl -X PUT "http://localhost:8000/institutions/me/careers/10" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbnRlc3QiLCJ6ZW1haWwiOiJhZG1pbnRlc3RAb3ZvdGVzdC5jb20iLCJyb2wiOiJBZG1pbmlzdHJhZG9yIiwiaWF0IjoxNzMyMzQ1ODAwLCJleHAiOjE3MzIzNDk0MDB9.admin456def789" \
  -d '{
    "id": 10,
    "cantidadMaterias": 40,
    "duracionCarrera": 5,
    "fechaFin": "",
    "fechaInicio": "2000-01-01",
    "horasCursado": 450,
    "idCarrera": 9,
    "idEstado": 1,
    "idModalidad": 6,
    "montoCuota": 0,
    "nombreCarrera": "Pruebas",
    "observaciones": "esto es un cambio",
    "tituloCarrera": "Pruebas"
  }' \
  -v
```

### Respuesta Esperada (403 Forbidden) - Si administradores no pueden editar

```json
{
  "success": false,
  "error": "Acceso denegado",
  "code": "FORBIDDEN",
  "message": "Solo las instituciones pueden editar sus propias carreras.",
  "requiredRole": "Institución",
  "currentRole": "Administrador",
  "timestamp": "2024-11-23 22:32:00"
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
   - El rol del usuario sea "Institución" para acceder a endpoints `/institutions/me/*`
   - El usuario solo pueda editar carreras que pertenezcan a su propia institución
   - El endpoint `/institutions/me/careers/{id}` debe validar que la carrera con `id` pertenezca al usuario autenticado

3. **Validación de Propiedad:** El sistema debe verificar que:
   - La carrera existe en la base de datos
   - La carrera pertenece a la institución del usuario autenticado
   - Si la carrera pertenece a otra institución, devolver 403 Forbidden

4. **Validación de Datos:** El sistema debe validar:
   - Campos requeridos presentes
   - Tipos de datos correctos
   - Valores dentro de rangos válidos (duración positiva, fechas válidas, etc.)
   - IDs de referencias válidos (idCarrera, idEstado, idModalidad)

5. **Auditoría:** Todos los intentos de acceso deben registrarse en el sistema de auditoría con:
   - Timestamp
   - Usuario autenticado
   - Rol del usuario
   - IP de origen
   - Endpoint intentado
   - ID de carrera
   - Resultado (éxito o denegación)
   - Razón de denegación (si aplica)
   - Cambios realizados (en caso de edición exitosa)

6. **Respuestas:** Las respuestas exitosas (200) deben incluir:
   - La carrera actualizada con todos sus campos
   - Un resumen de los cambios realizados (opcional pero recomendado)
   - Timestamp de actualización
   - ID de la institución propietaria

7. **Estructura del Payload:** El payload debe incluir todos los campos de la carrera:
   - `id`: ID de la carrera a editar
   - `cantidadMaterias`: Número de materias
   - `duracionCarrera`: Duración en años
   - `fechaFin`: Fecha de finalización (puede ser vacía/null)
   - `fechaInicio`: Fecha de inicio
   - `horasCursado`: Total de horas de cursado
   - `idCarrera`: ID de referencia a catálogo de carreras
   - `idEstado`: ID de estado de la carrera
   - `idModalidad`: ID de modalidad (presencial, virtual, etc.)
   - `montoCuota`: Monto de la cuota
   - `nombreCarrera`: Nombre de la carrera
   - `observaciones`: Observaciones adicionales
   - `tituloCarrera`: Título que otorga la carrera

