from locust import HttpUser, task, between
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DashboardSearchUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["x-api-key"] = api_key
    
    @task(1)
    def search_dashboard(self):
        params = {
            "tipoCarrera": "Todas",
            "fechaDesde": "01/01/2024",
            "fechaHasta": "31/12/2024"
        }
        
        with self.client.get(
            "/api/dashboard/search",
            params=params,
            headers=self.headers,
            name="Dashboard Search",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.failure(f"Rate limit alcanzado: {response.status_code}")
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")

