"""
Configuration module for PDF Info Retrieval application.

This module centralizes all configuration settings, constants, and
environment variable handling for the application.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class Config:
    """
    Application configuration class.

    Centralizes all configurable parameters including text processing,
    embedding models, and LLM settings.
    """

    # Text Processing Settings
    chunk_size: int = 1500
    min_response_length: int = 30

    # Academic Section Headers for Chunking
    academic_headers: List[str] = field(default_factory=lambda: [
        "Abstract",
        "Introduction",
        "Methods",
        "Methodology",
        "Results",
        "Discussion",
        "Conclusion",
    ])

    # Text Cleaning Patterns
    cleaning_patterns: List[str] = field(default_factory=lambda: [
        r'\b[\w.-]+?@\w+?\.\w+?\b',  # Email addresses
        r'\[[^\]]*\]',                 # Text in square brackets
        r'Figure \d+: [^\n]+',         # Figure captions
        r'Table \d+: [^\n]+',          # Table captions
        r'^Source:.*$',                # Source lines
        r'[^\x00-\x7F]+',              # Non-ASCII characters
        r'\bSee Figure \d+\b',         # References to figures
        r'\bEq\.\s*\d+\b',             # Equation references
        r'\b(Table|Fig)\.\s*\d+\b',    # Other reference styles
        r'<[^>]+>',                     # HTML tags
    ])

    # Embedding Model Settings
    embedding_model_type: str = "openai"  # 'openai' or 'huggingface'
    huggingface_model_name: Optional[str] = None

    # LLM Settings
    llm_model_name: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7

    # Vector Store Settings
    vector_store_type: str = "faiss"

    # UI Settings
    page_title: str = "ResearchAI: Answer Extraction from Research Papers"
    page_icon: str = ":books:"

    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = None
    huggingface_api_token: Optional[str] = None

    def __post_init__(self):
        """Load environment variables after initialization."""
        self._load_env_variables()

    def _load_env_variables(self):
        """Load API keys and tokens from environment variables or Streamlit secrets."""
        load_dotenv()

        # Try environment variables first
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

        # Fall back to Streamlit secrets if available
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                if not self.openai_api_key and 'OPENAI_API_KEY' in st.secrets:
                    self.openai_api_key = st.secrets['OPENAI_API_KEY']
                    os.environ['OPENAI_API_KEY'] = self.openai_api_key
                if not self.huggingface_api_token and 'HUGGINGFACEHUB_API_TOKEN' in st.secrets:
                    self.huggingface_api_token = st.secrets['HUGGINGFACEHUB_API_TOKEN']
        except Exception:
            pass  # Streamlit not available or no secrets

    @property
    def header_pattern(self) -> str:
        """Generate regex pattern for academic section headers."""
        headers = "|".join(self.academic_headers)
        return rf'\n\s*({headers})\s*\n'

    @property
    def section_pattern(self) -> str:
        """Generate regex pattern for matching section names."""
        headers = "|".join(self.academic_headers)
        return rf'^({headers})$'

    def validate(self) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        if self.embedding_model_type == "openai" and not self.openai_api_key:
            return False
        if self.embedding_model_type == "huggingface" and not self.huggingface_api_token:
            return False
        return True

    def get_missing_keys(self) -> List[str]:
        """
        Get list of missing required API keys.

        Returns:
            List[str]: Names of missing API keys.
        """
        missing = []
        if self.embedding_model_type == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if self.embedding_model_type == "huggingface" and not self.huggingface_api_token:
            missing.append("HUGGINGFACEHUB_API_TOKEN")
        return missing


# Default configuration instance
default_config = Config()
