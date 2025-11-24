"""
Unit test para validar el formato exacto del payload de Bedrock.

Este test asegura que cualquier cambio en el formato del payload que cause
ValidationException sea detectado inmediatamente.

Referencias oficiales:
- AWS Bedrock Messages API Format: https://docs.aws.amazon.com/bedrock/latest/userguide/api-messages.html
- AWS Bedrock Inference Parameters: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-parameters.html
- Amazon Nova Micro: Modelo fundacional generativo text-only que usa formato Messages API
"""
import os
import sys
import json
from unittest.mock import Mock, patch

# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

import pytest
from lib.chat.bedrock_client import call_bedrock
from lib.chat.config import BEDROCK_MODEL_ID


class TestBedrockPayloadFormat:
    """
    Test que valida el formato exacto del payload de Bedrock.
    
    Este test valida que el payload cumple con el formato requerido por
    Amazon Nova Micro v1:0, que usa el formato Messages API de Bedrock.
    
    Cualquier cambio que cause ValidationException será detectado aquí.
    """
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_payload_format_matches_expected_structure(self, mock_bedrock):
        """
        Valida que el payload tenga exactamente el formato esperado por Nova Micro.
        
        Este test verifica:
        1. Campos que NO deben existir (causan ValidationException)
        2. Campos que SÍ deben existir con estructura correcta
        3. Valores críticos de configuración
        4. Estructura de messages y inferenceConfig
        """
        # Mock response
        mock_response_body = {
            "output": {
                "message": {
                    "content": [{"text": "Test response"}]
                }
            }
        }
        mock_body = Mock()
        mock_body.read.return_value = json.dumps(mock_response_body).encode()
        mock_bedrock.invoke_model.return_value = {"body": mock_body}
        
        # Test con mensajes normales
        messages = [
            {"role": "user", "content": [{"text": "System prompt"}]},
            {"role": "user", "content": [{"text": "User message"}]},
            {"role": "assistant", "content": [{"text": "Assistant response"}]}
        ]
        call_bedrock(messages, is_final_analysis=False)
        
        call_args = mock_bedrock.invoke_model.call_args
        payload = json.loads(call_args[1]["body"])
        
        # ============================================================
        # VALIDACIONES CRÍTICAS: Campos que NO deben existir
        # ============================================================
        # Estos campos causan ValidationException en Nova Micro
        assert "schemaVersion" not in payload, (
            "CRÍTICO: El payload NO debe contener 'schemaVersion'. "
            "Amazon Nova Micro no lo soporta y causa ValidationException."
        )
        assert "system" not in payload, (
            "CRÍTICO: El payload NO debe contener campo 'system' separado. "
            "El system prompt debe ir como primer mensaje en el array 'messages'."
        )
        
        # ============================================================
        # VALIDACIONES CRÍTICAS: Campos requeridos
        # ============================================================
        assert "messages" in payload, "El payload debe contener 'messages'"
        assert "inferenceConfig" in payload, "El payload debe contener 'inferenceConfig'"
        
        # ============================================================
        # VALIDACIÓN: Estructura de messages
        # ============================================================
        assert isinstance(payload["messages"], list), "messages debe ser un array"
        assert len(payload["messages"]) > 0, "messages no debe estar vacío"
        
        for msg in payload["messages"]:
            assert "role" in msg, "Cada mensaje debe tener 'role'"
            assert msg["role"] in ["user", "assistant"], f"role debe ser 'user' o 'assistant', no '{msg['role']}'"
            assert "content" in msg, "Cada mensaje debe tener 'content'"
            assert isinstance(msg["content"], list), "content debe ser un array"
            assert len(msg["content"]) > 0, "content no debe estar vacío"
            
            for content_item in msg["content"]:
                assert "text" in content_item, "Cada elemento en content debe tener 'text'"
                assert isinstance(content_item["text"], str), "text debe ser string"
        
        # ============================================================
        # VALIDACIÓN: inferenceConfig con valores exactos
        # ============================================================
        inference_config = payload["inferenceConfig"]
        
        # Campos requeridos
        assert "maxTokens" in inference_config, "inferenceConfig debe tener 'maxTokens'"
        assert "temperature" in inference_config, "inferenceConfig debe tener 'temperature'"
        assert "topP" in inference_config, "inferenceConfig debe tener 'topP'"
        assert "stopSequences" in inference_config, "inferenceConfig debe tener 'stopSequences'"
        
        # Valores exactos configurados (cualquier cambio puede romper)
        assert inference_config["maxTokens"] == 200, "maxTokens debe ser 200"
        assert inference_config["temperature"] == 0.1, "temperature debe ser 0.1"
        assert inference_config["topP"] == 0.9, "topP debe ser 0.9"
        
        # stopSequences: valores exactos que funcionan
        expected_stop_sequences = [
            "Usuario:",
            "Asistente:",
            "\n\n**Pregunta",
            "\nPregunta ",
            "Una vez finalizada",
            "Procederé a generar"
        ]
        assert inference_config["stopSequences"] == expected_stop_sequences, (
            f"stopSequences debe ser exactamente {expected_stop_sequences}. "
            f"Cambios aquí pueden causar ValidationException."
        )
        
        # ============================================================
        # VALIDACIÓN: toolConfig NO debe existir en modo normal
        # ============================================================
        assert "toolConfig" not in payload, (
            "El payload NO debe contener 'toolConfig' cuando is_final_analysis=False"
        )
        
        # ============================================================
        # VALIDACIÓN: invoke_model llamado con parámetros correctos
        # ============================================================
        call_kwargs = call_args[1] if len(call_args) > 1 else {}
        assert call_kwargs["modelId"] == BEDROCK_MODEL_ID, f"modelId debe ser '{BEDROCK_MODEL_ID}'"
        assert call_kwargs["accept"] == "application/json", "accept debe ser 'application/json'"
        assert call_kwargs["contentType"] == "application/json", "contentType debe ser 'application/json'"
    
    @patch('lib.chat.bedrock_client.bedrock')
    def test_payload_format_with_final_analysis(self, mock_bedrock):
        """
        Valida el formato del payload cuando is_final_analysis=True.
        
        Verifica que toolConfig tenga la estructura correcta para structured outputs.
        """
        # Mock response con toolUse
        mock_response_body = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "aptitudes_scores": {"Aptitud1": 8}
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
        aptitudes = ["Creatividad", "Liderazgo"]
        call_bedrock(messages, is_final_analysis=True, aptitudes=aptitudes)
        
        call_args = mock_bedrock.invoke_model.call_args
        payload = json.loads(call_args[1]["body"])
        
        # Validaciones base (igual que el test anterior)
        assert "schemaVersion" not in payload, "NO debe tener schemaVersion"
        assert "system" not in payload, "NO debe tener campo system separado"
        assert "messages" in payload, "Debe tener messages"
        assert "inferenceConfig" in payload, "Debe tener inferenceConfig"
        
        # Validación específica: toolConfig debe existir
        assert "toolConfig" in payload, "El payload debe contener 'toolConfig' cuando is_final_analysis=True"
        
        tool_config = payload["toolConfig"]
        assert "toolChoice" in tool_config, "toolConfig debe tener 'toolChoice'"
        assert "tools" in tool_config, "toolConfig debe tener 'tools'"
        
        # Estructura de toolChoice
        assert "tool" in tool_config["toolChoice"], "toolChoice debe tener 'tool'"
        assert tool_config["toolChoice"]["tool"]["name"] == "final_analysis", (
            "El nombre del tool debe ser 'final_analysis'"
        )
        
        # Estructura de tools
        assert isinstance(tool_config["tools"], list), "tools debe ser un array"
        assert len(tool_config["tools"]) > 0, "tools no debe estar vacío"
        
        tool_spec = tool_config["tools"][0]
        assert "toolSpec" in tool_spec, "Cada tool debe tener 'toolSpec'"
        assert "name" in tool_spec["toolSpec"], "toolSpec debe tener 'name'"
        assert "inputSchema" in tool_spec["toolSpec"], "toolSpec debe tener 'inputSchema'"
        assert "json" in tool_spec["toolSpec"]["inputSchema"], "inputSchema debe tener 'json'"
