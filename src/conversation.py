"""
Conversation module for managing RAG-based chat interactions.

This module handles the creation and management of conversational
retrieval chains for question answering over documents.
"""

import logging
from typing import Optional, List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage

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
        self._retriever = None
        self._llm = None
        self._message_history: List = []  # List of HumanMessage/AIMessage
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

    def create_chain(self, vectorstore):
        """
        Create a conversational retrieval chain.

        Args:
            vectorstore: Vector store with document embeddings.

        Returns:
            The initialized conversation chain.

        Raises:
            ConversationError: If chain creation fails.
        """
        try:
            # Initialize LLM
            self._llm = ChatOpenAI(
                model_name=self.config.llm_model_name,
                temperature=self.config.llm_temperature
            )

            # Get retriever
            self._retriever = vectorstore.as_retriever()

            # Build the chain using LCEL
            prompt = ChatPromptTemplate.from_messages([
                ("system",
                 "You are a helpful research assistant. Use the following "
                 "context from research documents to answer the user's question. "
                 "If you cannot find the answer in the context, say so clearly.\n\n"
                 "Context:\n{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
            ])

            def format_docs(docs):
                return "\n\n".join(doc.page_content for doc in docs)

            # Store retriever reference for source document access
            self._last_source_docs = []

            def retrieve_and_store(question):
                docs = self._retriever.invoke(question)
                self._last_source_docs = docs
                return format_docs(docs)

            self._chain = (
                {
                    "context": lambda x: retrieve_and_store(x["question"]),
                    "question": lambda x: x["question"],
                    "chat_history": lambda x: x["chat_history"],
                }
                | prompt
                | self._llm
                | StrOutputParser()
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
            Dict containing 'answer', 'chat_history', 'is_relevant',
            and 'source_documents'.

        Raises:
            ConversationError: If chain not initialized or query fails.
        """
        if not self.is_initialized:
            raise ConversationError(
                "Conversation chain not initialized. Call create_chain first."
            )

        try:
            self._last_source_docs = []

            answer = self._chain.invoke({
                "question": question,
                "chat_history": self._message_history,
            })

            # Update message history for future context
            self._message_history.append(HumanMessage(content=question))
            self._message_history.append(AIMessage(content=answer))

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
                'chat_history': self._message_history,
                'is_relevant': is_relevant,
                'source_documents': self._last_source_docs,
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
        self._message_history = []
        logger.info("Conversation history cleared")

    def reset(self):
        """Reset the conversation manager completely."""
        self._chain = None
        self._retriever = None
        self._llm = None
        self._message_history = []
        self._chat_history = []
        logger.info("Conversation manager reset")
