"""
Conversation module for managing RAG-based chat interactions.

This module handles the creation and management of conversational
retrieval chains for question answering over documents.
"""

import logging
from typing import Optional, List, Dict, Any

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

from src.config import Config, default_config

# Configure module logger
logger = logging.getLogger(__name__)


class ConversationError(Exception):
    """Exception raised when conversation operations fail."""
    pass


class ConversationManager:
    """
    Manages conversational retrieval chains for document Q&A.

    This class provides methods to create and manage conversation chains
    that combine LLM capabilities with document retrieval for contextual
    question answering.

    Example:
        >>> manager = ConversationManager()
        >>> chain = manager.create_chain(vectorstore)
        >>> response = manager.ask("What is the main finding?")
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the conversation manager.

        Args:
            config: Configuration object. Uses default if not provided.
        """
        self.config = config or default_config
        self._chain = None
        self._memory = None
        self._chat_history: List[Dict[str, str]] = []

    @property
    def chain(self):
        """Get the current conversation chain."""
        return self._chain

    @property
    def is_initialized(self) -> bool:
        """Check if conversation chain has been initialized."""
        return self._chain is not None

    @property
    def chat_history(self) -> List[Dict[str, str]]:
        """Get the chat history."""
        return self._chat_history.copy()

    def create_chain(self, vectorstore) -> ConversationalRetrievalChain:
        """
        Create a conversational retrieval chain.

        Args:
            vectorstore: Vector store with document embeddings.

        Returns:
            ConversationalRetrievalChain: Initialized conversation chain.

        Raises:
            ConversationError: If chain creation fails.
        """
        try:
            # Initialize LLM
            llm = ChatOpenAI(
                model_name=self.config.llm_model_name,
                temperature=self.config.llm_temperature
            )

            # Initialize conversation memory
            self._memory = ConversationBufferMemory(
                memory_key='chat_history',
                return_messages=True
            )

            # Create the chain with source document retrieval
            self._chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=vectorstore.as_retriever(),
                memory=self._memory,
                return_source_documents=True
            )

            logger.info("Conversation chain created successfully")
            return self._chain

        except Exception as e:
            error_msg = f"Failed to create conversation chain: {str(e)}"
            logger.error(error_msg)
            raise ConversationError(error_msg) from e

    def ask(
        self,
        question: str,
        validate_response: bool = True
    ) -> Dict[str, Any]:
        """
        Ask a question and get a response.

        Args:
            question: The question to ask.
            validate_response: If True, validates response meets minimum length.

        Returns:
            Dict containing 'answer', 'chat_history', and 'is_relevant'.

        Raises:
            ConversationError: If chain not initialized or query fails.
        """
        if not self.is_initialized:
            raise ConversationError(
                "Conversation chain not initialized. Call create_chain first."
            )

        try:
            response = self._chain({'question': question})

            # Extract answer
            answer = ""
            if response.get('chat_history'):
                # Get the last bot message (odd indices are bot responses)
                messages = response['chat_history']
                if len(messages) > 0:
                    answer = messages[-1].content if hasattr(
                        messages[-1], 'content'
                    ) else str(messages[-1])

            # Validate response relevance
            is_relevant = True
            if validate_response:
                is_relevant = len(answer) >= self.config.min_response_length

            # Update chat history
            self._chat_history.append({
                'question': question,
                'answer': answer,
                'is_relevant': is_relevant
            })

            logger.debug(f"Question answered. Relevant: {is_relevant}")

            return {
                'answer': answer,
                'chat_history': response.get('chat_history', []),
                'is_relevant': is_relevant,
                'source_documents': response.get('source_documents', [])
            }

        except Exception as e:
            error_msg = f"Failed to process question: {str(e)}"
            logger.error(error_msg)
            raise ConversationError(error_msg) from e

    def get_formatted_history(self) -> List[Dict[str, str]]:
        """
        Get formatted chat history for display.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        formatted = []
        for entry in self._chat_history:
            formatted.append({
                'role': 'user',
                'content': entry['question']
            })
            formatted.append({
                'role': 'assistant',
                'content': entry['answer']
            })
        return formatted

    def clear_history(self):
        """Clear conversation history and memory."""
        self._chat_history = []
        if self._memory:
            self._memory.clear()
        logger.info("Conversation history cleared")

    def reset(self):
        """Reset the conversation manager completely."""
        self._chain = None
        self._memory = None
        self._chat_history = []
        logger.info("Conversation manager reset")
