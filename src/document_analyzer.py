"""
Document Analyzer module for extracting document-level insights.

This module provides functionality for analyzing document text to produce
statistics, summaries, keywords, and suggested questions.
"""

import re
import logging
import math
from typing import Optional, List, Dict, Any
from collections import Counter

from src.config import Config, default_config

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analyzes document text to extract statistics, keywords, summary, and
    suggested questions.

    Usage in app_enhanced.py:
        analyzer = DocumentAnalyzer(config)
        analysis = analyzer.analyze_document(text)
        # analysis keys: 'stats', 'summary', 'keywords', 'suggested_questions'
    """

    # Common English stopwords to exclude from keyword extraction
    STOPWORDS = frozenset([
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'shall', 'can', 'need', 'dare',
        'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those',
        'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'she', 'they',
        'them', 'their', 'what', 'which', 'who', 'when', 'where', 'how',
        'not', 'no', 'nor', 'as', 'if', 'then', 'than', 'too', 'very',
        'also', 'just', 'about', 'above', 'after', 'again', 'all', 'am',
        'any', 'because', 'before', 'below', 'between', 'both', 'each',
        'few', 'further', 'here', 'into', 'more', 'most', 'other', 'out',
        'over', 'own', 'same', 'so', 'some', 'such', 'through', 'under',
        'until', 'up', 'while', 'during', 'et', 'al', 'fig', 'figure',
        'table', 'however', 'thus', 'therefore', 'although', 'since',
        'using', 'based', 'two', 'one', 'three', 'four', 'five',
        'new', 'first', 'well', 'also', 'us', 'use', 'used', 'many',
        'much', 'even', 'still', 'including', 'given', 'show', 'shows',
        'shown', 'see', 'e', 'g', 'eg', 'ie', 'etc', 'vs',
    ])

    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config

    def analyze_document(self, text: str) -> Dict[str, Any]:
        """
        Analyze a document and return statistics, summary, keywords,
        and suggested questions.

        Args:
            text: The full document text.

        Returns:
            Dict with keys: 'stats', 'summary', 'keywords', 'suggested_questions'.
        """
        if not text or not text.strip():
            return {
                'stats': {'words': 0, 'reading_time': '0 min'},
                'summary': '',
                'keywords': [],
                'suggested_questions': [],
            }

        stats = self._compute_stats(text)
        summary = self._extract_summary(text)
        keywords = self._extract_keywords(text)
        questions = self._generate_suggested_questions(text, keywords)

        return {
            'stats': stats,
            'summary': summary,
            'keywords': keywords,
            'suggested_questions': questions,
        }

    def _compute_stats(self, text: str) -> Dict[str, Any]:
        """Compute word count, reading time, etc."""
        words = text.split()
        word_count = len(words)
        # Average reading speed: ~250 words per minute
        reading_minutes = max(1, math.ceil(word_count / 250))
        reading_time = f"{reading_minutes} min"

        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        paragraphs = text.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])

        return {
            'words': word_count,
            'reading_time': reading_time,
            'sentences': sentence_count,
            'paragraphs': paragraph_count,
            'characters': len(text),
        }

    def _extract_summary(self, text: str, max_sentences: int = 5) -> str:
        """
        Extract a simple extractive summary by picking the most
        representative sentences from the beginning/abstract.
        """
        # Try to find an abstract section
        abstract_match = re.search(
            r'(?:abstract|summary)\s*[:\n]\s*(.*?)(?:\n\s*(?:introduction|keywords|1\.|1\s))',
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            # Clean and return up to max_sentences
            sentences = re.split(r'(?<=[.!?])\s+', abstract_text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            return ' '.join(sentences[:max_sentences])

        # Fallback: take the first meaningful sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
        return ' '.join(meaningful[:max_sentences])

    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract top keywords using simple term frequency."""
        # Tokenize: lowercase, alphabetic words of length >= 3
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter stopwords
        filtered = [w for w in words if w not in self.STOPWORDS]
        # Count frequencies
        counter = Counter(filtered)

        # Also look for bigrams (two-word phrases)
        bigrams = []
        for i in range(len(filtered) - 1):
            bigram = f"{filtered[i]} {filtered[i+1]}"
            bigrams.append(bigram)
        bigram_counter = Counter(bigrams)

        # Combine: take top unigrams and top bigrams
        top_unigrams = [word for word, _ in counter.most_common(top_n)]
        top_bigrams = [
            bg for bg, count in bigram_counter.most_common(10)
            if count >= 3
        ]

        # Merge, preferring bigrams
        keywords = []
        seen = set()
        for bg in top_bigrams[:8]:
            keywords.append(bg)
            for w in bg.split():
                seen.add(w)
        for ug in top_unigrams:
            if ug not in seen and len(keywords) < top_n:
                keywords.append(ug)
                seen.add(ug)

        return keywords[:top_n]

    def _generate_suggested_questions(
        self, text: str, keywords: List[str]
    ) -> List[str]:
        """Generate suggested questions based on document content."""
        questions = []

        # Check for common academic sections and generate relevant questions
        text_lower = text.lower()

        if re.search(r'\b(?:method|methodology|approach)\b', text_lower):
            questions.append("What methodology or approach does this paper use?")

        if re.search(r'\b(?:result|finding|experiment)\b', text_lower):
            questions.append("What are the main results and findings?")

        if re.search(r'\b(?:conclusion|future work|limitation)\b', text_lower):
            questions.append("What are the conclusions and limitations?")

        if re.search(r'\b(?:contribut|novel|propos)\b', text_lower):
            questions.append("What are the key contributions of this work?")

        if re.search(r'\b(?:compar|baseline|benchmark|state.of.the.art)\b', text_lower):
            questions.append("How does this approach compare to existing methods?")

        # Add keyword-based question
        if keywords:
            top_keyword = keywords[0]
            questions.append(f"Can you explain the role of '{top_keyword}' in this paper?")

        # Always include a general question
        if not questions:
            questions.append("What is this paper about?")
            questions.append("What problem does this paper address?")

        return questions[:5]
