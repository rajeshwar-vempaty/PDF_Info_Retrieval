"""
Tests for the PDF processing module.
"""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from src.pdf_processor import PDFProcessor, PDFProcessingError


class TestPDFProcessor:
    """Test cases for the PDFProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a PDFProcessor instance for testing."""
        return PDFProcessor()

    def test_initialization(self, processor):
        """Test that processor initializes correctly."""
        assert processor.processed_count == 0
        assert processor.failed_files == []

    def test_reset_stats(self, processor):
        """Test resetting processing statistics."""
        processor._processed_count = 5
        processor._failed_files = ["file1.pdf", "file2.pdf"]

        processor.reset_stats()

        assert processor.processed_count == 0
        assert processor.failed_files == []

    def test_get_processing_summary(self, processor):
        """Test processing summary generation."""
        processor._processed_count = 3
        processor._failed_files = ["failed.pdf"]

        summary = processor.get_processing_summary()

        assert summary["processed_count"] == 3
        assert summary["failed_count"] == 1
        assert "failed.pdf" in summary["failed_files"]
        assert summary["success"] is False

    def test_get_processing_summary_success(self, processor):
        """Test processing summary when all files succeed."""
        processor._processed_count = 3
        processor._failed_files = []

        summary = processor.get_processing_summary()

        assert summary["success"] is True

    @patch('src.pdf_processor.pdfplumber')
    def test_extract_text_from_file_success(self, mock_pdfplumber, processor):
        """Test successful text extraction from a PDF."""
        # Setup mock
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content from page"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        # Create mock file
        mock_file = Mock()
        mock_file.name = "test.pdf"

        # Execute
        result = processor.extract_text_from_file(mock_file)

        # Verify
        assert "Test content from page" in result
        assert processor.processed_count == 1

    @patch('src.pdf_processor.pdfplumber')
    def test_extract_text_from_file_error(self, mock_pdfplumber, processor):
        """Test error handling during text extraction."""
        mock_pdfplumber.open.side_effect = Exception("PDF read error")

        mock_file = Mock()
        mock_file.name = "corrupt.pdf"

        with pytest.raises(PDFProcessingError):
            processor.extract_text_from_file(mock_file)

        assert "corrupt.pdf" in processor.failed_files

    @patch('src.pdf_processor.pdfplumber')
    def test_extract_text_from_files_multiple(self, mock_pdfplumber, processor):
        """Test extracting text from multiple PDFs."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Content"

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdfplumber.open.return_value = mock_pdf

        mock_files = [Mock(name=f"file{i}.pdf") for i in range(3)]
        for f in mock_files:
            f.name = f"file.pdf"

        result = processor.extract_text_from_files(mock_files)

        assert "Content" in result
        assert processor.processed_count == 3

    @patch('src.pdf_processor.pdfplumber')
    def test_extract_text_continue_on_error(self, mock_pdfplumber, processor):
        """Test that processing continues when a file fails."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Error on second file")

            mock_page = Mock()
            mock_page.extract_text.return_value = "Content"

            mock_pdf = Mock()
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = Mock(return_value=mock_pdf)
            mock_pdf.__exit__ = Mock(return_value=False)
            return mock_pdf

        mock_pdfplumber.open.side_effect = side_effect

        mock_files = [Mock(name=f"file{i}.pdf") for i in range(3)]
        for i, f in enumerate(mock_files):
            f.name = f"file{i}.pdf"

        result = processor.extract_text_from_files(mock_files, continue_on_error=True)

        assert "Content" in result
        assert processor.processed_count == 2
        assert len(processor.failed_files) == 1

    def test_get_file_name_string_path(self, processor):
        """Test file name extraction from string path."""
        name = processor._get_file_name("/path/to/document.pdf")
        assert name == "document.pdf"

    def test_get_file_name_file_object(self, processor):
        """Test file name extraction from file object."""
        mock_file = Mock()
        mock_file.name = "uploaded.pdf"

        name = processor._get_file_name(mock_file)
        assert name == "uploaded.pdf"

    def test_get_file_name_unknown(self, processor):
        """Test file name extraction from unknown type."""
        name = processor._get_file_name(123)
        assert name == "unknown"

    def test_failed_files_returns_copy(self, processor):
        """Test that failed_files property returns a copy."""
        processor._failed_files = ["file.pdf"]

        failed = processor.failed_files
        failed.append("other.pdf")

        assert "other.pdf" not in processor._failed_files
