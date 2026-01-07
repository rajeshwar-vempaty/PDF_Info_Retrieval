"""
Tests for the configuration module.
"""

import pytest
from unittest.mock import patch
from src.config import Config


class TestConfig:
    """Test cases for the Config class."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = Config()

        assert config.chunk_size == 1500
        assert config.min_response_length == 30
        assert config.embedding_model_type == "openai"
        assert config.llm_model_name == "gpt-3.5-turbo"
        assert config.llm_temperature == 0.7
        assert config.vector_store_type == "faiss"

    def test_academic_headers(self):
        """Test that academic headers are configured correctly."""
        config = Config()

        expected_headers = [
            "Abstract",
            "Introduction",
            "Methods",
            "Methodology",
            "Results",
            "Discussion",
            "Conclusion",
        ]
        assert config.academic_headers == expected_headers

    def test_cleaning_patterns(self):
        """Test that cleaning patterns are configured."""
        config = Config()

        assert len(config.cleaning_patterns) > 0
        # Check for email pattern
        assert any('email' in p or '@' in p for p in config.cleaning_patterns)

    def test_header_pattern_property(self):
        """Test header pattern regex generation."""
        config = Config()

        pattern = config.header_pattern
        assert "Abstract" in pattern
        assert "Introduction" in pattern
        assert "Conclusion" in pattern

    def test_section_pattern_property(self):
        """Test section pattern regex generation."""
        config = Config()

        pattern = config.section_pattern
        assert pattern.startswith("^")
        assert pattern.endswith("$")

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_load_env_variables(self):
        """Test environment variable loading."""
        config = Config()
        config._load_env_variables()

        assert config.openai_api_key == 'test-key'

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_validate_with_openai_key(self):
        """Test validation passes with OpenAI key present."""
        config = Config()
        config.embedding_model_type = "openai"
        config._load_env_variables()

        assert config.validate() is True

    def test_validate_without_keys(self):
        """Test validation fails without required keys."""
        config = Config()
        config.openai_api_key = None
        config.embedding_model_type = "openai"

        assert config.validate() is False

    def test_get_missing_keys(self):
        """Test getting list of missing API keys."""
        config = Config()
        config.openai_api_key = None
        config.embedding_model_type = "openai"

        missing = config.get_missing_keys()
        assert "OPENAI_API_KEY" in missing

    def test_custom_chunk_size(self):
        """Test creating config with custom chunk size."""
        config = Config(chunk_size=2000)

        assert config.chunk_size == 2000
