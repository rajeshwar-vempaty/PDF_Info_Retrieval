"""
Document Analyzer module for automatic document analysis.

This module provides functionality for analyzing documents
and extracting insights like keywords, statistics, and summaries.
"""

import re
import logging
from typing import List, Dict, Optional
from collections import Counter

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from src.config import Config, default_config

logger = logging.getLogger(__name__)

# Common English stopwords
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
    'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'where', 'when',
    'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
    'into', 'through', 'during', 'before', 'after', 'above', 'below',
    'between', 'under', 'again', 'further', 'then', 'once', 'et', 'al',
    'fig', 'figure', 'table', 'see', 'using', 'used', 'use', 'based',
    'however', 'therefore', 'thus', 'hence', 'although', 'while', 'since',
    'because', 'if', 'when', 'where', 'which', 'who', 'whom', 'whose',
    'about', 'against', 'over', 'up', 'down', 'out', 'off', 'any', 'many'
}


class DocumentAnalyzer:
    """
    Analyzes documents to extract insights and statistics.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config
        self._llm = None

    def _get_llm(self):
        """Get or create LLM instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.config.llm_model_name,
                temperature=0.3
            )
        return self._llm

    def get_document_stats(self, text: str) -> Dict:
        """
        Calculate document statistics.

        Args:
            text: The document text.

        Returns:
            Dict with statistics.
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        word_count = len(words)
        # Average reading speed: 200-250 words per minute
        reading_time = max(1, round(word_count / 200))

        return {
            'words': f"{word_count:,}",
            'characters': f"{len(text):,}",
            'sentences': f"{len(sentences):,}",
            'reading_time': f"{reading_time} min"
        }

    def extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """
        Extract top keywords from text.

        Args:
            text: The document text.
            top_n: Number of keywords to return.

        Returns:
            List of keywords.
        """
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter stopwords and count
        filtered_words = [w for w in words if w not in STOPWORDS]
        word_counts = Counter(filtered_words)

        # Get top keywords
        keywords = [word for word, count in word_counts.most_common(top_n)]

        return keywords

    def generate_summary(self, text: str) -> str:
        """
        Generate a brief summary of the document.

        Args:
            text: The document text.

        Returns:
            Summary string.
        """
        try:
            llm = self._get_llm()

            # Use first 4000 characters for summary
            text_sample = text[:4000]

            prompt = PromptTemplate(
                input_variables=["text"],
                template="""Analyze this document and provide a brief summary in 2-3 sentences.
Focus on the main topic and key points.

Document:
{text}

Summary:"""
            )

            response = llm.invoke(prompt.format(text=text_sample))
            return response.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return "Summary generation failed. Please try again."

    def generate_suggested_questions(self, text: str) -> List[str]:
        """
        Generate suggested questions based on document content.

        Args:
            text: The document text.

        Returns:
            List of suggested questions.
        """
        try:
            llm = self._get_llm()

            # Use first 3000 characters
            text_sample = text[:3000]

            prompt = PromptTemplate(
                input_variables=["text"],
                template="""Based on this document, suggest 5 insightful questions that a reader might want to ask.
Make the questions specific to the content.

Document:
{text}

Return only the questions, one per line, without numbering:"""
            )

            response = llm.invoke(prompt.format(text=text_sample))
            questions = response.content.strip().split('\n')
            questions = [q.strip().lstrip('•-123456789.') .strip() for q in questions if q.strip()]

            return questions[:5]

        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return [
                "What is the main topic of this document?",
                "What are the key findings?",
                "What methodology was used?",
                "What are the conclusions?",
                "What are the implications?"
            ]

    def analyze_document(self, text: str, generate_ai_insights: bool = True) -> Dict:
        """
        Perform comprehensive document analysis.

        Args:
            text: The document text.
            generate_ai_insights: Whether to generate AI-powered insights.

        Returns:
            Dict with all analysis results.
        """
        analysis = {
            'stats': self.get_document_stats(text),
            'keywords': self.extract_keywords(text),
        }

        if generate_ai_insights:
            analysis['summary'] = self.generate_summary(text)
            analysis['suggested_questions'] = self.generate_suggested_questions(text)

        return analysis
