"""
Tests for the conversation module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.conversation import ConversationManager, ConversationError


class TestConversationManager:
    """Test cases for the ConversationManager class."""

    @pytest.fixture
    def manager(self):
        """Create a ConversationManager instance for testing."""
        return ConversationManager()

    @pytest.fixture
    def mock_vectorstore(self):
        """Create a mock vector store."""
        mock = Mock()
        mock.as_retriever.return_value = Mock()
        return mock

    def test_initialization(self, manager):
        """Test that manager initializes correctly."""
        assert manager.chain is None
        assert manager.is_initialized is False
        assert manager.chat_history == []

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_create_chain_success(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test successful chain creation."""
        mock_chain_instance = Mock()
        mock_chain_class.from_llm.return_value = mock_chain_instance

        result = manager.create_chain(mock_vectorstore)

        mock_llm.assert_called_once()
        mock_memory.assert_called_once()
        mock_chain_class.from_llm.assert_called_once()
        assert result == mock_chain_instance
        assert manager.is_initialized is True

    @patch('src.conversation.ChatOpenAI')
    def test_create_chain_error(self, mock_llm, manager, mock_vectorstore):
        """Test error handling during chain creation."""
        mock_llm.side_effect = Exception("LLM initialization failed")

        with pytest.raises(ConversationError):
            manager.create_chain(mock_vectorstore)

    def test_ask_not_initialized(self, manager):
        """Test ask raises error when not initialized."""
        with pytest.raises(ConversationError, match="not initialized"):
            manager.ask("What is the answer?")

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_ask_success(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test successful question answering."""
        # Setup mock chain
        mock_message = Mock()
        mock_message.content = "This is a detailed answer to the question."

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'What is ML?',
            'chat_history': [Mock(content="What is ML?"), mock_message],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        result = manager.ask("What is ML?")

        assert 'answer' in result
        assert 'chat_history' in result
        assert 'is_relevant' in result
        assert result['is_relevant'] is True

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_ask_irrelevant_response(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test detection of irrelevant (short) responses."""
        mock_message = Mock()
        mock_message.content = "No."  # Very short response

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'Complex question?',
            'chat_history': [Mock(content="Complex question?"), mock_message],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        result = manager.ask("Complex question?")

        assert result['is_relevant'] is False

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_ask_without_validation(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test asking without response validation."""
        mock_message = Mock()
        mock_message.content = "No."

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'Q?',
            'chat_history': [Mock(content="Q?"), mock_message],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        result = manager.ask("Q?", validate_response=False)

        assert result['is_relevant'] is True  # Validation disabled

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_chat_history_tracking(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test that chat history is tracked."""
        mock_message = Mock()
        mock_message.content = "This is a comprehensive answer."

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'Test question',
            'chat_history': [Mock(content="Test question"), mock_message],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        manager.ask("Test question")

        history = manager.chat_history
        assert len(history) == 1
        assert history[0]['question'] == "Test question"

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_get_formatted_history(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test formatted history generation."""
        mock_message = Mock()
        mock_message.content = "This is the answer to your question."

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'Question 1',
            'chat_history': [Mock(content="Question 1"), mock_message],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        manager.ask("Question 1")

        formatted = manager.get_formatted_history()
        assert len(formatted) == 2
        assert formatted[0]['role'] == 'user'
        assert formatted[1]['role'] == 'assistant'

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_clear_history(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test clearing conversation history."""
        mock_memory_instance = Mock()
        mock_memory.return_value = mock_memory_instance

        mock_chain = Mock()
        mock_chain.return_value = {
            'question': 'Test',
            'chat_history': [Mock(content="Test"), Mock(content="Answer here!")],
        }
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        manager.ask("Test")

        assert len(manager.chat_history) > 0

        manager.clear_history()

        assert manager.chat_history == []
        mock_memory_instance.clear.assert_called_once()

    @patch('src.conversation.ChatOpenAI')
    @patch('src.conversation.ConversationBufferMemory')
    @patch('src.conversation.ConversationalRetrievalChain')
    def test_reset(
        self, mock_chain_class, mock_memory, mock_llm, manager, mock_vectorstore
    ):
        """Test full reset of conversation manager."""
        mock_chain = Mock()
        mock_chain_class.from_llm.return_value = mock_chain

        manager.create_chain(mock_vectorstore)
        assert manager.is_initialized is True

        manager.reset()

        assert manager.is_initialized is False
        assert manager.chain is None
        assert manager.chat_history == []

    def test_chat_history_returns_copy(self, manager):
        """Test that chat_history returns a copy."""
        manager._chat_history = [{'question': 'Q', 'answer': 'A', 'is_relevant': True}]

        history = manager.chat_history
        history.append({'question': 'Q2', 'answer': 'A2', 'is_relevant': True})

        assert len(manager._chat_history) == 1
