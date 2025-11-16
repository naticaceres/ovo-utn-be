"""
Unit tests para quota_service.py
"""
import os
import sys
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

# Ensure project root is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

import pytest
from lib.chat.quota_service import (
    handle_quota_check,
    revert_global_quota,
    check_quotas,
    get_quota_table
)


class TestHandleQuotaCheck:
    """Tests para handle_quota_check"""
    
    def test_handle_quota_check_success(self):
        """Test verificación exitosa de cuota"""
        mock_table = Mock()
        mock_table.update_item.return_value = {"Attributes": {"Count": 1}}
        
        # No debería lanzar excepción
        handle_quota_check(mock_table, "user123", "2024-01-01", 10)
        
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args[1]["Key"]["UserID"] == "user123"
        assert call_args[1]["Key"]["Date"] == "2024-01-01"
    
    def test_handle_quota_check_exceeds_limit(self):
        """Test que lanza excepción cuando se excede el límite"""
        mock_table = Mock()
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException"
            }
        }
        mock_table.update_item.side_effect = ClientError(error_response, "UpdateItem")
        
        with pytest.raises(ClientError):
            handle_quota_check(mock_table, "user123", "2024-01-01", 10)


class TestRevertGlobalQuota:
    """Tests para revert_global_quota"""
    
    def test_revert_global_quota_success(self):
        """Test reversión exitosa de cuota global"""
        from lib.chat.config import GLOBAL_USER_ID
        
        mock_table = Mock()
        
        revert_global_quota(mock_table, "2024-01-01")
        
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args[1]["Key"]["UserID"] == GLOBAL_USER_ID
        assert call_args[1]["Key"]["Date"] == "2024-01-01"
    
    def test_revert_global_quota_handles_exception(self):
        """Test que maneja excepciones silenciosamente"""
        mock_table = Mock()
        mock_table.update_item.side_effect = Exception("Database error")
        
        # No debería lanzar excepción
        revert_global_quota(mock_table, "2024-01-01")


class TestCheckQuotas:
    """Tests para check_quotas"""
    
    def test_check_quotas_success(self):
        """Test verificación exitosa de cuotas"""
        from lib.chat.config import GLOBAL_USER_ID, USER_REQUEST_LIMIT, GLOBAL_REQUEST_LIMIT
        
        mock_table = Mock()
        mock_table.update_item.return_value = {"Attributes": {"Count": 1}}
        
        result = check_quotas(mock_table, "user123", "2024-01-01")
        
        assert result is None  # Sin error
        assert mock_table.update_item.call_count == 2  # Global + User
    
    def test_check_quotas_global_exceeded(self):
        """Test cuando se excede la cuota global"""
        from lib.chat.config import GLOBAL_USER_ID, GLOBAL_REQUEST_LIMIT
        
        mock_table = Mock()
        # El código busca GLOBAL_USER_ID en str(e.response)
        # Necesitamos que el error incluya GLOBAL_USER_ID en su representación
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": f"Quota exceeded for {GLOBAL_USER_ID}"
            },
            "ResponseMetadata": {
                "RequestId": "test"
            }
        }
        # Crear un ClientError
        error = ClientError(error_response, "UpdateItem")
        error.response = error_response
        
        # Primera llamada (global) falla, segunda nunca se ejecuta
        mock_table.update_item.side_effect = [error]
        
        result = check_quotas(mock_table, "user123", "2024-01-01")
        
        assert result is not None
        assert result["statusCode"] == 429
        body = __import__("json").loads(result["body"])
        assert "Global Quota Exceeded" in body["error"]
    
    def test_check_quotas_user_exceeded(self):
        """Test cuando se excede la cuota de usuario"""
        from lib.chat.config import GLOBAL_USER_ID, USER_REQUEST_LIMIT
        
        mock_table = Mock()
        # El error de usuario NO debe incluir GLOBAL_USER_ID
        error_response = {
            "Error": {
                "Code": "ConditionalCheckFailedException",
                "Message": "User quota exceeded"
            }
        }
        error = ClientError(error_response, "UpdateItem")
        error.response = error_response
        
        # Primera llamada (global) OK, segunda (user) falla
        mock_table.update_item.side_effect = [
            {"Attributes": {"Count": 1}},  # Global OK
            error  # User fails
        ]
        
        result = check_quotas(mock_table, "user123", "2024-01-01")
        
        assert result is not None
        assert result["statusCode"] == 429
        body = __import__("json").loads(result["body"])
        assert "User Quota Exceeded" in body["error"]
        # Debería revertir la cuota global
        assert mock_table.update_item.call_count >= 3  # Global + User + Revert


class TestGetQuotaTable:
    """Tests para get_quota_table"""
    
    @patch('lib.chat.quota_service.dynamodb')
    def test_get_quota_table(self, mock_dynamodb):
        """Test obtención de tabla de cuotas"""
        from lib.chat.config import QUOTA_TABLE_NAME
        
        mock_table = Mock()
        mock_dynamodb.Table.return_value = mock_table
        
        result = get_quota_table()
        
        assert result == mock_table
        mock_dynamodb.Table.assert_called_once_with(QUOTA_TABLE_NAME)

