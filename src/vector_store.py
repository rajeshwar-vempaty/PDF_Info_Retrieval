"""
Vector Store module for managing document embeddings.

This module handles the creation and management of vector stores
using FAISS for efficient similarity search operations.
"""

import logging
from typing import List, Optional, Literal

from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS

from src.config import Config, default_config

# Configure module logger
logger = logging.getLogger(__name__)

# Type alias for embedding model types
EmbeddingType = Literal["openai", "huggingface"]


class VectorStoreError(Exception):
    """Exception raised when vector store operations fail."""
    pass


class VectorStoreManager:
    """
    Manages vector store creation and operations.

    This class provides methods to create vector stores from text chunks
    using either OpenAI or HuggingFace embedding models.

    Example:
        >>> manager = VectorStoreManager()
        >>> vectorstore = manager.create_vectorstore(text_chunks)
        >>> results = vectorstore.similarity_search(query)
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the vector store manager.

        Args:
            config: Configuration object. Uses default if not provided.
        """
        self.config = config or default_config
        self._vectorstore = None
        self._embedding_model = None

    @property
    def vectorstore(self):
        """Get the current vector store instance."""
        return self._vectorstore

    @property
    def is_initialized(self) -> bool:
        """Check if vector store has been initialized."""
        return self._vectorstore is not None

    def _create_embeddings(
        self,
        model_type: Optional[EmbeddingType] = None,
        model_name: Optional[str] = None
    ):
        """
        Create embedding model based on configuration.

        Args:
            model_type: Type of embedding model ('openai' or 'huggingface').
            model_name: Specific model name for HuggingFace models.

        Returns:
            Embedding model instance.

        Raises:
            VectorStoreError: If embedding model creation fails.
        """
        model_type = model_type or self.config.embedding_model_type
        model_name = model_name or self.config.huggingface_model_name

        try:
            if model_type == "huggingface" and model_name:
                logger.info(f"Using HuggingFace model: {model_name}")
                return HuggingFaceInstructEmbeddings(model_name=model_name)
            else:
                logger.info("Using OpenAI embeddings")
                return OpenAIEmbeddings()
        except Exception as e:
            error_msg = f"Failed to create embedding model: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e

    def create_vectorstore(
        self,
        text_chunks: List[str],
        model_type: Optional[EmbeddingType] = None,
        model_name: Optional[str] = None
    ) -> FAISS:
        """
        Create a FAISS vector store from text chunks.

        Args:
            text_chunks: List of text segments to embed.
            model_type: Type of embedding model to use.
            model_name: Specific model name for HuggingFace models.

        Returns:
            FAISS: Initialized FAISS vector store.

        Raises:
            VectorStoreError: If vector store creation fails.
            ValueError: If text_chunks is empty.
        """
        if not text_chunks:
            raise ValueError("Cannot create vector store from empty text chunks")

        try:
            self._embedding_model = self._create_embeddings(model_type, model_name)
            self._vectorstore = FAISS.from_texts(
                texts=text_chunks,
                embedding=self._embedding_model
            )
            logger.info(
                f"Vector store created successfully with {len(text_chunks)} chunks"
            )
            return self._vectorstore

        except Exception as e:
            error_msg = f"Failed to create vector store: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e

    def add_texts(self, text_chunks: List[str]) -> List[str]:
        """
        Add additional text chunks to existing vector store.

        Args:
            text_chunks: List of text segments to add.

        Returns:
            List[str]: IDs of added documents.

        Raises:
            VectorStoreError: If vector store is not initialized.
        """
        if not self.is_initialized:
            raise VectorStoreError(
                "Vector store not initialized. Call create_vectorstore first."
            )

        try:
            ids = self._vectorstore.add_texts(text_chunks)
            logger.info(f"Added {len(text_chunks)} chunks to vector store")
            return ids
        except Exception as e:
            error_msg = f"Failed to add texts to vector store: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e

    def similarity_search(
        self,
        query: str,
        k: int = 4
    ) -> List:
        """
        Perform similarity search on the vector store.

        Args:
            query: Search query string.
            k: Number of results to return.

        Returns:
            List: List of similar documents.

        Raises:
            VectorStoreError: If search fails or vector store not initialized.
        """
        if not self.is_initialized:
            raise VectorStoreError(
                "Vector store not initialized. Call create_vectorstore first."
            )

        try:
            results = self._vectorstore.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} similar documents for query")
            return results
        except Exception as e:
            error_msg = f"Similarity search failed: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e

    def as_retriever(self, **kwargs):
        """
        Get retriever interface for the vector store.

        Args:
            **kwargs: Additional arguments passed to as_retriever.

        Returns:
            Retriever interface for the vector store.

        Raises:
            VectorStoreError: If vector store not initialized.
        """
        if not self.is_initialized:
            raise VectorStoreError(
                "Vector store not initialized. Call create_vectorstore first."
            )

        return self._vectorstore.as_retriever(**kwargs)

    def save_local(self, path: str):
        """
        Save vector store to local directory.

        Args:
            path: Directory path to save the vector store.

        Raises:
            VectorStoreError: If save operation fails.
        """
        if not self.is_initialized:
            raise VectorStoreError(
                "Vector store not initialized. Nothing to save."
            )

        try:
            self._vectorstore.save_local(path)
            logger.info(f"Vector store saved to {path}")
        except Exception as e:
            error_msg = f"Failed to save vector store: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e

    def load_local(self, path: str, embeddings=None):
        """
        Load vector store from local directory.

        Args:
            path: Directory path to load from.
            embeddings: Embedding model to use. Creates new one if not provided.

        Raises:
            VectorStoreError: If load operation fails.
        """
        try:
            if embeddings is None:
                embeddings = self._create_embeddings()

            self._vectorstore = FAISS.load_local(path, embeddings)
            self._embedding_model = embeddings
            logger.info(f"Vector store loaded from {path}")
        except Exception as e:
            error_msg = f"Failed to load vector store: {str(e)}"
            logger.error(error_msg)
            raise VectorStoreError(error_msg) from e
