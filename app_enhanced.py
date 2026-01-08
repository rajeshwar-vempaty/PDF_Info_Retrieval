"""
PaperMind: AI-Powered Research Paper Analysis
Clean, professional UI for understanding research papers.
"""

import json
import logging
from datetime import datetime
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager
from src.conversation import ConversationManager, ConversationError
from src.document_analyzer import DocumentAnalyzer
from src.paper_analyzer import PaperAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CSS ====================
CSS = """
<style>
.stApp { background-color: #0f172a; }
footer { visibility: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155;
}
section[data-testid="stSidebar"] > div { background: #1e293b !important; }

/* Cards */
.card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.card-title {
    font-weight: 600;
    color: #f1f5f9;
    font-size: 0.9rem;
}

.card-badge {
    background: #8b5cf6;
    color: white;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
}

.card-content {
    color: #94a3b8;
    font-size: 0.8rem;
    line-height: 1.5;
}

/* Equation display */
.equation-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #8b5cf6;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.equation-formula {
    font-family: 'Courier New', monospace;
    font-size: 1rem;
    color: #e0e7ff;
    background: #0f172a;
    padding: 0.75rem;
    border-radius: 4px;
    text-align: center;
    margin-bottom: 0.5rem;
}

.equation-label {
    color: #a78bfa;
    font-size: 0.75rem;
    text-align: right;
}

/* Figure display */
.figure-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.figure-icon {
    width: 40px;
    height: 40px;
    background: #334155;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
}

.figure-info { flex: 1; }
.figure-title { color: #f1f5f9; font-size: 0.85rem; font-weight: 500; }
.figure-meta { color: #64748b; font-size: 0.7rem; margin-top: 0.25rem; }

/* Stats row */
.stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.stat-box {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.75rem;
    text-align: center;
}

.stat-value { color: #8b5cf6; font-size: 1.25rem; font-weight: 600; }
.stat-label { color: #64748b; font-size: 0.7rem; margin-top: 0.25rem; }

/* Keywords */
.keyword {
    display: inline-block;
    background: linear-gradient(135deg, #8b5cf6, #a855f7);
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 10px;
    font-size: 0.7rem;
    margin: 0.1rem;
}

/* Chat */
.user-msg {
    background: rgba(139, 92, 246, 0.2);
    color: #e0e7ff;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.5rem 0 0.5rem 20%;
    font-size: 0.85rem;
}

.ai-msg {
    background: #1e293b;
    border: 1px solid #334155;
    color: #f1f5f9;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.5rem 20% 0.5rem 0;
    font-size: 0.85rem;
    line-height: 1.6;
}

.source-ref {
    background: rgba(15, 23, 42, 0.5);
    border-left: 2px solid #8b5cf6;
    padding: 0.5rem;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: #94a3b8;
}

/* Section header */
.section-title {
    color: #94a3b8;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 1rem 0 0.5rem 0;
}

/* Welcome */
.welcome-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.5rem;
}

.welcome-sub {
    color: #64748b;
    text-align: center;
    margin-bottom: 1.5rem;
}

/* Streamlit overrides */
.stButton > button {
    background: #334155 !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    padding: 0.4rem 0.75rem !important;
}

.stButton > button:hover {
    background: #475569 !important;
    border-color: #8b5cf6 !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8b5cf6, #a855f7) !important;
    border: none !important;
}

div[data-testid="stMetric"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 0.5rem;
}

div[data-testid="stMetricValue"] { color: #8b5cf6 !important; font-size: 1.1rem !important; }
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.7rem !important; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: #1e293b; border-radius: 6px; padding: 0.25rem; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 4px; font-size: 0.8rem; padding: 0.5rem 1rem; }
.stTabs [aria-selected="true"] { background: #8b5cf6 !important; }

.stExpander { background: #1e293b; border: 1px solid #334155; border-radius: 6px; }
.stTextInput input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; }
</style>
"""


def init_state():
    """Initialize session state."""
    if "config" not in st.session_state:
        st.session_state.config = Config()
        st.session_state.pdf_processor = PDFProcessor()
        st.session_state.text_processor = TextProcessor(st.session_state.config)
        st.session_state.vectorstore_manager = VectorStoreManager(st.session_state.config)
        st.session_state.conversation_manager = ConversationManager(st.session_state.config)
        st.session_state.document_analyzer = DocumentAnalyzer(st.session_state.config)
        st.session_state.paper_analyzer = PaperAnalyzer(st.session_state.config)

    for key, val in [("messages", []), ("processed", False), ("analysis", None),
                      ("paper", None), ("text", ""), ("filename", None), ("level", "detailed")]:
        if key not in st.session_state:
            st.session_state[key] = val


