"""
PDF Processing module for extracting text from PDF documents.

This module handles the extraction of raw text from PDF files
using pdfplumber for reliable text extraction.
"""

import logging
from typing import List, Optional, BinaryIO, Union
from pathlib import Path

import pdfplumber

# Configure module logger
logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Exception raised when PDF processing fails."""
    pass


class PDFProcessor:
    """
    Handles PDF document processing and text extraction.

    This class provides methods to extract text from single or multiple
    PDF documents, with proper error handling and logging.

    Example:
        >>> processor = PDFProcessor()
        >>> text = processor.extract_text_from_files([pdf_file1, pdf_file2])
    """

    def __init__(self):
        """Initialize the PDF processor."""
        self._processed_count = 0
        self._failed_files: List[str] = []

    @property
    def processed_count(self) -> int:
        """Get the count of successfully processed PDFs."""
        return self._processed_count

    @property
    def failed_files(self) -> List[str]:
        """Get list of files that failed to process."""
        return self._failed_files.copy()

    def reset_stats(self):
        """Reset processing statistics."""
        self._processed_count = 0
        self._failed_files = []

    def extract_text_from_file(self, pdf_file: Union[BinaryIO, str, Path]) -> str:
        """
        Extract text from a single PDF file.

        Args:
            pdf_file: File object, path string, or Path object pointing to PDF.

        Returns:
            str: Extracted text content from the PDF.

        Raises:
            PDFProcessingError: If text extraction fails.
        """
        text = ""
        file_name = self._get_file_name(pdf_file)

        try:
            with pdfplumber.open(pdf_file) as pdf_reader:
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        logger.warning(
                            f"No text extracted from page {page_num} of {file_name}"
                        )

            if not text.strip():
                logger.warning(f"No text content extracted from {file_name}")

            self._processed_count += 1
            logger.info(f"Successfully processed: {file_name}")
            return text

        except Exception as e:
            error_msg = f"Failed to process PDF {file_name}: {str(e)}"
            logger.error(error_msg)
            self._failed_files.append(file_name)
            raise PDFProcessingError(error_msg) from e

    def extract_text_from_files(
        self,
        pdf_files: List[Union[BinaryIO, str, Path]],
        continue_on_error: bool = True
    ) -> str:
        """
        Extract text from multiple PDF files.

        Args:
            pdf_files: List of file objects or paths to PDF files.
            continue_on_error: If True, continue processing remaining files
                             when one fails. Default is True.

        Returns:
            str: Combined text content from all successfully processed PDFs.

        Raises:
            PDFProcessingError: If processing fails and continue_on_error is False.
        """
        self.reset_stats()
        combined_text = ""

        for pdf_file in pdf_files:
            try:
                text = self.extract_text_from_file(pdf_file)
                combined_text += text + "\n\n"
            except PDFProcessingError as e:
                if not continue_on_error:
                    raise
                logger.warning(f"Skipping file due to error: {e}")

        if not combined_text.strip():
            logger.warning("No text extracted from any PDF files")

        return combined_text

    def get_processing_summary(self) -> dict:
        """
        Get a summary of the processing results.

        Returns:
            dict: Summary containing processed count, failed files, and status.
        """
        return {
            "processed_count": self._processed_count,
            "failed_count": len(self._failed_files),
            "failed_files": self._failed_files.copy(),
            "success": len(self._failed_files) == 0,
        }

    @staticmethod
    def _get_file_name(pdf_file: Union[BinaryIO, str, Path]) -> str:
        """Extract file name from various input types."""
        if isinstance(pdf_file, (str, Path)):
            return Path(pdf_file).name
        elif hasattr(pdf_file, 'name'):
            return pdf_file.name
        return "unknown"
