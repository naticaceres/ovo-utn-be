"""
Unit tests para response_builder.py
"""
import os
import sys
import json

# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

import pytest
from lib.chat.response_builder import (
    get_cors_headers,
    get_cors_headers_options,
    get_history_to_return,
    build_response,
    build_error_response
)


class TestGetCorsHeaders:
    """Tests para get_cors_headers"""
    
    def test_returns_cors_headers(self):
        """Test que retorna headers CORS correctos"""
        headers = get_cors_headers()
        
        assert "Content-Type" in headers
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
    
    def test_headers_values(self):
        """Test que los headers tienen los valores correctos"""
        headers = get_cors_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Access-Control-Allow-Methods"] == "POST, OPTIONS"
        assert headers["Access-Control-Allow-Headers"] == "Content-Type, Authorization"
    
    def test_returns_copy(self):
        """Test que retorna una copia (no referencia)"""
        headers1 = get_cors_headers()
        headers2 = get_cors_headers()
        
        headers1["test"] = "value"
        assert "test" not in headers2


class TestGetCorsHeadersOptions:
    """Tests para get_cors_headers_options"""
    
    def test_removes_content_type(self):
        """Test que remueve Content-Type para OPTIONS"""
        headers = get_cors_headers_options()
        
        assert "Content-Type" not in headers
        assert "Access-Control-Allow-Origin" in headers


class TestGetHistoryToReturn:
    """Tests para get_history_to_return"""
    
    def test_removes_first_element(self):
        """Test que remueve el primer elemento (system prompt)"""
        history = [
            "System: System prompt",
            "Usuario: Hola",
            "Asistente: Respuesta"
        ]
        
        result = get_history_to_return(history)
        
        assert len(result) == 2
        assert result[0] == "Usuario: Hola"
        assert result[1] == "Asistente: Respuesta"
    
    def test_empty_history(self):
        """Test con historial vacío"""
        history = []
        
        result = get_history_to_return(history)
        
        assert result == []
    
    def test_single_element_history(self):
        """Test con historial de un solo elemento"""
        history = ["System: System prompt"]
        
        result = get_history_to_return(history)
        
        assert result == []


class TestBuildResponse:
    """Tests para build_response"""
    
    def test_build_response_basic(self):
        """Test construcción básica de respuesta"""
        response = build_response(
            "Respuesta del chatbot",
            "chat123",
            "Waiting for 2 of 5",
            ["System: prompt", "Usuario: Hola", "Asistente: Respuesta"]
        )
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["chatbot_response"] == "Respuesta del chatbot"
        assert body["chat_id"] == "chat123"
        assert body["status"] == "Waiting for 2 of 5"
        assert len(body["full_history"]) == 2
    
    def test_build_response_with_final_scores(self):
        """Test construcción de respuesta con final_scores"""
        final_scores = {"Creatividad": 8, "Liderazgo": 7}
        response = build_response(
            "",
            "chat123",
            "FINISHED",
            ["System: prompt"],
            final_scores
        )
        
        body = json.loads(response["body"])
        assert "final_scores" in body
        assert body["final_scores"] == final_scores
    
    def test_build_response_without_final_scores(self):
        """Test que no incluye final_scores si es None"""
        response = build_response(
            "Respuesta",
            "chat123",
            "Waiting for 1 of 5",
            ["System: prompt"]
        )
        
        body = json.loads(response["body"])
        assert "final_scores" not in body


class TestBuildErrorResponse:
    """Tests para build_error_response"""
    
    def test_build_error_response_basic(self):
        """Test construcción básica de error"""
        response = build_error_response(400, "Bad Request")
        
        assert response["statusCode"] == 400
        assert "headers" in response
        assert "body" in response
        
        body = json.loads(response["body"])
        assert body["error"] == "Bad Request"
        assert "detail" not in body
    
    def test_build_error_response_with_detail(self):
        """Test construcción de error con detalle"""
        response = build_error_response(500, "Internal Error", "Something went wrong")
        
        body = json.loads(response["body"])
        assert body["error"] == "Internal Error"
        assert body["detail"] == "Something went wrong"
    
    def test_different_status_codes(self):
        """Test con diferentes códigos de estado"""
        for code in [400, 429, 500]:
            response = build_error_response(code, "Error")
            assert response["statusCode"] == code

