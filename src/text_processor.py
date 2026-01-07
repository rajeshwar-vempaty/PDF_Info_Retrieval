"""
Text Processing module for cleaning and chunking extracted text.

This module provides functionality for cleaning raw text extracted from
PDFs and splitting it into optimal chunks for embedding and retrieval.
"""

import re
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.config import Config, default_config

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """
    Represents a chunk of processed text with metadata.

    Attributes:
        content: The text content of the chunk.
        start_offset: Starting position in original text.
        end_offset: Ending position in original text.
        section: The academic section this chunk belongs to (if applicable).
    """
    content: str
    start_offset: int = 0
    end_offset: int = 0
    section: Optional[str] = None


class TextProcessor:
    """
    Handles text cleaning and chunking operations.

    This class provides methods for cleaning extracted PDF text and
    splitting it into manageable chunks suitable for embedding.

    Example:
        >>> processor = TextProcessor()
        >>> cleaned = processor.clean_text(raw_text)
        >>> chunks = processor.create_chunks(cleaned)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the text processor.

        Args:
            config: Configuration object. Uses default if not provided.
        """
        self.config = config or default_config
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._cleaning_patterns = [
            re.compile(pattern, re.MULTILINE)
            for pattern in self.config.cleaning_patterns
        ]
        self._header_pattern = re.compile(
            self.config.header_pattern,
            re.IGNORECASE
        )
        self._section_pattern = re.compile(
            self.config.section_pattern,
            re.IGNORECASE
        )

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing noise and normalizing formatting.

        Performs the following operations:
        - Converts text to lowercase
        - Removes email addresses, brackets, figure/table captions
        - Removes non-ASCII characters
        - Normalizes whitespace

        Args:
            text: Raw text to clean.

        Returns:
            str: Cleaned and normalized text.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Apply all cleaning patterns
        for pattern in self._cleaning_patterns:
            text = pattern.sub('', text)

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        logger.debug(f"Cleaned text length: {len(text)} characters")
        return text

    def create_chunks(
        self,
        text: str,
        return_metadata: bool = False
    ) -> List[str]:
        """
        Split text into chunks based on academic sections and size limits.

        Uses intelligent chunking that:
        - Respects academic section boundaries (Abstract, Introduction, etc.)
        - Limits chunks to configured maximum size
        - Preserves context within chunks

        Args:
            text: Text to split into chunks.
            return_metadata: If True, returns TextChunk objects with metadata.

        Returns:
            List[str]: List of text chunks, or List[TextChunk] if return_metadata=True.
        """
        if not text:
            return []

        sections = self._header_pattern.split(text)
        chunks: List[TextChunk] = []
        current_chunk_words: List[str] = []
        current_length = 0
        current_offset = 0
        current_section: Optional[str] = None

        for section in sections:
            if self._section_pattern.match(section):
                # Save current chunk if exists
                if current_chunk_words:
                    chunk_content = ' '.join(current_chunk_words).strip()
                    chunks.append(TextChunk(
                        content=chunk_content,
                        start_offset=current_offset,
                        end_offset=current_offset + len(chunk_content),
                        section=current_section
                    ))
                    current_chunk_words = []
                    current_length = 0

                # Start new section
                current_section = section.capitalize()
                current_chunk_words.append(section)
                current_offset += len(section) + 1
            else:
                words = section.split()
                for word in words:
                    word_len = len(word) + 1  # +1 for space

                    if current_length + word_len > self.config.chunk_size:
                        # Save current chunk and start new one
                        if current_chunk_words:
                            chunk_content = ' '.join(current_chunk_words).strip()
                            chunks.append(TextChunk(
                                content=chunk_content,
                                start_offset=current_offset,
                                end_offset=current_offset + len(chunk_content),
                                section=current_section
                            ))
                        current_chunk_words = [word]
                        current_length = word_len
                    else:
                        current_chunk_words.append(word)
                        current_length += word_len

        # Don't forget the last chunk
        if current_chunk_words:
            chunk_content = ' '.join(current_chunk_words).strip()
            chunks.append(TextChunk(
                content=chunk_content,
                start_offset=current_offset,
                end_offset=current_offset + len(chunk_content),
                section=current_section
            ))

        logger.info(f"Created {len(chunks)} chunks from text")

        if return_metadata:
            return chunks
        return [chunk.content for chunk in chunks]

    def process(self, text: str) -> List[str]:
        """
        Full processing pipeline: clean text and create chunks.

        Convenience method that combines cleaning and chunking
        in a single call.

        Args:
            text: Raw text to process.

        Returns:
            List[str]: List of cleaned and chunked text segments.
        """
        cleaned_text = self.clean_text(text)
        return self.create_chunks(cleaned_text)

    def get_stats(self, text: str) -> dict:
        """
        Get statistics about text before and after processing.

        Args:
            text: Text to analyze.

        Returns:
            dict: Statistics including character counts, word counts, etc.
        """
        cleaned = self.clean_text(text)
        chunks = self.create_chunks(cleaned)

        return {
            "original_length": len(text),
            "cleaned_length": len(cleaned),
            "reduction_percent": round(
                (1 - len(cleaned) / len(text)) * 100, 2
            ) if text else 0,
            "word_count": len(cleaned.split()),
            "chunk_count": len(chunks),
            "avg_chunk_size": round(
                sum(len(c) for c in chunks) / len(chunks), 2
            ) if chunks else 0,
        }
