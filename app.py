"""
ResearchAI: Answer Extraction from Research Papers

A Streamlit-based web application for extracting and querying
information from PDF research documents using RAG (Retrieval-Augmented Generation).

Usage:
    streamlit run app.py
"""

import json
import logging
from datetime import datetime
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor, PDFProcessingError
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager, VectorStoreError
from src.conversation import ConversationManager, ConversationError
from src.document_analyzer import DocumentAnalyzer
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

    if "document_analyzer" not in st.session_state:
        st.session_state.document_analyzer = DocumentAnalyzer(st.session_state.config)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "documents_processed" not in st.session_state:
        st.session_state.documents_processed = False

    if "document_analysis" not in st.session_state:
        st.session_state.document_analysis = None

    if "raw_text" not in st.session_state:
        st.session_state.raw_text = ""


def process_documents(pdf_docs):
    """Process uploaded PDF documents through the RAG pipeline."""
    try:
        # Step 1: Extract text from PDFs
        with st.spinner("📄 Extracting text from PDFs..."):
            raw_text = st.session_state.pdf_processor.extract_text_from_files(pdf_docs)

            if not raw_text.strip():
                st.error("No text could be extracted from the uploaded documents.")
                return False

            st.session_state.raw_text = raw_text

        # Step 2: Analyze document
        with st.spinner("🔍 Analyzing document..."):
            analysis = st.session_state.document_analyzer.analyze_document(raw_text)
            st.session_state.document_analysis = analysis

        # Step 3: Clean and chunk text
        with st.spinner("✂️ Processing and chunking text..."):
            text_chunks = st.session_state.text_processor.process(raw_text)

            if not text_chunks:
                st.error("Failed to create text chunks from the documents.")
                return False

        # Step 4: Create vector store
        with st.spinner("🧠 Creating embeddings..."):
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(
                text_chunks
            )

        # Step 5: Initialize conversation chain
        with st.spinner("💬 Setting up AI assistant..."):
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.documents_processed = True
        st.session_state.messages = []  # Clear previous messages
        return True

    except (PDFProcessingError, VectorStoreError, ConversationError) as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Processing error: {e}")
        return False

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        logger.exception("Unexpected error during document processing")
        return False


def display_document_analysis():
    """Display document analysis panel."""
    if st.session_state.document_analysis:
        analysis = st.session_state.document_analysis

        # Document Statistics
        st.subheader("📊 Document Statistics")
        cols = st.columns(4)
        stats = analysis.get('stats', {})
        stat_items = list(stats.items())
        icons = {'words': '📝', 'characters': '🔤', 'sentences': '💬', 'reading_time': '⏱️'}

        for i, (key, value) in enumerate(stat_items):
            with cols[i % 4]:
                icon = icons.get(key, '📊')
                st.metric(
                    label=f"{icon} {key.replace('_', ' ').title()}",
                    value=value
                )

        # Keywords
        st.subheader("🏷️ Key Topics")
        keywords = analysis.get('keywords', [])
        if keywords:
            keyword_html = " ".join([
                f'<span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                f'color: white; padding: 5px 12px; border-radius: 20px; margin: 3px; '
                f'display: inline-block; font-size: 0.9rem;">{kw}</span>'
                for kw in keywords[:12]
            ])
            st.markdown(keyword_html, unsafe_allow_html=True)

        # Summary
        st.subheader("📋 Document Summary")
        summary = analysis.get('summary', '')
        if summary:
            st.info(summary)

        # Suggested Questions
        st.subheader("💡 Try Asking")
        questions = analysis.get('suggested_questions', [])
        if questions:
            for q in questions[:5]:
                if st.button(f"❓ {q}", key=f"q_{hash(q)}"):
                    st.session_state.pending_question = q
                    st.rerun()


def display_chat():
    """Display chat messages."""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                ChatTemplates.render_user_message(message["content"]),
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                ChatTemplates.render_bot_message(message["content"]),
                unsafe_allow_html=True
            )
            # Show sources if available
            if message.get("sources"):
                with st.expander("📚 View Sources", expanded=False):
                    for i, source in enumerate(message["sources"], 1):
                        st.markdown(
                            ChatTemplates.render_source_citation(i, source),
                            unsafe_allow_html=True
                        )


def handle_question(question: str):
    """Process a question and get response."""
    if not st.session_state.documents_processed:
        st.error("Please upload and process documents first.")
        return

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    try:
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.conversation_manager.ask(question)

        answer = response.get('answer', 'Sorry, I could not find an answer.')
        sources = []

        if response.get('source_documents'):
            sources = [
                doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                for doc in response['source_documents'][:3]
            ]

        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })

    except ConversationError as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Sorry, I encountered an error: {str(e)}"
        })


