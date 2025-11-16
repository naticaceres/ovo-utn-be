"""
Unit tests para bedrock_client.py
"""
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

import pytest
from lib.chat.bedrock_client import build_messages_from_history, call_bedrock


class TestBuildMessagesFromHistory:
    """Tests para build_messages_from_history"""
    
    def test_build_messages_with_system_prompt(self):
        """Test construcción de mensajes con system prompt"""
        history = [
            "System: Eres un asistente útil",
            "Usuario: Hola",
            "Asistente: Hola, ¿cómo puedo ayudarte?"
        ]
        
        messages = build_messages_from_history(history)
        
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"][0]["text"] == "Eres un asistente útil"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"][0]["text"] == "Hola"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"][0]["text"] == "Hola, ¿cómo puedo ayudarte?"
    
    def test_build_messages_only_user(self):
        """Test construcción con solo mensajes de usuario"""
        history = [
            "Usuario: Primera pregunta",
            "Usuario: Segunda pregunta"
        ]
        
        messages = build_messages_from_history(history)
        
        assert len(messages) == 2
        assert all(msg["role"] == "user" for msg in messages)
    
    def test_build_messages_only_assistant(self):
        """Test construcción con solo mensajes del asistente"""
        history = [
            "Asistente: Primera respuesta",
            "Asistente: Segunda respuesta"
        ]
        
        messages = build_messages_from_history(history)
        
        assert len(messages) == 2
        assert all(msg["role"] == "assistant" for msg in messages)
    
    def test_build_messages_ignores_unknown_prefixes(self):
        """Test que ignora líneas sin prefijos conocidos"""
        history = [
            "System: System prompt",
            "Línea sin prefijo",
            "Usuario: Hola"
        ]
        
        messages = build_messages_from_history(history)
        
        assert len(messages) == 2
        assert messages[1]["content"][0]["text"] == "Hola"
    
    def test_build_messages_empty_history(self):
        """Test con historial vacío"""
        messages = build_messages_from_history([])
        
        assert messages == []
    
    def test_build_messages_strips_whitespace(self):
        """Test que remueve espacios en blanco"""
        history = [
            "System:   System prompt con espacios   ",
            "Usuario:   Usuario con espacios   "
        ]
        
        messages = build_messages_from_history(history)
        
        assert messages[0]["content"][0]["text"] == "System prompt con espacios"
        assert messages[1]["content"][0]["text"] == "Usuario con espacios"


class TestCallBedrock:
    """Tests para call_bedrock"""
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_normal_response(self, mock_bedrock):
        """Test invocación normal de Bedrock"""
        # Mock response
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Esta es una pregunta del chatbot"}
                    ]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        messages = [
            {"role": "user", "content": [{"text": "Inicia"}]}
        ]
        
        response, scores = call_bedrock(messages, is_final_analysis=False)
        
        assert response == "Esta es una pregunta del chatbot"
        assert scores is None
        mock_bedrock.invoke_model.assert_called_once()
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_final_analysis(self, mock_bedrock):
        """Test invocación con análisis final (structured output)"""
        # Mock response con toolUse
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "aptitudes_scores": {
                                        "Creatividad": 8,
                                        "Liderazgo": 7
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        messages = [
            {"role": "user", "content": [{"text": "System prompt"}]},
            {"role": "user", "content": [{"text": "Última respuesta"}]}
        ]
        
        response, scores = call_bedrock(messages, is_final_analysis=True)
        
        assert response == ""
        assert scores == {"Creatividad": 8, "Liderazgo": 7}
        mock_bedrock.invoke_model.assert_called_once()
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_empty_messages_list(self, mock_bedrock):
        """Test que agrega mensaje por defecto si messages_list está vacío"""
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Respuesta"}
                    ]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        response, scores = call_bedrock([], is_final_analysis=False)
        
        # Verificar que se llamó con un mensaje por defecto
        call_args = mock_bedrock.invoke_model.call_args
        payload = json.loads(call_args[1]["body"])
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_payload_structure(self, mock_bedrock):
        """Test que el payload tiene la estructura correcta"""
        mock_response_body = {
            "output": {
                "message": {
                    "content": [{"text": "Respuesta"}]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        messages = [{"role": "user", "content": [{"text": "Test"}]}]
        call_bedrock(messages, is_final_analysis=False)
        
        call_args = mock_bedrock.invoke_model.call_args
        payload = json.loads(call_args[1]["body"])
        
        assert "messages" in payload
        assert "inferenceConfig" in payload
        assert payload["inferenceConfig"]["maxTokens"] == 200
        assert payload["inferenceConfig"]["temperature"] == 0.1
        assert "stopSequences" in payload["inferenceConfig"]
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_with_tool_config(self, mock_bedrock):
        """Test que toolConfig se agrega cuando is_final_analysis=True"""
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "aptitudes_scores": {}
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        messages = [{"role": "user", "content": [{"text": "Test"}]}]
        call_bedrock(messages, is_final_analysis=True)
        
        call_args = mock_bedrock.invoke_model.call_args
        payload = json.loads(call_args[1]["body"])
        
        assert "toolConfig" in payload
        assert payload["toolConfig"]["toolChoice"]["tool"]["name"] == "final_analysis"
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_call_bedrock_final_analysis_no_tooluse(self, mock_bedrock):
        """Test que lanza excepción si no hay toolUse en análisis final"""
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {"text": "Respuesta sin toolUse"}
                    ]
                }
            }
        }
        
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        messages = [{"role": "user", "content": [{"text": "Test"}]}]
        
        with pytest.raises(Exception) as exc_info:
            call_bedrock(messages, is_final_analysis=True)
        
        assert "toolUse" in str(exc_info.value)

