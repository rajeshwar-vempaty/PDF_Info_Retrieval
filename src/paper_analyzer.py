"""
Paper Analyzer module for extracting structured elements from research papers.

This module identifies figures, tables, and technical terms referenced in
the text of research papers.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from collections import Counter

from src.config import Config, default_config

logger = logging.getLogger(__name__)


@dataclass
class FigureReference:
    """A reference to a figure or table found in the paper text."""
    type: str        # 'figure' or 'table'
    title: str       # e.g. "Figure 1" or "Table 3"
    caption: str     # Caption text (if found)
    page: int        # Estimated page number


@dataclass
class TechnicalTerm:
    """A technical term extracted from the paper."""
    term: str        # The term itself
    frequency: int   # How many times it appears
    context: str     # A sentence where the term appears


class PaperAnalyzer:
    """
    Analyzes research paper text to extract structured elements:
    - Figure and table references
    - Technical terms with context

    Usage in app_enhanced.py:
        analyzer = PaperAnalyzer(config)
        paper = analyzer.analyze_paper(text)
        # paper keys: 'figures', 'terms'
    """

    # Common non-technical words to exclude from term detection
    COMMON_WORDS = frozenset([
        'abstract', 'introduction', 'methods', 'methodology', 'results',
        'discussion', 'conclusion', 'references', 'acknowledgments',
        'figure', 'table', 'section', 'chapter', 'paper', 'study',
        'approach', 'analysis', 'data', 'based', 'using', 'used',
        'proposed', 'results', 'show', 'shown', 'however', 'therefore',
        'although', 'moreover', 'furthermore', 'respectively', 'corresponding',
        'following', 'previous', 'different', 'similar', 'various',
        'several', 'many', 'including', 'according', 'compared',
        'example', 'given', 'consider', 'note', 'also', 'well',
    ])

    def __init__(self, config: Optional[Config] = None):
        self.config = config or default_config

    def analyze_paper(self, text: str) -> Dict[str, Any]:
        """
        Analyze a research paper and extract figures, tables, and
        technical terms.

        Args:
            text: The full paper text.

        Returns:
            Dict with keys: 'figures' (list of FigureReference),
                            'terms' (list of TechnicalTerm).
        """
        if not text or not text.strip():
            return {'figures': [], 'terms': []}

        figures = self._extract_figure_references(text)
        terms = self._extract_technical_terms(text)

        return {
            'figures': figures,
            'terms': terms,
        }

    def _extract_figure_references(self, text: str) -> List[FigureReference]:
        """Extract figure and table references from text."""
        refs = []
        seen_titles = set()

        # Match "Figure X" / "Fig. X" / "Table X" patterns with optional captions
        patterns = [
            (r'(Figure|Fig\.?)\s+(\d+)[.:]?\s*([^\n]{0,200})', 'figure'),
            (r'(Table)\s+(\d+)[.:]?\s*([^\n]{0,200})', 'table'),
        ]

        chars_per_page = max(1, len(text) // max(1, len(text) // 3000))

        for pattern, ref_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                title = f"{match.group(1)} {match.group(2)}"
                # Normalize title for dedup
                title_key = title.lower().replace('.', '').strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                caption = match.group(3).strip() if match.group(3) else ""
                # Clean up caption
                caption = re.sub(r'\s+', ' ', caption)
                if len(caption) > 200:
                    caption = caption[:200].rsplit(' ', 1)[0] + "..."

                page = max(1, match.start() // 3000 + 1)

                refs.append(FigureReference(
                    type=ref_type,
                    title=title,
                    caption=caption,
                    page=page,
                ))

        # Sort by page
        refs.sort(key=lambda r: r.page)
        return refs

    def _extract_technical_terms(self, text: str, top_n: int = 30) -> List[TechnicalTerm]:
        """
        Extract technical terms from paper text.

        Looks for:
        - Capitalized multi-word phrases (e.g. "Convolutional Neural Network")
        - Acronyms (e.g. "CNN", "LSTM")
        - Domain-specific patterns
        """
        terms_with_context: Dict[str, Dict] = {}

        # Split text into sentences for context extraction
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # 1. Find acronyms (2-6 uppercase letters)
        acronym_pattern = re.compile(r'\b([A-Z]{2,6})\b')
        for sentence in sentences:
            for match in acronym_pattern.finditer(sentence):
                acronym = match.group(1)
                # Skip very common ones that aren't technical
                if acronym in ('THE', 'AND', 'FOR', 'NOT', 'BUT', 'ARE', 'WAS',
                               'HAS', 'HAD', 'CAN', 'MAY', 'ALL', 'ANY', 'ITS'):
                    continue
                key = acronym.upper()
                if key not in terms_with_context:
                    terms_with_context[key] = {
                        'term': acronym,
                        'count': 0,
                        'context': sentence.strip()[:300],
                    }
                terms_with_context[key]['count'] += 1

        # 2. Find capitalized multi-word phrases (potential proper nouns / techniques)
        phrase_pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b')
        for sentence in sentences:
            for match in phrase_pattern.finditer(sentence):
                phrase = match.group(1)
                words = phrase.lower().split()
                # Skip if all words are common
                if all(w in self.COMMON_WORDS for w in words):
                    continue
                # Skip very short or long phrases
                if len(phrase) < 5 or len(phrase) > 60:
                    continue
                key = phrase.lower()
                if key not in terms_with_context:
                    terms_with_context[key] = {
                        'term': phrase,
                        'count': 0,
                        'context': sentence.strip()[:300],
                    }
                terms_with_context[key]['count'] += 1

        # 3. Find hyphenated technical terms (e.g. "self-attention", "pre-training")
        hyphen_pattern = re.compile(r'\b([a-z]+-[a-z]+(?:-[a-z]+)*)\b')
        for sentence in sentences:
            for match in hyphen_pattern.finditer(sentence):
                term = match.group(1)
                if len(term) < 5:
                    continue
                key = term.lower()
                if key not in terms_with_context:
                    terms_with_context[key] = {
                        'term': term,
                        'count': 0,
                        'context': sentence.strip()[:300],
                    }
                terms_with_context[key]['count'] += 1

        # Filter: require at least 2 occurrences
        filtered = {
            k: v for k, v in terms_with_context.items()
            if v['count'] >= 2
        }

        # Sort by frequency, descending
        sorted_terms = sorted(
            filtered.values(),
            key=lambda x: x['count'],
            reverse=True,
        )

        # Convert to TechnicalTerm objects
        result = []
        for item in sorted_terms[:top_n]:
            result.append(TechnicalTerm(
                term=item['term'],
                frequency=item['count'],
                context=item['context'],
            ))

        return result
