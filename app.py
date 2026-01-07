"""
ResearchAI: Answer Extraction from Research Papers

A Streamlit-based web application for extracting and querying
information from PDF research documents using RAG (Retrieval-Augmented Generation).

Usage:
    streamlit run app.py
"""

import logging
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor, PDFProcessingError
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager, VectorStoreError
from src.conversation import ConversationManager, ConversationError
from src.ui.templates import ChatTemplates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "config" not in st.session_state:
        st.session_state.config = Config()

    if "pdf_processor" not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor()

    if "text_processor" not in st.session_state:
        st.session_state.text_processor = TextProcessor(st.session_state.config)

    if "vectorstore_manager" not in st.session_state:
        st.session_state.vectorstore_manager = VectorStoreManager(st.session_state.config)

    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = ConversationManager(st.session_state.config)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "documents_processed" not in st.session_state:
        st.session_state.documents_processed = False


def process_documents(pdf_docs):
    """
    Process uploaded PDF documents through the RAG pipeline.

    Args:
        pdf_docs: List of uploaded PDF file objects.

    Returns:
        bool: True if processing succeeded, False otherwise.
    """
    try:
        # Step 1: Extract text from PDFs
        with st.spinner("Extracting text from PDFs..."):
            raw_text = st.session_state.pdf_processor.extract_text_from_files(pdf_docs)

            if not raw_text.strip():
                st.error("No text could be extracted from the uploaded documents.")
                return False

            # Show processing summary
            summary = st.session_state.pdf_processor.get_processing_summary()
            if summary['failed_count'] > 0:
                st.warning(
                    f"Failed to process {summary['failed_count']} file(s): "
                    f"{', '.join(summary['failed_files'])}"
                )

        # Step 2: Clean and chunk text
        with st.spinner("Processing and chunking text..."):
            text_chunks = st.session_state.text_processor.process(raw_text)

            if not text_chunks:
                st.error("Failed to create text chunks from the documents.")
                return False

            st.info(f"Created {len(text_chunks)} text chunks from your documents.")

        # Step 3: Create vector store
        with st.spinner("Creating embeddings and vector store..."):
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(
                text_chunks
            )

        # Step 4: Initialize conversation chain
        with st.spinner("Setting up conversation chain..."):
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.documents_processed = True
        st.success("Documents processed successfully! You can now ask questions.")
        return True

    except PDFProcessingError as e:
        st.error(f"Error processing PDFs: {str(e)}")
        logger.error(f"PDF processing error: {e}")
        return False

    except VectorStoreError as e:
        st.error(f"Error creating vector store: {str(e)}")
        logger.error(f"Vector store error: {e}")
        return False

    except ConversationError as e:
        st.error(f"Error setting up conversation: {str(e)}")
        logger.error(f"Conversation error: {e}")
        return False

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.exception("Unexpected error during document processing")
        return False


def handle_user_input(user_question: str):
    """
    Handle user question and display response.

    Args:
        user_question: The user's question about the documents.
    """
    if not st.session_state.documents_processed:
        st.error("Please upload and process your PDF documents before asking questions.")
        return

    if not st.session_state.conversation_manager.is_initialized:
        st.error("Conversation not initialized. Please process documents first.")
        return

    try:
        # Get response from conversation chain
        response = st.session_state.conversation_manager.ask(user_question)

        # Update chat history in session state
        st.session_state.chat_history = response.get('chat_history', [])

        # Display chat history
        if st.session_state.chat_history:
            if response.get('is_relevant', True):
                for i, message in enumerate(st.session_state.chat_history):
                    content = message.content if hasattr(message, 'content') else str(message)
                    if i % 2 == 0:  # User messages
                        st.write(
                            ChatTemplates.render_user_message(content),
                            unsafe_allow_html=True
                        )
                    else:  # Bot messages
                        st.write(
                            ChatTemplates.render_bot_message(content),
                            unsafe_allow_html=True
                        )
            else:
                st.write(
                    ChatTemplates.render_warning_message(
                        "There is no relevant information in the document "
                        "related to your question."
                    ),
                    unsafe_allow_html=True
                )

    except ConversationError as e:
        st.error(f"Error processing your question: {str(e)}")
        logger.error(f"Conversation error: {e}")


def render_sidebar():
    """Render the sidebar with document upload and settings."""
    with st.sidebar:
        st.subheader("Document Upload")

        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click 'Process'",
            accept_multiple_files=True,
            type=['pdf']
        )

        if st.button("Process", type="primary"):
            if pdf_docs:
                process_documents(pdf_docs)
            else:
                st.warning("Please upload at least one PDF document.")

        # Display processing status
        if st.session_state.documents_processed:
            st.success("Documents ready for questions!")

        st.divider()

        # Settings section
        st.subheader("Settings")

        # Clear conversation button
        if st.button("Clear Conversation"):
            st.session_state.conversation_manager.clear_history()
            st.session_state.chat_history = []
            st.rerun()

        # Reset all button
        if st.button("Reset All"):
            st.session_state.conversation_manager.reset()
            st.session_state.chat_history = []
            st.session_state.documents_processed = False
            st.rerun()


def main():
    """Main application entry point."""
    # Page configuration
    config = Config()
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout="wide"
    )

    # Apply CSS styles
    st.write(ChatTemplates.get_css(), unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Render header
    st.header(f"{config.page_title} {config.page_icon}")

    st.markdown("""
    Upload your research papers or PDF documents and ask questions about their content.
    The system uses AI to find relevant information and provide accurate answers.
    """)

    # Render sidebar
    render_sidebar()

    # Main content area
    st.divider()

    # Question input
    user_question = st.text_input(
        "Ask a question about your documents:",
        placeholder="e.g., What are the main findings of the research?"
    )

    if user_question:
        handle_user_input(user_question)


if __name__ == '__main__':
    main()
