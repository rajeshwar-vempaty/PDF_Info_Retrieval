"""
PDF Info Retrieval - Interactive PDF Knowledge Extraction System

This package provides a RAG (Retrieval-Augmented Generation) based system
for extracting and querying information from PDF documents.
"""

from src.config import Config
from src.pdf_processor import PDFProcessor
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager
from src.conversation import ConversationManager

__version__ = "1.0.0"
__author__ = "PDF Info Retrieval Team"

__all__ = [
    "Config",
    "PDFProcessor",
    "TextProcessor",
    "VectorStoreManager",
    "ConversationManager",
]
