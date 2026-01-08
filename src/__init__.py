"""
PaperMind - AI-Powered Research Paper Analysis

This package provides a RAG (Retrieval-Augmented Generation) based system
for extracting and querying information from PDF research documents with
advanced features like:
- Automatic section detection
- Technical term glossary
- Equation explanations
- Figure and table analysis
"""

from src.config import Config
from src.pdf_processor import PDFProcessor
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager
from src.conversation import ConversationManager
from src.document_analyzer import DocumentAnalyzer
from src.paper_analyzer import PaperAnalyzer

__version__ = "2.0.0"
__author__ = "Rajeshwar Vempaty"

__all__ = [
    "Config",
    "PDFProcessor",
    "TextProcessor",
    "VectorStoreManager",
    "ConversationManager",
    "DocumentAnalyzer",
    "PaperAnalyzer",
]
