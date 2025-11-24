from locust import HttpUser, task, between
import logging
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportesExportUser(HttpUser):
    wait_time = between(3, 8)
    
    def on_start(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["x-api-key"] = api_key
        
        self.institucion_id = random.randint(100, 999)
    
    @task(1)
    def export_csv(self):
        params = {
            "formato": "csv",
            "institucionId": str(self.institucion_id),
            "fechaDesde": "01/01/2024",
            "fechaHasta": "31/12/2024",
            "registros": random.choice([100, 500, 1000, 5000, 10000])
        }
        
        with self.client.get(
            "/api/reportes/export",
            params=params,
            headers=self.headers,
            name="Reportes Export CSV",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                if 'text/csv' in response.headers.get('Content-Type', ''):
                    content_length = len(response.content)
                    if content_length > 0:
                        response.success()
                    else:
                        response.failure("Archivo CSV vacío")
                else:
                    response.failure("Content-Type incorrecto para CSV")
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")
    
    @task(1)
    def export_json(self):
        params = {
            "formato": "json",
            "institucionId": str(self.institucion_id),
            "fechaDesde": "01/01/2024",
            "fechaHasta": "31/12/2024",
            "registros": random.choice([100, 500, 1000, 5000, 10000])
        }
        
        with self.client.get(
            "/api/reportes/export",
            params=params,
            headers=self.headers,
            name="Reportes Export JSON",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") and "datos" in data:
                        total_registros = data.get("totalRegistros", 0)
                        if total_registros > 0:
                            response.success()
                        else:
                            response.failure("Reporte JSON sin registros")
                    else:
                        response.failure("Estructura JSON inválida")
                except:
                    response.failure("Error al parsear JSON")
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")

