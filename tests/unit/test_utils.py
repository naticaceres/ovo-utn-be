"""
Unit tests para utils.py
"""
import os
import sys

# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

import pytest
from lib.chat.utils import (
    extract_final_scores_from_response,
    clean_chatbot_response,
    validate_request,
    get_last_assistant_message
)


class TestExtractFinalScoresFromResponse:
    """Tests para extract_final_scores_from_response (legacy)"""
    
    def test_extract_scores_basic(self):
        """Test extracción básica de scores"""
        text = "final_scores: Creatividad: 8, Liderazgo: 7"
        result = extract_final_scores_from_response(text)
        
        assert result is not None
        assert result["Creatividad"] == 8.0
        assert result["Liderazgo"] == 7.0
    
    def test_extract_scores_not_found(self):
        """Test cuando no hay final_scores"""
        text = "No hay scores aquí"
        result = extract_final_scores_from_response(text)
        
        assert result is None
    
    def test_extract_scores_empty_text(self):
        """Test con texto vacío"""
        result = extract_final_scores_from_response("")
        assert result is None
    
    def test_extract_scores_with_spaces(self):
        """Test con espacios en el formato"""
        text = "final_scores: Aptitud1: 5, Aptitud2: 9"
        result = extract_final_scores_from_response(text)
        
        assert result is not None
        assert result["Aptitud1"] == 5.0
        assert result["Aptitud2"] == 9.0


class TestCleanChatbotResponse:
    """Tests para clean_chatbot_response (legacy)"""
    
    def test_clean_removes_final_scores_line(self):
        """Test que remueve líneas con final_scores"""
        text = "Esta es una respuesta\nfinal_scores: algo\nOtra línea"
        result = clean_chatbot_response(text)
        
        assert "final_scores" not in result.lower()
        assert "Esta es una respuesta" in result
        assert "Otra línea" in result
    
    def test_clean_empty_text(self):
        """Test con texto vacío"""
        result = clean_chatbot_response("")
        assert result == ""
    
    def test_clean_none_text(self):
        """Test con None"""
        result = clean_chatbot_response(None)
        assert result == ""


class TestValidateRequest:
    """Tests para validate_request"""
    
    def test_validate_request_valid(self):
        """Test validación de request válida"""
        body = {
            "ChatID": "chat123",
            "UserID": "user123",
            "prompt": "Mi respuesta"
        }
        
        result, error = validate_request(body)
        
        assert error is None
        assert result == ("user123", "Mi respuesta", "chat123")
    
    def test_validate_request_missing_chatid(self):
        """Test que falla sin ChatID"""
        body = {
            "UserID": "user123",
            "prompt": "Mi respuesta"
        }
        
        result, error = validate_request(body)
        
        assert result is None
        assert error is not None
        assert error["statusCode"] == 400
    
    def test_validate_request_anonymous_user(self):
        """Test que usa ANONYMOUS_USER si no hay UserID"""
        body = {
            "ChatID": "chat123",
            "prompt": "Mi respuesta"
        }
        
        result, error = validate_request(body)
        
        assert error is None
        assert result[0] == "ANONYMOUS_USER"
    
    def test_validate_request_prompt_too_long(self):
        """Test que falla si el prompt es muy largo"""
        from lib.chat.config import MAX_USER_INPUT_CHARS
        
        body = {
            "ChatID": "chat123",
            "prompt": "a" * (MAX_USER_INPUT_CHARS + 1)
        }
        
        result, error = validate_request(body)
        
        assert result is None
        assert error is not None
        assert error["statusCode"] == 400
    
    def test_validate_request_prompt_exact_limit(self):
        """Test que acepta prompt en el límite exacto"""
        from lib.chat.config import MAX_USER_INPUT_CHARS
        
        body = {
            "ChatID": "chat123",
            "prompt": "a" * MAX_USER_INPUT_CHARS
        }
        
        result, error = validate_request(body)
        
        assert error is None
        assert result[1] == "a" * MAX_USER_INPUT_CHARS


class TestGetLastAssistantMessage:
    """Tests para get_last_assistant_message"""
    
    def test_get_last_message_basic(self):
        """Test obtención básica del último mensaje"""
        history = [
            "System: System prompt",
            "Usuario: Hola",
            "Asistente: Primera respuesta",
            "Usuario: Otra pregunta",
            "Asistente: Segunda respuesta"
        ]
        
        result = get_last_assistant_message(history)
        
        assert result == "Segunda respuesta"
    
    def test_get_last_message_no_assistant(self):
        """Test cuando no hay mensajes del asistente"""
        history = [
            "System: System prompt",
            "Usuario: Hola"
        ]
        
        result = get_last_assistant_message(history)
        
        assert result == ""
    
    def test_get_last_message_empty_history(self):
        """Test con historial vacío"""
        result = get_last_assistant_message([])
        
        assert result == ""
    
    def test_get_last_message_strips_whitespace(self):
        """Test que remueve espacios en blanco"""
        history = [
            "Asistente:   Respuesta con espacios   "
        ]
        
        result = get_last_assistant_message(history)
        
        assert result == "Respuesta con espacios"

