# Pruebas de Carga - Sistema OVO

Este directorio contiene las pruebas de carga para el sistema OVO, organizadas de forma modular siguiendo principios de alta cohesión y bajo acoplamiento.

## 📁 Estructura del Proyecto

```
tests/load/
├── common/                    # Código reutilizable
│   ├── __init__.py
│   ├── mock_server.py        # Servidor mock con todos los endpoints
│   └── show_results.py       # Visualización de resultados
├── cp010/                     # Prueba CP010 específica
│   └── locustfile.py         # Definición de usuarios y tareas CP010
├── cp011/                     # Prueba CP011 específica
│   └── locustfile.py         # Definición de usuarios y tareas CP011
├── cp012/                     # Prueba CP012 específica
│   └── locustfile.py         # Definición de usuarios y tareas CP012
├── cp013/                     # Prueba CP013 específica
│   └── locustfile.py         # Definición de usuarios y tareas CP013
├── run_load_test.sh          # Script principal de ejecución
├── run_mock_server.sh         # Script para iniciar servidor mock
├── config.example.env         # Ejemplo de configuración
├── README.md                  # Documentación principal
└── QUICKSTART.md              # Guía rápida de inicio
```

## 🧪 Casos de Prueba

### CP010 - Búsqueda/filtrado en tableros bajo carga concurrente

**Objetivo:** Validar que el sistema mantenga un tiempo promedio de respuesta de 5 segundos y un máximo de 10 segundos con 100 solicitudes concurrentes.

**Umbrales:**
- Tiempo promedio: ≤ 5 segundos
- Tiempo máximo: ≤ 10 segundos
- Tasa de error: < 1%

**Endpoint:** `GET /api/dashboard/search`

### CP011 - Finalización de test y generación de informe bajo carga concurrente

**Objetivo:** Comprobar que el sistema soporte 100 solicitudes concurrentes de finalización de test, manteniendo un tiempo promedio 3s para persistir los datos y 6s para generar y mostrar el informe.

**Umbrales:**
- Persistencia (finish): ≤ 3 segundos
- Informe (report): ≤ 6 segundos
- Tasa de error: < 1%

**Endpoints:**
- `POST /api/tests/finish` - Finalizar test y persistir respuestas
- `GET /api/tests/report` - Obtener informe de resultados

### CP012 - Autenticación y sesión bajo carga concurrente

**Objetivo:** Validar que el sistema mantenga un tiempo promedio de respuesta ≤ 6 segundos y una tasa de error < 1% durante solicitudes concurrentes de inicio de sesión y mantenimiento de sesión activa.

**Umbrales:**
- Tiempo promedio: ≤ 6 segundos
- Tasa de error: < 1%
- Sin desconexiones de sesión durante el mantenimiento de carga

**Endpoints:**
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/validate` - Validar token de sesión

### CP013 - Generación de reportes institucionales bajo carga

**Objetivo:** Validar que el sistema genere reportes (CSV y JSON) de hasta 10.000 registros en un tiempo ≤ 15 segundos durante horario pico de uso académico.

**Umbrales:**
- Tiempo promedio: ≤ 15 segundos
- Tasa de error: < 1%
- Archivo generado completo y sin corrupción

**Endpoints:**
- `GET /api/reportes/export` - Exportar reportes (CSV o JSON)

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements-dev.txt
```

### 2. Iniciar servidor mock

```bash
cd tests/load
./run_mock_server.sh
```

### 3. Ejecutar prueba de carga

**CP010:**
```bash
./run_load_test.sh cp010 http://localhost:8000
```

**CP011:**
```bash
./run_load_test.sh cp011 http://localhost:8000
```

**CP012:**
```bash
./run_load_test.sh cp012 http://localhost:8000
```

**CP013:**
```bash
./run_load_test.sh cp013 http://localhost:8000
```

## 📊 Ver Resultados

Después de ejecutar una prueba, los resultados se muestran automáticamente. También puedes verlos manualmente:

```bash
python3 common/show_results.py reports/results_cp010_YYYYMMDD_HHMMSS_stats.csv CP010
python3 common/show_results.py reports/results_cp011_YYYYMMDD_HHMMSS_stats.csv CP011
python3 common/show_results.py reports/results_cp012_YYYYMMDD_HHMMSS_stats.csv CP012
python3 common/show_results.py reports/results_cp013_YYYYMMDD_HHMMSS_stats.csv CP013
```

## 🛠️ Servidor Mock

El servidor mock (`common/mock_server.py`) simula todos los endpoints necesarios para las pruebas:

- **GET /api/dashboard/search** - Búsqueda en dashboard (CP010)
- **POST /api/tests/finish** - Finalizar test (CP011)
- **GET /api/tests/report** - Obtener informe (CP011)
- **POST /api/auth/login** - Iniciar sesión (CP012)
- **GET /api/auth/validate** - Validar token de sesión (CP012)
- **GET /api/reportes/export** - Exportar reportes CSV/JSON (CP013)
- **GET /health** - Health check
- **GET /stats** - Estadísticas del servidor

### Tiempos de respuesta simulados

**CP010 - Dashboard Search:**
- 20% de requests: 1-2 segundos
- 60% de requests: 3-5 segundos
- 15% de requests: 6-8 segundos
- 5% de requests: 8-10 segundos

**CP011 - Test Finish:**
- 70% de requests: 0.5-1.75 segundos
- 30% de requests: 1.75-3 segundos

**CP011 - Test Report:**
- 70% de requests: 1-3.5 segundos
- 30% de requests: 3.5-6 segundos

**CP012 - Auth Login:**
- 70% de requests: 1-3.5 segundos
- 30% de requests: 3.5-6 segundos

**CP013 - Reportes Export:**
- 70% de requests: 5-10 segundos
- 30% de requests: 10-15 segundos

## 📝 Configuración

### Variables de entorno

Crea un archivo `.env` (opcional):

```bash
API_BASE_URL=http://localhost:8000
API_KEY=tu-api-key-aqui
USERS=100
SPAWN_RATE=10
```

### Parámetros de ejecución

- `USERS`: Número de usuarios concurrentes (default: 100)
- `SPAWN_RATE`: Usuarios a iniciar por segundo (default: 10)
- `RUN_TIME`: Duración de la prueba (fijo: 1m)

## 🔧 Desarrollo

### Agregar una nueva prueba

1. Crear directorio `cpXXX/`
2. Crear `cpXXX/locustfile.py` con la clase de usuario
3. Agregar endpoints al mock server si es necesario
4. Actualizar `run_load_test.sh` para incluir el nuevo test case

### Estructura de un locustfile

```python
from locust import HttpUser, task, between
import os

class MyTestUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.headers = {"Content-Type": "application/json"}
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["x-api-key"] = api_key
    
    @task(1)
    def my_endpoint(self):
        with self.client.get("/api/endpoint", headers=self.headers) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Error: {response.status_code}")
```

## 📚 Referencias

- [Documentación oficial de Locust](https://docs.locust.io/)
- [Guía de mejores prácticas de Locust](https://docs.locust.io/en/stable/writing-a-locustfile.html)