def process_pdf(files):
    """Process uploaded PDFs."""
    try:
        st.session_state.filename = files[0].name if files else None

        with st.spinner("Extracting text..."):
            text = st.session_state.pdf_processor.extract_text_from_files(files)
            if not text.strip():
                st.error("No text found in PDF.")
                return False
            st.session_state.text = text

        with st.spinner("Analyzing paper..."):
            st.session_state.paper = st.session_state.paper_analyzer.analyze_paper(text)
            st.session_state.analysis = st.session_state.document_analyzer.analyze_document(text)

        with st.spinner("Building index..."):
            chunks = st.session_state.text_processor.process(text)
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(chunks)
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.processed = True
        st.session_state.messages = []
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def ask(question):
    """Ask a question."""
    if not st.session_state.processed:
        return

    prompts = {'brief': 'Be brief.', 'detailed': 'Explain in detail.', 'expert': 'Give technical depth.'}
    enhanced = f"{question}\n\n{prompts.get(st.session_state.level, '')}"

    st.session_state.messages.append({"role": "user", "content": question})

    try:
        response = st.session_state.conversation_manager.ask(enhanced)
        sources = [d.page_content[:150] + "..." for d in response.get('source_documents', [])[:2]]
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get('answer', 'No answer.'),
            "sources": sources
        })
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})


def render_sidebar():
    """Render sidebar."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0;">
            <span style="font-size: 2rem;">📚</span>
            <h2 style="margin: 0.25rem 0; background: linear-gradient(135deg, #8b5cf6, #a855f7);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 1.5rem;">
                PaperMind</h2>
            <p style="color: #64748b; font-size: 0.8rem; margin: 0;">AI Research Assistant</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Upload
        files = st.file_uploader("Upload PDF", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")

        if st.button("🚀 Analyze Paper", type="primary", use_container_width=True):
            if files:
                if process_pdf(files):
                    st.rerun()
            else:
                st.warning("Upload a PDF first")

        if st.session_state.processed:
            st.success(f"✓ {st.session_state.filename}")

        st.divider()

        # Response level
        st.markdown("**Response Level**")
        st.session_state.level = st.radio(
            "level", ["brief", "detailed", "expert"],
            index=1, horizontal=True, label_visibility="collapsed"
        )

        st.divider()

        # Actions
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_manager.clear_history()
                st.rerun()
        with c2:
            if st.button("Reset All", use_container_width=True):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


def render_welcome():
    """Render welcome screen."""
    st.markdown('<div class="welcome-title">📚 PaperMind</div>', unsafe_allow_html=True)
    st.markdown('<p class="welcome-sub">AI-Powered Research Paper Analysis</p>', unsafe_allow_html=True)

    st.markdown("""
    <p style="text-align:center; color:#94a3b8; max-width:500px; margin:0 auto 2rem;">
    Upload research papers and get instant explanations of complex concepts, equations, and terminology.
    </p>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    features = [("📖", "Glossary", "Technical terms"), ("📐", "Equations", "Step-by-step"),
                ("📊", "Figures", "Visual analysis"), ("💬", "Q&A", "Ask anything")]
    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div class="card-title">{title}</div>
                <div class="card-content">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.info("👈 Upload a PDF from the sidebar to begin")


