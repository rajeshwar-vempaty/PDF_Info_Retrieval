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
        # Additional stopwords for research papers
        'paper', 'section', 'method', 'approach', 'propose', 'proposed',
        'present', 'presented', 'work', 'study', 'result', 'results',
        'number', 'set', 'order', 'case', 'high', 'low', 'large', 'small',
        'different', 'similar', 'previous', 'following', 'respectively',
        'corresponding', 'according', 'compared', 'example', 'consider',
        'note', 'able', 'get', 'got', 'take', 'taken', 'make', 'made',
        'provide', 'provides', 'provide', 'total', 'only', 'without',
        'within', 'among', 'across', 'per', 'via', 'like', 'specific',
        'particular', 'general', 'overall', 'left', 'right', 'end',
        'part', 'each', 'every', 'either', 'neither', 'rather',
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

    def _fix_reversed_text(self, text: str) -> str:
        """Detect and fix reversed text from PDF extraction."""
        common_words = frozenset([
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'was', 'one', 'our', 'has', 'his', 'how', 'its', 'may',
            'new', 'now', 'see', 'way', 'who', 'did', 'get', 'say', 'she',
            'use', 'with', 'this', 'that', 'have', 'from', 'they', 'been',
            'each', 'which', 'their', 'will', 'other', 'about', 'many',
            'then', 'them', 'these', 'some', 'would', 'make', 'like',
            'model', 'data', 'input', 'output', 'method', 'paper',
        ])
        words = text.split()
        if len(words) < 10:
            return text
        sample = words[:min(80, len(words))]
        normal_hits = sum(1 for w in sample if w.lower() in common_words)
        reversed_hits = sum(1 for w in sample if w[::-1].lower() in common_words)
        if reversed_hits > normal_hits * 2 and reversed_hits > 3:
            return ' '.join(w[::-1] for w in words)
        return text

    def _extract_summary(self, text: str, max_sentences: int = 5) -> str:
        """
        Extract a simple extractive summary by picking the most
        representative sentences from the beginning/abstract.
        """
        # Fix reversed text if needed
        text = self._fix_reversed_text(text)

        # Try to find an abstract section (multiple patterns)
        abstract_patterns = [
            r'(?:abstract|summary)\s*[:\n]\s*(.*?)(?:\n\s*(?:introduction|keywords|1\.|1\s|I\.))',
            r'(?:abstract|summary)\s*\n+(.*?)(?:\n\s*\n)',
            r'(?:^|\n)\s*abstract\s*\n(.*?)(?:\n\s*\n)',
        ]

        for pattern in abstract_patterns:
            abstract_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if abstract_match:
                abstract_text = abstract_match.group(1).strip()
                if len(abstract_text) > 50:
                    # Clean and return up to max_sentences
                    sentences = re.split(r'(?<=[.!?])\s+', abstract_text)
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                    if sentences:
                        return ' '.join(sentences[:max_sentences])

        # Fallback: take the first meaningful sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        meaningful = [s.strip() for s in sentences if len(s.strip()) > 30]
        return ' '.join(meaningful[:max_sentences])

    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract top keywords using simple term frequency."""
        # Fix reversed text if needed
        text = self._fix_reversed_text(text)

        # Tokenize: lowercase, alphabetic words of length >= 3
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter stopwords and very short/long words
        filtered = [w for w in words
                    if w not in self.STOPWORDS and 3 <= len(w) <= 25]
        # Count frequencies
        counter = Counter(filtered)

        # Also look for bigrams (two-word phrases)
        bigrams = []
        for i in range(len(filtered) - 1):
            # Skip bigrams where both words are the same (duplicate noise)
            if filtered[i] != filtered[i + 1]:
                bigram = f"{filtered[i]} {filtered[i+1]}"
                bigrams.append(bigram)
        bigram_counter = Counter(bigrams)

        # Combine: take top unigrams and top bigrams
        top_unigrams = [word for word, count in counter.most_common(top_n * 2)
                        if count >= 2]  # Require at least 2 occurrences
        top_bigrams = [
            bg for bg, count in bigram_counter.most_common(15)
            if count >= 3
        ]

        # Merge, preferring bigrams, avoiding duplicates
        keywords = []
        seen_words = set()
        for bg in top_bigrams[:8]:
            bg_words = bg.split()
            # Skip if bigram contains duplicate words
            if len(set(bg_words)) < len(bg_words):
                continue
            keywords.append(bg)
            for w in bg_words:
                seen_words.add(w)
        for ug in top_unigrams:
            if ug not in seen_words and len(keywords) < top_n:
                # Skip words that look like reversed gibberish
                # (no vowels or very unlikely character sequences)
                vowels = set('aeiou')
                if not vowels.intersection(ug):
                    continue
                keywords.append(ug)
                seen_words.add(ug)

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
