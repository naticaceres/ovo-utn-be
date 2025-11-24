from locust import HttpUser, task, between
import logging
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthUser(HttpUser):
    wait_time = between(2, 5)
    
    def on_start(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["x-api-key"] = api_key
        
        self.user_number = random.randint(1, 1000)
        self.email = f"usuario{self.user_number}@prueba.com"
        self.password = "password123"
        self.token = None
    
    @task(3)
    def login(self):
        payload = {
            "email": self.email,
            "password": self.password
        }
        
        with self.client.post(
            "/api/auth/login",
            json=payload,
            headers=self.headers,
            name="Auth Login",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") and data.get("token"):
                        self.token = data["token"]
                        self.headers["Authorization"] = f"Bearer {self.token}"
                        response.success()
                    else:
                        response.failure("Login exitoso pero sin token")
                except:
                    response.failure("Error al parsear respuesta")
            elif response.status_code == 401:
                response.failure(f"Credenciales inválidas: {response.status_code}")
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")
    
    @task(1)
    def validate_session(self):
        if not self.token:
            return
        
        with self.client.get(
            "/api/auth/validate",
            headers=self.headers,
            name="Auth Validate",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success") and data.get("valid"):
                        response.success()
                    else:
                        response.failure("Token inválido")
                except:
                    response.failure("Error al parsear respuesta")
            elif response.status_code == 401:
                response.failure(f"Token inválido: {response.status_code}")
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")

