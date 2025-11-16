"""
Unit tests para dynamodb_service.py
"""
import os
import sys
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
from lib.chat.dynamodb_service import (
    get_aptitudes_from_table,
    get_chat_state,
    save_chat_progress
)


class TestGetAptitudesFromTable:
    """Tests para get_aptitudes_from_table"""
    
    @patch('lib.chat.dynamodb_service.dynamodb')
    def test_get_aptitudes_success(self, mock_dynamodb):
        """Test obtención exitosa de aptitudes"""
        mock_table = Mock()
        mock_table.scan.return_value = {
            "Items": [
                {"aptitud": "Creatividad", "activa": True},
                {"aptitud": "Liderazgo", "activa": True},
                {"aptitud": "Trabajo en equipo", "activa": True}
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        
        aptitudes = get_aptitudes_from_table()
        
        assert len(aptitudes) == 3
        assert "Creatividad" in aptitudes
        assert "Liderazgo" in aptitudes
        assert "Trabajo en equipo" in aptitudes
        mock_table.scan.assert_called_once()
    
    @patch('lib.chat.dynamodb_service.dynamodb')
    def test_get_aptitudes_filters_inactive(self, mock_dynamodb):
        """Test que filtra aptitudes inactivas
        
        Nota: El filtrado se hace en DynamoDB con FilterExpression,
        así que el mock debe devolver solo las activas.
        """
        mock_table = Mock()
        # DynamoDB ya filtra con FilterExpression, así que solo devuelve activas
        mock_table.scan.return_value = {
            "Items": [
                {"aptitud": "Creatividad", "activa": True}
            ]
        }
        mock_dynamodb.Table.return_value = mock_table
        
        aptitudes = get_aptitudes_from_table()
        
        assert len(aptitudes) == 1
        assert "Creatividad" in aptitudes
    
    @patch('lib.chat.dynamodb_service.dynamodb')
    def test_get_aptitudes_empty_table(self, mock_dynamodb):
        """Test con tabla vacía"""
        mock_table = Mock()
        mock_table.scan.return_value = {"Items": []}
        mock_dynamodb.Table.return_value = mock_table
        
        aptitudes = get_aptitudes_from_table()
        
        assert aptitudes == []
    
    @patch('lib.chat.dynamodb_service.dynamodb')
    def test_get_aptitudes_raises_exception(self, mock_dynamodb):
        """Test que propaga excepciones"""
        mock_table = Mock()
        mock_table.scan.side_effect = Exception("Database error")
        mock_dynamodb.Table.return_value = mock_table
        
        with pytest.raises(Exception):
            get_aptitudes_from_table()


class TestGetChatState:
    """Tests para get_chat_state"""
    
    @patch('lib.chat.dynamodb_service.get_aptitudes_from_table')
    def test_get_chat_state_new_chat(self, mock_get_aptitudes):
        """Test obtención de estado para chat nuevo"""
        mock_get_aptitudes.return_value = ["Creatividad", "Liderazgo", "Trabajo en equipo"]
        
        mock_table = Mock()
        mock_table.get_item.return_value = {}  # No Item = chat nuevo
        
        history, next_q, is_finished, scores, total, is_new = get_chat_state(
            mock_table, "new_chat"
        )
        
        assert is_new is True
        assert next_q == 1
        assert is_finished is False
        assert scores is None
        assert total == 3
        assert len(history) == 1
        assert history[0].startswith("System:")
    
    @patch('lib.chat.dynamodb_service.get_aptitudes_from_table')
    def test_get_chat_state_existing_chat(self, mock_get_aptitudes):
        """Test obtención de estado para chat existente"""
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "ChatID": "existing_chat",
                "UserID": "user123",
                "QuestionNumber": 3,
                "Status": "IN_PROGRESS",
                "History": [
                    "System: System prompt",
                    "Usuario: Hola",
                    "Asistente: Respuesta"
                ],
                "TotalQuestions": 5
            }
        }
        
        history, next_q, is_finished, scores, total, is_new = get_chat_state(
            mock_table, "existing_chat"
        )
        
        assert is_new is False
        assert next_q == 3
        assert is_finished is False
        assert len(history) == 3
        assert total == 5
    
    @patch('lib.chat.dynamodb_service.get_aptitudes_from_table')
    def test_get_chat_state_finished_chat(self, mock_get_aptitudes):
        """Test obtención de estado para chat finalizado"""
        mock_table = Mock()
        mock_table.get_item.return_value = {
            "Item": {
                "ChatID": "finished_chat",
                "Status": "FINISHED",
                "QuestionNumber": 6,
                "History": ["System: prompt"],
                "FinalScores": {"Creatividad": "8", "Liderazgo": "7"},
                "TotalQuestions": 5
            }
        }
        
        history, next_q, is_finished, scores, total, is_new = get_chat_state(
            mock_table, "finished_chat"
        )
        
        assert is_finished is True
        assert scores == {"Creatividad": "8", "Liderazgo": "7"}
    
    @patch('lib.chat.dynamodb_service.get_aptitudes_from_table')
    def test_get_chat_state_no_aptitudes(self, mock_get_aptitudes):
        """Test que lanza excepción si no hay aptitudes"""
        mock_get_aptitudes.return_value = []
        
        mock_table = Mock()
        mock_table.get_item.return_value = {}
        
        with pytest.raises(Exception) as exc_info:
            get_chat_state(mock_table, "new_chat")
        
        assert "aptitudes" in str(exc_info.value).lower()


class TestSaveChatProgress:
    """Tests para save_chat_progress"""
    
    def test_save_chat_progress_in_progress(self):
        """Test guardado de progreso en curso"""
        mock_table = Mock()
        
        history = ["System: prompt", "Usuario: Hola"]
        status = save_chat_progress(
            mock_table, "chat123", "user123", history, 
            False, 2, None, 5
        )
        
        assert status == "Waiting for 3 of 5"
        mock_table.put_item.assert_called_once()
        
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        assert item["ChatID"] == "chat123"
        assert item["UserID"] == "user123"
        assert item["QuestionNumber"] == 3
        assert item["Status"] == "IN_PROGRESS"
        assert item["TotalQuestions"] == 5
    
    def test_save_chat_progress_finished(self):
        """Test guardado de progreso finalizado"""
        mock_table = Mock()
        
        history = ["System: prompt", "Usuario: Última respuesta"]
        final_scores = {"Creatividad": 8, "Liderazgo": 7}
        status = save_chat_progress(
            mock_table, "chat123", "user123", history,
            True, 5, final_scores, 5
        )
        
        assert status == "FINISHED"
        mock_table.put_item.assert_called_once()
        
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        assert item["Status"] == "FINISHED"
        assert item["QuestionNumber"] == 6  # total_questions + 1
        assert item["FinalScores"] == {"Creatividad": "8", "Liderazgo": "7"}  # Convertidos a strings
    
    def test_save_chat_progress_finished_no_scores(self):
        """Test guardado finalizado sin scores"""
        mock_table = Mock()
        
        status = save_chat_progress(
            mock_table, "chat123", "user123", [],
            True, 5, None, 5
        )
        
        assert status == "FINISHED"
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]
        assert item["FinalScores"] == {}

