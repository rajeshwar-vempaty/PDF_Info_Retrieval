"""
PaperMind: AI-Powered Research Paper Analysis

A clean, professional Streamlit application for understanding research papers.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor, PDFProcessingError
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager, VectorStoreError
from src.conversation import ConversationManager, ConversationError
from src.document_analyzer import DocumentAnalyzer
from src.paper_analyzer import PaperAnalyzer, Section, Term, Figure

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== CUSTOM CSS ====================
CUSTOM_CSS = """
<style>
/* Dark theme base */
.stApp {
    background-color: #0f172a;
}

/* Hide only footer */
footer {visibility: hidden;}

/* Scrollbar */
::-webkit-scrollbar {width: 6px; height: 6px;}
::-webkit-scrollbar-track {background: #1e293b;}
::-webkit-scrollbar-thumb {background: #475569; border-radius: 3px;}

/* Section headers */
.section-header {
    font-size: 0.85rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Compact cards */
.info-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
}

/* Term badge */
.term-badge {
    display: inline-block;
    background: rgba(139, 92, 246, 0.15);
    color: #a78bfa;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    margin: 0.125rem;
}

/* Chat message */
.chat-msg {
    padding: 0.75rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    line-height: 1.5;
}

.chat-msg.user {
    background: rgba(139, 92, 246, 0.2);
    color: #e0e7ff;
    margin-left: 15%;
}

.chat-msg.assistant {
    background: #1e293b;
    border: 1px solid #334155;
    color: #f1f5f9;
}

/* Source citation */
.source-box {
    background: rgba(15, 23, 42, 0.5);
    border-left: 2px solid #8b5cf6;
    padding: 0.5rem;
    margin-top: 0.5rem;
    font-size: 0.8rem;
    color: #94a3b8;
    border-radius: 0 4px 4px 0;
}

/* Stats display */
.stat-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}

.stat-item {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    text-align: center;
    min-width: 80px;
}

.stat-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: #8b5cf6;
}

.stat-label {
    font-size: 0.7rem;
    color: #64748b;
}

/* Keywords */
.keyword-tag {
    display: inline-block;
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
    color: white;
    padding: 0.25rem 0.6rem;
    border-radius: 12px;
    font-size: 0.75rem;
    margin: 0.15rem;
}

/* Welcome screen */
.welcome-box {
    text-align: center;
    padding: 2rem;
}

.welcome-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.welcome-subtitle {
    color: #64748b;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

/* Feature grid */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    max-width: 500px;
    margin: 0 auto;
}

.feature-item {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}

.feature-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.feature-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 0.25rem;
}

.feature-desc {
    font-size: 0.75rem;
    color: #64748b;
}

/* Streamlit overrides */
.stButton > button {
    background: #334155 !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
    border-radius: 6px !important;
    padding: 0.35rem 0.75rem !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    background: #475569 !important;
    border-color: #8b5cf6 !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%) !important;
    border: none !important;
}

div[data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.5rem;
}

div[data-testid="stMetricValue"] {
    font-size: 1.25rem !important;
    color: #8b5cf6 !important;
}

div[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    color: #64748b !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: transparent;
}

.stTabs [data-baseweb="tab"] {
    background: #1e293b;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
}

.stTabs [aria-selected="true"] {
    background: #8b5cf6 !important;
}

.stExpander {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
}

.stTextInput input, .stSelectbox > div > div {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    font-size: 0.85rem !important;
}

section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155 !important;
    min-width: 250px !important;
}

section[data-testid="stSidebar"] > div {
    background: #1e293b !important;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #f1f5f9 !important;
}

/* Ensure sidebar is visible */
[data-testid="stSidebar"][aria-expanded="true"] {
    display: block !important;
    visibility: visible !important;
}

/* Radio buttons compact */
.stRadio > div {
    flex-direction: row !important;
    gap: 0.5rem !important;
}

