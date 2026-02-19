"""
ResearchAI: Answer Extraction from Research Papers (Enhanced)

An enhanced Streamlit-based web application for extracting and querying
information from PDF research documents using RAG (Retrieval-Augmented Generation).

Improvements over app.py:
- Uses Streamlit's native chat UI (st.chat_message / st.chat_input)
- Persistent chat history that survives re-runs
- API key validation before document processing
- Progress bar for multi-step document processing
- Graceful handling of missing dependencies

Usage:
    streamlit run app_enhanced.py
"""

import logging
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor, PDFProcessingError
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager, VectorStoreError
from src.conversation import ConversationManager, ConversationError

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

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "documents_processed" not in st.session_state:
        st.session_state.documents_processed = False


def validate_api_keys() -> bool:
    """
    Validate that required API keys are configured.

    Returns:
        bool: True if all required keys are present.
    """
    config = st.session_state.config
    missing = config.get_missing_keys()
    if missing:
        st.error(
            f"Missing required API key(s): {', '.join(missing)}. "
            "Please set them in a `.env` file or as environment variables."
        )
        return False
    return True


def process_documents(pdf_docs):
    """
    Process uploaded PDF documents through the RAG pipeline.

    Args:
        pdf_docs: List of uploaded PDF file objects.

    Returns:
        bool: True if processing succeeded, False otherwise.
    """
    if not validate_api_keys():
        return False

    try:
        progress = st.progress(0, text="Starting document processing...")

        # Step 1: Extract text from PDFs
        progress.progress(10, text="Extracting text from PDFs...")
        raw_text = st.session_state.pdf_processor.extract_text_from_files(pdf_docs)

        if not raw_text.strip():
            st.error("No text could be extracted from the uploaded documents.")
            progress.empty()
            return False

        # Show processing summary
        summary = st.session_state.pdf_processor.get_processing_summary()
        if summary['failed_count'] > 0:
            st.warning(
                f"Failed to process {summary['failed_count']} file(s): "
                f"{', '.join(summary['failed_files'])}"
            )

        # Step 2: Clean and chunk text
        progress.progress(30, text="Processing and chunking text...")
        text_chunks = st.session_state.text_processor.process(raw_text)

        if not text_chunks:
            st.error("Failed to create text chunks from the documents.")
            progress.empty()
            return False

        st.info(f"Created {len(text_chunks)} text chunks from your documents.")

        # Step 3: Create vector store
        progress.progress(50, text="Creating embeddings and vector store...")
        vectorstore = st.session_state.vectorstore_manager.create_vectorstore(
            text_chunks
        )

        # Step 4: Initialize conversation chain
        progress.progress(80, text="Setting up conversation chain...")
        st.session_state.conversation_manager.create_chain(vectorstore)

        progress.progress(100, text="Done!")
        progress.empty()

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
    Handle user question and update chat history.

    Args:
        user_question: The user's question about the documents.
    """
    if not st.session_state.documents_processed:
        st.error("Please upload and process your PDF documents before asking questions.")
        return

    if not st.session_state.conversation_manager.is_initialized:
        st.error("Conversation not initialized. Please process documents first.")
        return

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_question})

    try:
        response = st.session_state.conversation_manager.ask(user_question)

        if response.get('is_relevant', True):
            answer = response.get('answer', 'No answer generated.')
        else:
            answer = (
                "I could not find relevant information in the uploaded documents "
                "to answer your question. Please try rephrasing or ask about "
                "a different topic covered in the documents."
            )

        st.session_state.messages.append({"role": "assistant", "content": answer})

    except ConversationError as e:
        error_msg = f"Error processing your question: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        logger.error(f"Conversation error: {e}")


def render_chat_history():
    """Render all messages in the chat history using Streamlit's chat UI."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


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

        if st.button("Clear Conversation"):
            st.session_state.conversation_manager.clear_history()
            st.session_state.messages = []
            st.rerun()

        if st.button("Reset All"):
            st.session_state.conversation_manager.reset()
            st.session_state.messages = []
            st.session_state.documents_processed = False
            st.rerun()


def main():
    """Main application entry point."""
    config = Config()
    st.set_page_config(
        page_title=config.page_title,
        page_icon=config.page_icon,
        layout="wide"
    )

    # Initialize session state
    initialize_session_state()

    # Header
    st.header(f"{config.page_title} {config.page_icon}")
    st.markdown(
        "Upload your research papers or PDF documents and ask questions "
        "about their content. The system uses AI to find relevant information "
        "and provide accurate answers."
    )

    # Sidebar
    render_sidebar()

    st.divider()

    # Render existing chat history
    render_chat_history()

    # Chat input at the bottom
    if user_question := st.chat_input(
        "Ask a question about your documents...",
        disabled=not st.session_state.documents_processed
    ):
        handle_user_input(user_question)
        # Re-render the latest messages
        with st.chat_message("user"):
            st.markdown(user_question)
        with st.chat_message("assistant"):
            st.markdown(st.session_state.messages[-1]["content"])


if __name__ == '__main__':
    main()
