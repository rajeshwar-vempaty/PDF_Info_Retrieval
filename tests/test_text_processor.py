"""
Tests for the text processing module.
"""

import pytest
from src.text_processor import TextProcessor, TextChunk
from src.config import Config


class TestTextProcessor:
    """Test cases for the TextProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a TextProcessor instance for testing."""
        return TextProcessor()

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return """
        Abstract
        This is the abstract section of the paper. It contains a summary of the research.

        Introduction
        This is the introduction section. Here we introduce the topic and background.

        Methods
        This section describes the methodology used in the research.

        Results
        The results section presents the findings of the study.

        Discussion
        Here we discuss the implications of our findings.

        Conclusion
        This is the conclusion of the paper.
        """

    def test_clean_text_lowercase(self, processor):
        """Test that clean_text converts to lowercase."""
        result = processor.clean_text("HELLO WORLD")
        assert result == "hello world"

    def test_clean_text_removes_emails(self, processor):
        """Test that clean_text removes email addresses."""
        text = "Contact us at test@example.com for more info"
        result = processor.clean_text(text)
        assert "@" not in result
        assert "example.com" not in result

    def test_clean_text_removes_brackets(self, processor):
        """Test that clean_text removes bracketed content."""
        text = "This is text [with brackets] and more"
        result = processor.clean_text(text)
        assert "[" not in result
        assert "]" not in result

    def test_clean_text_removes_figure_captions(self, processor):
        """Test that clean_text removes figure captions."""
        text = "Some text Figure 1: Caption here more text"
        result = processor.clean_text(text)
        assert "figure 1:" not in result.lower()

    def test_clean_text_normalizes_whitespace(self, processor):
        """Test that clean_text normalizes whitespace."""
        text = "Multiple    spaces   and\nnewlines"
        result = processor.clean_text(text)
        assert "  " not in result  # No double spaces

    def test_clean_text_empty_input(self, processor):
        """Test clean_text with empty input."""
        assert processor.clean_text("") == ""
        assert processor.clean_text(None) == ""

    def test_create_chunks_basic(self, processor, sample_text):
        """Test basic chunking functionality."""
        chunks = processor.create_chunks(sample_text)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

    def test_create_chunks_empty_input(self, processor):
        """Test create_chunks with empty input."""
        chunks = processor.create_chunks("")
        assert chunks == []

    def test_create_chunks_with_metadata(self, processor, sample_text):
        """Test chunking with metadata enabled."""
        chunks = processor.create_chunks(sample_text, return_metadata=True)

        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert all(hasattr(chunk, 'content') for chunk in chunks)

    def test_chunk_size_limit(self, processor):
        """Test that chunks respect size limits."""
        # Create text larger than chunk size
        large_text = "word " * 1000  # ~5000 characters
        chunks = processor.create_chunks(large_text)

        for chunk in chunks:
            assert len(chunk) <= processor.config.chunk_size + 100  # Allow small overflow

    def test_process_combines_clean_and_chunk(self, processor, sample_text):
        """Test that process() combines cleaning and chunking."""
        chunks = processor.process(sample_text)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        # Check that text is cleaned (lowercase)
        assert all(chunk == chunk.lower() for chunk in chunks)

    def test_get_stats(self, processor, sample_text):
        """Test statistics generation."""
        stats = processor.get_stats(sample_text)

        assert "original_length" in stats
        assert "cleaned_length" in stats
        assert "reduction_percent" in stats
        assert "word_count" in stats
        assert "chunk_count" in stats
        assert "avg_chunk_size" in stats

        assert stats["original_length"] > 0
        assert stats["chunk_count"] > 0

    def test_custom_config(self):
        """Test TextProcessor with custom configuration."""
        config = Config(chunk_size=500)
        processor = TextProcessor(config)

        assert processor.config.chunk_size == 500

    def test_academic_section_detection(self, processor):
        """Test that academic sections are detected."""
        text = """
        Abstract
        This is the abstract.

        Introduction
        This is the introduction.
        """
        chunks = processor.create_chunks(text, return_metadata=True)

        # Check that sections are identified
        sections = [chunk.section for chunk in chunks if chunk.section]
        assert len(sections) > 0
