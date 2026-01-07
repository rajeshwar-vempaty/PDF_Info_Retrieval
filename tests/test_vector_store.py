"""
Tests for the vector store module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.vector_store import VectorStoreManager, VectorStoreError


class TestVectorStoreManager:
    """Test cases for the VectorStoreManager class."""

    @pytest.fixture
    def manager(self):
        """Create a VectorStoreManager instance for testing."""
        return VectorStoreManager()

    @pytest.fixture
    def sample_chunks(self):
        """Sample text chunks for testing."""
        return [
            "This is the first chunk of text about machine learning.",
            "The second chunk discusses natural language processing.",
            "A third chunk covers deep learning architectures.",
        ]

    def test_initialization(self, manager):
        """Test that manager initializes correctly."""
        assert manager.vectorstore is None
        assert manager.is_initialized is False

    def test_is_initialized_false(self, manager):
        """Test is_initialized returns False when not set up."""
        assert manager.is_initialized is False

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_create_vectorstore_openai(
        self, mock_faiss, mock_embeddings, manager, sample_chunks
    ):
        """Test creating vector store with OpenAI embeddings."""
        mock_embedding_instance = Mock()
        mock_embeddings.return_value = mock_embedding_instance

        mock_vectorstore = Mock()
        mock_faiss.from_texts.return_value = mock_vectorstore

        result = manager.create_vectorstore(sample_chunks, model_type="openai")

        mock_embeddings.assert_called_once()
        mock_faiss.from_texts.assert_called_once_with(
            texts=sample_chunks,
            embedding=mock_embedding_instance
        )
        assert result == mock_vectorstore
        assert manager.is_initialized is True

    @patch('src.vector_store.HuggingFaceInstructEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_create_vectorstore_huggingface(
        self, mock_faiss, mock_hf_embeddings, manager, sample_chunks
    ):
        """Test creating vector store with HuggingFace embeddings."""
        mock_embedding_instance = Mock()
        mock_hf_embeddings.return_value = mock_embedding_instance

        mock_vectorstore = Mock()
        mock_faiss.from_texts.return_value = mock_vectorstore

        result = manager.create_vectorstore(
            sample_chunks,
            model_type="huggingface",
            model_name="hkunlp/instructor-base"
        )

        mock_hf_embeddings.assert_called_once_with(model_name="hkunlp/instructor-base")
        assert result == mock_vectorstore

    def test_create_vectorstore_empty_chunks(self, manager):
        """Test that empty chunks raise ValueError."""
        with pytest.raises(ValueError, match="empty text chunks"):
            manager.create_vectorstore([])

    @patch('src.vector_store.OpenAIEmbeddings')
    def test_create_vectorstore_error(self, mock_embeddings, manager, sample_chunks):
        """Test error handling during vector store creation."""
        mock_embeddings.side_effect = Exception("API Error")

        with pytest.raises(VectorStoreError):
            manager.create_vectorstore(sample_chunks)

    def test_add_texts_not_initialized(self, manager):
        """Test add_texts raises error when not initialized."""
        with pytest.raises(VectorStoreError, match="not initialized"):
            manager.add_texts(["new chunk"])

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_add_texts_success(
        self, mock_faiss, mock_embeddings, manager, sample_chunks
    ):
        """Test adding texts to existing vector store."""
        mock_vectorstore = Mock()
        mock_vectorstore.add_texts.return_value = ["id1", "id2"]
        mock_faiss.from_texts.return_value = mock_vectorstore
        mock_embeddings.return_value = Mock()

        manager.create_vectorstore(sample_chunks)
        ids = manager.add_texts(["new chunk 1", "new chunk 2"])

        assert ids == ["id1", "id2"]
        mock_vectorstore.add_texts.assert_called_once()

    def test_similarity_search_not_initialized(self, manager):
        """Test similarity_search raises error when not initialized."""
        with pytest.raises(VectorStoreError, match="not initialized"):
            manager.similarity_search("test query")

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_similarity_search_success(
        self, mock_faiss, mock_embeddings, manager, sample_chunks
    ):
        """Test successful similarity search."""
        mock_results = [Mock(page_content="result 1"), Mock(page_content="result 2")]
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search.return_value = mock_results
        mock_faiss.from_texts.return_value = mock_vectorstore
        mock_embeddings.return_value = Mock()

        manager.create_vectorstore(sample_chunks)
        results = manager.similarity_search("machine learning", k=2)

        assert len(results) == 2
        mock_vectorstore.similarity_search.assert_called_once_with(
            "machine learning", k=2
        )

    def test_as_retriever_not_initialized(self, manager):
        """Test as_retriever raises error when not initialized."""
        with pytest.raises(VectorStoreError, match="not initialized"):
            manager.as_retriever()

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_as_retriever_success(
        self, mock_faiss, mock_embeddings, manager, sample_chunks
    ):
        """Test getting retriever interface."""
        mock_retriever = Mock()
        mock_vectorstore = Mock()
        mock_vectorstore.as_retriever.return_value = mock_retriever
        mock_faiss.from_texts.return_value = mock_vectorstore
        mock_embeddings.return_value = Mock()

        manager.create_vectorstore(sample_chunks)
        retriever = manager.as_retriever(search_kwargs={"k": 3})

        assert retriever == mock_retriever
        mock_vectorstore.as_retriever.assert_called_once_with(search_kwargs={"k": 3})

    def test_save_local_not_initialized(self, manager):
        """Test save_local raises error when not initialized."""
        with pytest.raises(VectorStoreError, match="not initialized"):
            manager.save_local("/tmp/vectorstore")

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_save_local_success(
        self, mock_faiss, mock_embeddings, manager, sample_chunks
    ):
        """Test saving vector store locally."""
        mock_vectorstore = Mock()
        mock_faiss.from_texts.return_value = mock_vectorstore
        mock_embeddings.return_value = Mock()

        manager.create_vectorstore(sample_chunks)
        manager.save_local("/tmp/test_store")

        mock_vectorstore.save_local.assert_called_once_with("/tmp/test_store")

    @patch('src.vector_store.OpenAIEmbeddings')
    @patch('src.vector_store.FAISS')
    def test_load_local_success(self, mock_faiss, mock_embeddings, manager):
        """Test loading vector store from disk."""
        mock_vectorstore = Mock()
        mock_faiss.load_local.return_value = mock_vectorstore
        mock_embeddings.return_value = Mock()

        manager.load_local("/tmp/test_store")

        assert manager.is_initialized is True
        mock_faiss.load_local.assert_called_once()
