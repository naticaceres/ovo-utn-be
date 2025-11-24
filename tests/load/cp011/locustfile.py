from locust import HttpUser, task, between
import logging
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFinishUser(HttpUser):
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["x-api-key"] = api_key
        
        self.test_id = f"test_{random.randint(1000, 9999)}"
        self.user_id = f"user_{random.randint(100, 999)}"
    
    @task(1)
    def finish_test(self):
        respuestas = {
            f"pregunta_{i}": random.choice(["A", "B", "C", "D"]) 
            for i in range(1, random.randint(20, 50))
        }
        
        payload = {
            "testId": self.test_id,
            "userId": self.user_id,
            "respuestas": respuestas
        }
        
        with self.client.post(
            "/api/tests/finish",
            json=payload,
            headers=self.headers,
            name="Test Finish",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")
    
    @task(2)
    def get_report(self):
        params = {
            "testId": self.test_id,
            "userId": self.user_id
        }
        
        with self.client.get(
            "/api/tests/report",
            params=params,
            headers=self.headers,
            name="Test Report",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code >= 500:
                response.failure(f"Error del servidor: {response.status_code}")
            else:
                response.failure(f"Error HTTP: {response.status_code}")