.stRadio label {
    background: #334155 !important;
    padding: 0.3rem 0.6rem !important;
    border-radius: 4px !important;
    font-size: 0.75rem !important;
}
</style>
"""


def init_session_state():
    """Initialize session state."""
    defaults = {
        "config": Config(),
        "messages": [],
        "documents_processed": False,
        "document_analysis": None,
        "paper_analysis": None,
        "raw_text": "",
        "current_filename": None,
        "explanation_level": "detailed",
        "nav_tab": "outline",
        "term_defs": {},
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # Initialize processors
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
    if "paper_analyzer" not in st.session_state:
        st.session_state.paper_analyzer = PaperAnalyzer(st.session_state.config)


def process_documents(pdf_docs):
    """Process uploaded PDFs."""
    try:
        st.session_state.current_filename = pdf_docs[0].name if pdf_docs else None

        with st.spinner("Extracting text..."):
            raw_text = st.session_state.pdf_processor.extract_text_from_files(pdf_docs)
            if not raw_text.strip():
                st.error("No text extracted from documents.")
                return False
            st.session_state.raw_text = raw_text

        with st.spinner("Analyzing structure..."):
            st.session_state.paper_analysis = st.session_state.paper_analyzer.analyze_paper(raw_text)

        with st.spinner("Generating insights..."):
            st.session_state.document_analysis = st.session_state.document_analyzer.analyze_document(raw_text)

        with st.spinner("Creating embeddings..."):
            chunks = st.session_state.text_processor.process(raw_text)
            if not chunks:
                st.error("Failed to process text.")
                return False
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(chunks)

        with st.spinner("Setting up AI..."):
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.documents_processed = True
        st.session_state.messages = []
        return True

    except Exception as e:
        st.error(f"Error: {str(e)}")
        logger.exception("Processing error")
        return False


def ask_question(question: str):
    """Process a question."""
    if not st.session_state.documents_processed:
        return

    level = st.session_state.explanation_level
    prompts = {
        'brief': 'Answer briefly in 1-2 sentences.',
        'detailed': 'Provide a detailed explanation.',
        'expert': 'Provide a comprehensive technical explanation.'
    }

    enhanced = f"{question}\n\n{prompts.get(level, '')}"
    st.session_state.messages.append({"role": "user", "content": question})

    try:
        response = st.session_state.conversation_manager.ask(enhanced)
        answer = response.get('answer', 'No answer found.')
        sources = []

        if response.get('source_documents'):
            sources = [doc.page_content[:150] + "..." for doc in response['source_documents'][:2]]

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"Error: {str(e)}"
        })


def render_sidebar():
    """Render sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.75rem 0;">
            <span style="font-size: 1.75rem;">📚</span>
            <h2 style="margin: 0.25rem 0; font-size: 1.25rem;
                background: linear-gradient(135deg, #8b5cf6, #a855f7);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                PaperMind
            </h2>
            <p style="color: #64748b; font-size: 0.75rem; margin: 0;">AI Research Assistant</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Upload
        st.markdown('<p class="section-header">Upload Paper</p>', unsafe_allow_html=True)
        pdf_docs = st.file_uploader(
            "PDF", accept_multiple_files=True, type=['pdf'],
            label_visibility="collapsed"
        )

        if st.button("Analyze", type="primary", use_container_width=True):
            if pdf_docs:
                if process_documents(pdf_docs):
                    st.success("Ready!")
                    st.rerun()
            else:
                st.warning("Upload a PDF first.")

        if st.session_state.documents_processed:
            st.caption(f"✓ {st.session_state.current_filename}")

        st.divider()

        # Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_manager.clear_history()
                st.rerun()
        with col2:
            if st.button("Reset", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # Export
        if st.session_state.messages:
            st.divider()
            export_data = json.dumps({
                'app': 'PaperMind',
                'date': datetime.now().isoformat(),
                'chat': st.session_state.messages
            }, indent=2)
            st.download_button(
                "Export Chat", export_data,
                f"chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                use_container_width=True
            )


def render_welcome():
    """Render welcome screen."""
    st.markdown("""
    <div class="welcome-box">
        <div class="welcome-title">📚 PaperMind</div>
        <div class="welcome-subtitle">AI-Powered Research Paper Analysis</div>
        <p style="color: #94a3b8; max-width: 450px; margin: 0 auto 1.5rem; font-size: 0.9rem;">
            Upload research papers and get instant explanations of complex concepts,
            equations, and technical terminology.
        </p>
        <div class="feature-grid">
            <div class="feature-item">
                <div class="feature-icon">📖</div>
                <div class="feature-title">Glossary</div>
                <div class="feature-desc">Auto-detect technical terms</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📐</div>
                <div class="feature-title">Equations</div>
                <div class="feature-desc">Step-by-step explanations</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Figures</div>
                <div class="feature-desc">Visual element analysis</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">💬</div>
                <div class="feature-title">Q&A</div>
                <div class="feature-desc">Ask anything about the paper</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.info("👈 Upload a PDF from the sidebar to begin")


def render_navigation():
    """Render left navigation panel."""
    paper = st.session_state.paper_analysis or {}

    # Tab buttons
    tabs = {"outline": "Outline", "terms": "Terms", "figures": "Figures"}
    cols = st.columns(3)
    for i, (key, label) in enumerate(tabs.items()):
        with cols[i]:
            btn_type = "primary" if st.session_state.nav_tab == key else "secondary"
            if st.button(label, key=f"nav_{key}", type=btn_type, use_container_width=True):
                st.session_state.nav_tab = key
                st.rerun()

    st.markdown("---")

    # Content based on tab
    if st.session_state.nav_tab == "outline":
        sections = paper.get('sections', [])
        if sections:
            for sec in sections[:8]:
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(f"○ {sec.title}", key=f"sec_{sec.id}", use_container_width=True):
                        ask_question(f"Summarize the {sec.title} section.")
                        st.rerun()
                with col2:
                    st.caption(f"p.{sec.page}")
        else:
            st.caption("No sections detected")

    elif st.session_state.nav_tab == "terms":
        terms = paper.get('terms', [])
        if terms:
            for term in terms[:10]:
                with st.expander(f"{term.term} ({term.frequency}x)"):
                    if term.term in st.session_state.term_defs:
                        st.write(st.session_state.term_defs[term.term])
                    else:
                        st.caption(term.context[:100] + "..." if term.context else "")
                    if st.button("Explain", key=f"term_{term.term}"):
                        with st.spinner("..."):
                            defn = st.session_state.paper_analyzer.generate_term_definition(
                                term.term, term.context
                            )
                            st.session_state.term_defs[term.term] = defn
                            st.rerun()
        else:
            st.caption("No terms detected")

    else:  # figures
        figures = paper.get('figures', [])
        if figures:
            for fig in figures[:8]:
                icon = {'figure': '📊', 'table': '📋', 'equation': '📐'}.get(fig.type, '📄')
                with st.expander(f"{icon} {fig.title}"):
                    st.caption(f"Page {fig.page} • {fig.type}")
                    if st.button("Explain", key=f"fig_{fig.id}"):
                        ask_question(f"Explain {fig.title}")
                        st.rerun()
        else:
            st.caption("No figures detected")


def render_chat():
    """Render chat panel."""
    # Explanation level
    st.markdown('<p class="section-header">Response Detail</p>', unsafe_allow_html=True)
    level = st.radio(
        "Level", ["brief", "detailed", "expert"],
        index=["brief", "detailed", "expert"].index(st.session_state.explanation_level),
        horizontal=True, label_visibility="collapsed"
    )
    if level != st.session_state.explanation_level:
        st.session_state.explanation_level = level

    # Quick actions
    st.markdown('<p class="section-header">Quick Actions</p>', unsafe_allow_html=True)
    cols = st.columns(4)
    actions = [
        ("✨ Summary", "Summarize this paper in detail."),
        ("💡 Takeaways", "What are the key takeaways?"),
        ("📐 Equations", "Explain the main equations."),
        ("🧠 Prerequisites", "What knowledge is needed?"),
    ]
    for i, (label, question) in enumerate(actions):
        with cols[i]:
            if st.button(label, use_container_width=True):
                ask_question(question)
                st.rerun()

    st.markdown("---")

    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-msg user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            content = msg["content"]
            sources_html = ""
            if msg.get("sources"):
                sources_html = '<div class="source-box">'
                for src in msg["sources"]:
                    sources_html += f"<div>📍 {src}</div>"
                sources_html += '</div>'
            st.markdown(f'<div class="chat-msg assistant">{content}{sources_html}</div>', unsafe_allow_html=True)

    # Suggested questions
    if not st.session_state.messages:
        analysis = st.session_state.document_analysis
        if analysis and analysis.get('suggested_questions'):
            st.markdown('<p class="section-header">Suggested Questions</p>', unsafe_allow_html=True)
            for q in analysis['suggested_questions'][:3]:
                if st.button(f"→ {q}", key=f"sq_{hash(q)}"):
                    ask_question(q)
                    st.rerun()

    # Input
    st.markdown("---")
    question = st.chat_input("Ask about the paper...")
    if question:
        ask_question(question)
        st.rerun()


def render_analysis():
    """Render analysis panel."""
    analysis = st.session_state.document_analysis
    paper = st.session_state.paper_analysis

    if not analysis:
        return

    # Stats
    stats = analysis.get('stats', {})
    st.markdown('<p class="section-header">Statistics</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    items = [
        ("📝", "Words", stats.get('words', '-')),
        ("⏱️", "Read Time", stats.get('reading_time', '-')),
        ("💬", "Sentences", stats.get('sentences', '-')),
        ("📊", "Figures", len(paper.get('figures', [])) if paper else 0),
    ]
    for i, (icon, label, val) in enumerate(items):
        with cols[i]:
            st.metric(f"{icon} {label}", val)

    # Summary
    st.markdown('<p class="section-header">Summary</p>', unsafe_allow_html=True)
    if analysis.get('summary'):
        st.info(analysis['summary'])

    # Keywords
    st.markdown('<p class="section-header">Key Topics</p>', unsafe_allow_html=True)
    keywords = analysis.get('keywords', [])
    if keywords:
        html = "".join([f'<span class="keyword-tag">{k}</span>' for k in keywords[:10]])
        st.markdown(html, unsafe_allow_html=True)

    # Citations
    if paper and paper.get('citations'):
        st.markdown('<p class="section-header">Top References</p>', unsafe_allow_html=True)
        for cit in paper['citations'][:5]:
            st.caption(f"• {cit.authors} ({cit.year}) - {cit.cited_count}x cited")


def main():
    """Main entry point."""
    st.set_page_config(
        page_title="PaperMind",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    init_session_state()
    render_sidebar()

    if not st.session_state.documents_processed:
        render_welcome()
    else:
        # Main layout
        col_nav, col_main = st.columns([1, 3])

        with col_nav:
            render_navigation()

        with col_main:
            tab1, tab2 = st.tabs(["💬 Chat", "📊 Analysis"])

            with tab1:
                render_chat()

            with tab2:
                render_analysis()


if __name__ == '__main__':
    main()
