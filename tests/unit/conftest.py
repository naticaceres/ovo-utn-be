"""
Configuración compartida para tests unitarios.

Este archivo se ejecuta automáticamente por pytest antes de los tests.
Se usa para configurar mocks globales y fixtures compartidas.
"""
import os
import sys
from unittest.mock import MagicMock

# Ensure project root and lib/chat are importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../.."))
LIB_CHAT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "lib", "chat"))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if LIB_CHAT_DIR not in sys.path:
    sys.path.insert(0, LIB_CHAT_DIR)

# Mock boto3 before any modules import it
# NO mockear botocore.exceptions para que ClientError funcione correctamente en tests
sys.modules['boto3'] = MagicMock()

# Create mock boto3 clients
mock_boto3 = sys.modules['boto3']
mock_boto3.resource = MagicMock()
mock_boto3.client = MagicMock()