def render_overview():
    """Render overview tab with stats, summary, keywords."""
    analysis = st.session_state.analysis
    paper = st.session_state.paper

    if not analysis:
        return

    stats = analysis.get('stats', {})
    figures = paper.get('figures', []) if paper else []

    # Stats
    st.markdown('<div class="section-title">📊 Statistics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Words", stats.get('words', '-'))
    c2.metric("Read Time", stats.get('reading_time', '-'))
    c3.metric("Sentences", stats.get('sentences', '-'))
    c4.metric("Figures", len([f for f in figures if f.type in ['figure', 'table']]))

    # Summary
    st.markdown('<div class="section-title">📋 Summary</div>', unsafe_allow_html=True)
    if analysis.get('summary'):
        st.info(analysis['summary'])

    # Keywords
    st.markdown('<div class="section-title">🏷️ Key Topics</div>', unsafe_allow_html=True)
    keywords = analysis.get('keywords', [])[:12]
    if keywords:
        html = "".join([f'<span class="keyword">{k}</span>' for k in keywords])
        st.markdown(html, unsafe_allow_html=True)


def render_equations():
    """Render equations tab."""
    paper = st.session_state.paper
    if not paper:
        return

    equations = [f for f in paper.get('figures', []) if f.type == 'equation']

    st.markdown('<div class="section-title">📐 Equations Found</div>', unsafe_allow_html=True)

    if not equations:
        st.caption("No equations detected in this paper.")
        return

    for eq in equations[:10]:
        st.markdown(f"""
        <div class="equation-card">
            <div class="equation-formula">{eq.content[:100]}</div>
            <div class="equation-label">{eq.title} • Page {eq.page}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Explain {eq.title}", key=f"eq_{eq.id}"):
            ask(f"Explain this equation step by step: {eq.content}")
            st.rerun()


def render_figures():
    """Render figures and tables tab."""
    paper = st.session_state.paper
    if not paper:
        return

    figures = [f for f in paper.get('figures', []) if f.type in ['figure', 'table']]

    st.markdown('<div class="section-title">📊 Figures & Tables</div>', unsafe_allow_html=True)

    if not figures:
        st.caption("No figures or tables detected.")
        return

    for fig in figures[:10]:
        icon = "📊" if fig.type == "figure" else "📋"
        st.markdown(f"""
        <div class="figure-card">
            <div class="figure-icon">{icon}</div>
            <div class="figure-info">
                <div class="figure-title">{fig.title}</div>
                <div class="figure-meta">{fig.type.title()} • Page {fig.page}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(fig.caption[:100] + "..." if len(fig.caption) > 100 else fig.caption)
        with col2:
            if st.button("Explain", key=f"fig_{fig.id}"):
                ask(f"Explain {fig.title}: {fig.caption}")
                st.rerun()


def render_terms():
    """Render technical terms tab."""
    paper = st.session_state.paper
    if not paper:
        return

    terms = paper.get('terms', [])[:15]

    st.markdown('<div class="section-title">📖 Technical Terms</div>', unsafe_allow_html=True)

    if not terms:
        st.caption("No technical terms detected.")
        return

    for term in terms:
        with st.expander(f"**{term.term}** ({term.frequency}x)"):
            if term.context:
                st.caption(f"Context: {term.context[:150]}...")
            if st.button("Get Definition", key=f"term_{term.term}"):
                ask(f"Define '{term.term}' in the context of this paper.")
                st.rerun()


def render_chat():
    """Render chat interface."""
    # Quick actions
    st.markdown('<div class="section-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    actions = [("✨ Summary", "Summarize this paper."),
               ("💡 Takeaways", "What are the key takeaways?"),
               ("📐 Equations", "Explain the main equations."),
               ("🧠 Prerequisites", "What background knowledge is needed?")]

    for i, (label, q) in enumerate(actions):
        with [c1, c2, c3, c4][i]:
            if st.button(label, use_container_width=True):
                ask(q)
                st.rerun()

    st.markdown("---")

    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            sources_html = ""
            if msg.get("sources"):
                sources_html = '<div class="source-ref">' + "<br>".join([f"📍 {s}" for s in msg["sources"]]) + '</div>'
            st.markdown(f'<div class="ai-msg">{msg["content"]}{sources_html}</div>', unsafe_allow_html=True)

    # Suggested questions
    if not st.session_state.messages:
        analysis = st.session_state.analysis
        if analysis and analysis.get('suggested_questions'):
            st.markdown('<div class="section-title">💡 Suggested Questions</div>', unsafe_allow_html=True)
            for q in analysis['suggested_questions'][:3]:
                if st.button(f"→ {q}", key=f"sq_{hash(q)}"):
                    ask(q)
                    st.rerun()

    # Input
    st.markdown("---")
    question = st.chat_input("Ask about the paper...")
    if question:
        ask(question)
        st.rerun()


def main():
    st.set_page_config(page_title="PaperMind", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)

    init_state()
    render_sidebar()

    if not st.session_state.processed:
        render_welcome()
    else:
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📊 Overview", "📐 Equations", "📊 Figures", "📖 Terms"])

        with tab1:
            render_chat()
        with tab2:
            render_overview()
        with tab3:
            render_equations()
        with tab4:
            render_figures()
        with tab5:
            render_terms()


if __name__ == '__main__':
    main()
