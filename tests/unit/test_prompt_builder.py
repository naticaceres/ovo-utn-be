"""
Unit tests para prompt_builder.py
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
from lib.chat.prompt_builder import build_dynamic_master_prompt, get_final_analysis_schema


class TestBuildDynamicMasterPrompt:
    """Tests para build_dynamic_master_prompt"""
    
    def test_build_prompt_with_single_aptitude(self):
        """Test que el prompt se construye correctamente con una aptitud"""
        aptitudes = ["Creatividad"]
        prompt = build_dynamic_master_prompt(aptitudes)
        
        assert "Creatividad" in prompt
        assert "1 preguntas" in prompt or "1 pregunta" in prompt
        assert "**ROL (ÚNICO E INNEGOCIABLE):**" in prompt
        assert "|| 1 | **Creatividad** |" in prompt
    
    def test_build_prompt_with_multiple_aptitudes(self):
        """Test que el prompt se construye correctamente con múltiples aptitudes"""
        aptitudes = ["Creatividad", "Trabajo en equipo", "Liderazgo"]
        prompt = build_dynamic_master_prompt(aptitudes)
        
        assert "Creatividad" in prompt
        assert "Trabajo en equipo" in prompt
        assert "Liderazgo" in prompt
        assert "3 preguntas" in prompt or "3 pregunta" in prompt
        assert "|| 1 | **Creatividad** |" in prompt
        assert "|| 2 | **Trabajo en equipo** |" in prompt
        assert "|| 3 | **Liderazgo** |" in prompt
    
    def test_build_prompt_includes_student_profile(self):
        """Test que el prompt incluye el perfil de estudiante"""
        aptitudes = ["Creatividad"]
        prompt = build_dynamic_master_prompt(aptitudes)
        
        assert "ESTUDIANTE" in prompt
        assert "experiencia profesional" in prompt.lower()
        assert "ACADÉMICAS" in prompt or "académicas" in prompt
    
    def test_build_prompt_includes_final_analysis_instructions(self):
        """Test que el prompt incluye instrucciones para el análisis final"""
        aptitudes = ["Creatividad"]
        prompt = build_dynamic_master_prompt(aptitudes)
        
        assert "ANÁLISIS FINAL" in prompt
        assert "final_scores" in prompt.lower()
    
    def test_build_prompt_includes_welcome_and_first_question_instruction(self):
        """Test que el prompt incluye instrucciones para incluir bienvenida y primera pregunta"""
        aptitudes = ["Creatividad"]
        prompt = build_dynamic_master_prompt(aptitudes)
        
        assert "bienvenida" in prompt.lower()
        assert "primera pregunta" in prompt.lower()
        assert "INICIO DE LA INTERACCIÓN" in prompt


class TestGetFinalAnalysisSchema:
    """Tests para get_final_analysis_schema"""
    
    def test_schema_structure(self):
        """Test que el schema tiene la estructura correcta"""
        schema = get_final_analysis_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
    
    def test_schema_has_aptitudes_scores(self):
        """Test que el schema incluye aptitudes_scores"""
        schema = get_final_analysis_schema()
        
        assert "aptitudes_scores" in schema["properties"]
        assert "aptitudes_scores" in schema["required"]
    
    def test_aptitudes_scores_properties(self):
        """Test que aptitudes_scores tiene las propiedades correctas"""
        schema = get_final_analysis_schema()
        aptitudes_scores = schema["properties"]["aptitudes_scores"]
        
        assert aptitudes_scores["type"] == "object"
        assert "additionalProperties" in aptitudes_scores
        assert aptitudes_scores["additionalProperties"]["type"] == "number"
        assert aptitudes_scores["additionalProperties"]["minimum"] == 1
        assert aptitudes_scores["additionalProperties"]["maximum"] == 10
    
    def test_schema_no_conclusion(self):
        """Test que el schema NO incluye conclusion (solo aptitudes_scores)"""
        schema = get_final_analysis_schema()
        
        assert "conclusion" not in schema["properties"]