def export_chat_history():
    """Export chat history as JSON."""
    export_data = {
        'exported_at': datetime.now().isoformat(),
        'application': 'ResearchAI - PDF Info Retrieval',
        'conversations': st.session_state.messages
    }
    return json.dumps(export_data, indent=2)


def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        # Logo/Brand
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="color: #667eea; margin: 0;">📚 ResearchAI</h1>
            <p style="color: #666; font-size: 0.9rem;">Intelligent Document Analysis</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Upload Section
        st.subheader("📤 Upload Documents")
        pdf_docs = st.file_uploader(
            "Drop your PDF files here",
            accept_multiple_files=True,
            type=['pdf'],
            label_visibility="collapsed"
        )

        if st.button("🚀 Process Documents", type="primary", use_container_width=True):
            if pdf_docs:
                if process_documents(pdf_docs):
                    st.success("✅ Ready to chat!")
                    st.rerun()
            else:
                st.warning("Please upload at least one PDF.")

        if st.session_state.documents_processed:
            st.success("✅ Documents loaded")

        st.divider()

        # Actions
        st.subheader("⚙️ Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_manager.clear_history()
                st.rerun()

        with col2:
            if st.button("🔄 Reset All", use_container_width=True):
                for key in ['messages', 'documents_processed', 'document_analysis', 'raw_text']:
                    if key in st.session_state:
                        st.session_state[key] = [] if key == 'messages' else None if key != 'raw_text' else ""
                st.session_state.documents_processed = False
                st.session_state.conversation_manager.reset()
                st.rerun()

        # Export
        if st.session_state.messages:
            st.divider()
            st.subheader("📥 Export")
            st.download_button(
                label="💾 Download Chat",
                data=export_chat_history(),
                file_name=f"research_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        # Footer
        st.divider()
        st.markdown("""
        <div style="text-align: center; color: #888; font-size: 0.8rem;">
            <p>Built with ❤️ using LangChain & Streamlit</p>
            <p>© 2024 ResearchAI</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="ResearchAI - Document Intelligence",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply CSS styles
    st.markdown(ChatTemplates.get_css(), unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Main content
    if not st.session_state.documents_processed:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem;">
            <h1 style="color: #667eea; font-size: 3rem;">📚 ResearchAI</h1>
            <h3 style="color: #666; font-weight: normal;">Intelligent Document Analysis & Q&A</h3>
            <p style="color: #888; max-width: 600px; margin: 1rem auto;">
                Upload your research papers, reports, or any PDF documents.
                Our AI will analyze them and answer your questions with source citations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Features
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 10px;">
                <h2>🔍</h2>
                <h4>Smart Analysis</h4>
                <p style="color: #666; font-size: 0.9rem;">Automatic keyword extraction, summaries, and document statistics</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 10px;">
                <h2>💬</h2>
                <h4>Natural Q&A</h4>
                <p style="color: #666; font-size: 0.9rem;">Ask questions in plain English and get accurate answers</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div style="text-align: center; padding: 1.5rem; background: #f8f9fa; border-radius: 10px;">
                <h2>📚</h2>
                <h4>Source Citations</h4>
                <p style="color: #666; font-size: 0.9rem;">Every answer comes with relevant source passages</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("👈 Upload your PDF documents from the sidebar to get started!")

    else:
        # Document processed - show analysis and chat
        tab1, tab2 = st.tabs(["💬 Chat", "📊 Document Analysis"])

        with tab1:
            st.subheader("💬 Ask Questions About Your Documents")

            # Display chat history
            chat_container = st.container()
            with chat_container:
                display_chat()

            # Check for pending question from suggested questions
            if "pending_question" in st.session_state:
                question = st.session_state.pending_question
                del st.session_state.pending_question
                handle_question(question)
                st.rerun()

            # Chat input
            st.divider()
            question = st.chat_input("Type your question here...")

            if question:
                handle_question(question)
                st.rerun()

            # Quick suggestions if no messages yet
            if not st.session_state.messages and st.session_state.document_analysis:
                st.markdown("**💡 Quick Start - Try these questions:**")
                questions = st.session_state.document_analysis.get('suggested_questions', [])
                cols = st.columns(min(len(questions), 3))
                for i, q in enumerate(questions[:3]):
                    with cols[i]:
                        if st.button(q, key=f"quick_{i}", use_container_width=True):
                            handle_question(q)
                            st.rerun()

        with tab2:
            display_document_analysis()


if __name__ == '__main__':
    main()
