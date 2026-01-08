"""
PaperMind: AI-Powered Research Paper Analysis

An advanced Streamlit application for understanding research papers with:
- Automatic section detection and navigation
- Technical term glossary with AI explanations
- Equation breakdown and step-by-step explanations
- Figure and table analysis
- Intelligent Q&A with source citations

Usage:
    streamlit run app_enhanced.py
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
from src.ui.dark_theme import DarkTheme

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "config": Config(),
        "pdf_processor": PDFProcessor(),
        "text_processor": None,
        "vectorstore_manager": None,
        "conversation_manager": None,
        "document_analyzer": None,
        "paper_analyzer": None,
        "messages": [],
        "documents_processed": False,
        "document_analysis": None,
        "paper_analysis": None,
        "raw_text": "",
        "active_section": None,
        "explanation_level": "detailed",
        "left_panel_tab": "outline",
        "current_filename": None,
        "term_definitions": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            if key == "text_processor":
                st.session_state[key] = TextProcessor(st.session_state.config)
            elif key == "vectorstore_manager":
                st.session_state[key] = VectorStoreManager(st.session_state.config)
            elif key == "conversation_manager":
                st.session_state[key] = ConversationManager(st.session_state.config)
            elif key == "document_analyzer":
                st.session_state[key] = DocumentAnalyzer(st.session_state.config)
            elif key == "paper_analyzer":
                st.session_state[key] = PaperAnalyzer(st.session_state.config)
            else:
                st.session_state[key] = value


def process_documents(pdf_docs):
    """Process uploaded PDF documents through the RAG pipeline."""
    try:
        # Get filename
        if pdf_docs:
            st.session_state.current_filename = pdf_docs[0].name if len(pdf_docs) == 1 else f"{len(pdf_docs)} documents"

        # Step 1: Extract text from PDFs
        with st.spinner("📄 Extracting text from PDFs..."):
            raw_text = st.session_state.pdf_processor.extract_text_from_files(pdf_docs)

            if not raw_text.strip():
                st.error("No text could be extracted from the uploaded documents.")
                return False

            st.session_state.raw_text = raw_text

        # Step 2: Analyze document structure
        with st.spinner("🔍 Analyzing paper structure..."):
            paper_analysis = st.session_state.paper_analyzer.analyze_paper(raw_text)
            st.session_state.paper_analysis = paper_analysis

        # Step 3: Basic document analysis
        with st.spinner("📊 Generating insights..."):
            analysis = st.session_state.document_analyzer.analyze_document(raw_text)
            st.session_state.document_analysis = analysis

        # Step 4: Clean and chunk text
        with st.spinner("✂️ Processing and chunking text..."):
            text_chunks = st.session_state.text_processor.process(raw_text)

            if not text_chunks:
                st.error("Failed to create text chunks from the documents.")
                return False

        # Step 5: Create vector store
        with st.spinner("🧠 Creating embeddings..."):
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(text_chunks)

        # Step 6: Initialize conversation chain
        with st.spinner("💬 Setting up AI assistant..."):
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.documents_processed = True
        st.session_state.messages = []
        return True

    except Exception as e:
        st.error(f"Error processing documents: {str(e)}")
        logger.exception("Document processing error")
        return False


def handle_question(question: str, context: str = None):
    """Process a question and get response."""
    if not st.session_state.documents_processed:
        st.error("Please upload and process documents first.")
        return

    # Add context for better responses based on explanation level
    level = st.session_state.explanation_level
    level_prompts = {
        'brief': 'Provide a brief, concise answer in 1-2 sentences.',
        'detailed': 'Provide a detailed explanation with examples if helpful.',
        'expert': 'Provide a comprehensive technical explanation suitable for researchers.'
    }

    enhanced_question = f"{question}\n\nInstruction: {level_prompts.get(level, '')}"
    if context:
        enhanced_question = f"Context: {context}\n\n{enhanced_question}"

    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    try:
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.conversation_manager.ask(enhanced_question)

        answer = response.get('answer', 'Sorry, I could not find an answer.')
        sources = []

        if response.get('source_documents'):
            sources = [
                doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
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


def get_term_definition(term: Term) -> str:
    """Get or generate definition for a term."""
    if term.term in st.session_state.term_definitions:
        return st.session_state.term_definitions[term.term]

    # Generate definition using AI
    with st.spinner(f"Getting definition for '{term.term}'..."):
        definition = st.session_state.paper_analyzer.generate_term_definition(
            term.term, term.context
        )
        st.session_state.term_definitions[term.term] = definition
        return definition


def render_left_panel():
    """Render the left navigation panel."""
    st.markdown("### 📑 Navigation")

    # Tab selection
    tab_options = {
        "outline": "📋 Outline",
        "glossary": "📖 Terms",
        "figures": "📊 Figures"
    }

    cols = st.columns(3)
    for i, (key, label) in enumerate(tab_options.items()):
        with cols[i]:
            if st.button(label, key=f"tab_{key}", use_container_width=True,
                        type="primary" if st.session_state.left_panel_tab == key else "secondary"):
                st.session_state.left_panel_tab = key
                st.rerun()

    st.divider()

    paper_analysis = st.session_state.paper_analysis

    if st.session_state.left_panel_tab == "outline":
        render_outline_panel(paper_analysis)
    elif st.session_state.left_panel_tab == "glossary":
        render_glossary_panel(paper_analysis)
    else:
        render_figures_panel(paper_analysis)


def render_outline_panel(paper_analysis: Dict):
    """Render document outline."""
    st.markdown("**Document Structure**")

    sections = paper_analysis.get('sections', [])
    if not sections:
        st.info("No sections detected in this document.")
        return

    for section in sections:
        is_active = st.session_state.active_section == section.id

        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                f"{'▶' if is_active else '○'} {section.title}",
                key=f"section_{section.id}",
                use_container_width=True
            ):
                st.session_state.active_section = section.id
                # Ask about this section
                handle_question(f"Summarize the {section.title} section of this paper.")
                st.rerun()
        with col2:
            st.caption(f"p.{section.page}")

        # Progress bar
        st.progress(section.progress / 100 if section.progress else 0)

    # Reading stats
    st.markdown("---")
    st.markdown("**📊 Reading Progress**")
    total_sections = len(sections)
    completed = sum(1 for s in sections if s.progress >= 100)
    st.metric("Sections Read", f"{completed}/{total_sections}")


def render_glossary_panel(paper_analysis: Dict):
    """Render glossary/terms panel."""
    st.markdown("**🔍 Technical Terms**")

    # Search
    search = st.text_input("Search terms...", key="term_search", placeholder="Type to filter...")

    terms = paper_analysis.get('terms', [])
    if not terms:
        st.info("No technical terms detected.")
        return

    # Filter terms
    if search:
        terms = [t for t in terms if search.lower() in t.term.lower()]

    for term in terms[:15]:
        with st.expander(f"**{term.term}** ({term.frequency}x)", expanded=False):
            # Get or generate definition
            if term.term in st.session_state.term_definitions:
                st.write(st.session_state.term_definitions[term.term])
            else:
                st.caption(term.context[:150] + "..." if term.context else "No context available")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✨ Explain", key=f"explain_{term.term}"):
                    definition = get_term_definition(term)
                    st.rerun()
            with col2:
                if st.button("❓ Ask about", key=f"ask_{term.term}"):
                    handle_question(f"Explain what '{term.term}' means in the context of this paper.")
                    st.rerun()


def render_figures_panel(paper_analysis: Dict):
    """Render figures and tables panel."""
    st.markdown("**📊 Figures & Tables**")

    figures = paper_analysis.get('figures', [])
    if not figures:
        st.info("No figures or tables detected.")
        return

    # Group by type
    fig_types = {'figure': [], 'table': [], 'equation': []}
    for fig in figures:
        if fig.type in fig_types:
            fig_types[fig.type].append(fig)

    type_icons = {'figure': '📊', 'table': '📋', 'equation': '📐'}
    type_colors = {'figure': 'blue', 'table': 'green', 'equation': 'orange'}

    for fig_type, items in fig_types.items():
        if items:
            st.markdown(f"**{type_icons[fig_type]} {fig_type.title()}s ({len(items)})**")

            for item in items[:5]:
                with st.expander(f"{item.title} (p.{item.page})", expanded=False):
                    st.caption(item.caption or item.content[:100])

                    if fig_type == 'equation':
                        if st.button("📐 Explain Step-by-Step", key=f"eq_{item.id}"):
                            explanation = st.session_state.paper_analyzer.explain_equation(
                                item.content, item.caption
                            )
                            st.markdown(DarkTheme.render_equation_explanation(
                                item.content, explanation
                            ), unsafe_allow_html=True)
                    else:
                        if st.button("✨ Explain This", key=f"fig_{item.id}"):
                            handle_question(f"Explain {item.title}: {item.caption}")
                            st.rerun()


def render_chat_panel():
    """Render the main chat panel."""
    # Explanation level toggle
    st.markdown("### 💬 AI Assistant")

    col1, col2, col3 = st.columns(3)
    levels = [('brief', 'Brief'), ('detailed', 'Detailed'), ('expert', 'Expert')]

    for i, (level, label) in enumerate(levels):
        with [col1, col2, col3][i]:
            if st.button(
                label,
                key=f"level_{level}",
                use_container_width=True,
                type="primary" if st.session_state.explanation_level == level else "secondary"
            ):
                st.session_state.explanation_level = level
                st.rerun()

    st.divider()

    # Quick actions
    st.markdown("**⚡ Quick Actions**")
    qa_cols = st.columns(2)

    quick_actions = [
        ("✨ Summarize", "Provide a comprehensive summary of this paper."),
        ("📐 Explain Equations", "List and explain all major equations in this paper."),
        ("💡 Key Takeaways", "What are the key takeaways from this paper?"),
        ("🧠 Prerequisites", "What prerequisite knowledge do I need to understand this paper?"),
    ]

    for i, (label, question) in enumerate(quick_actions):
        with qa_cols[i % 2]:
            if st.button(label, key=f"qa_{i}", use_container_width=True):
                handle_question(question)
                st.rerun()

    st.divider()

    # Chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(
                    DarkTheme.render_user_message(message["content"]),
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    DarkTheme.render_ai_message(
                        message["content"],
                        message.get("sources", [])
                    ),
                    unsafe_allow_html=True
                )

    # Suggested questions
    if not st.session_state.messages and st.session_state.document_analysis:
        st.markdown("**💡 Suggested Questions**")
        questions = st.session_state.document_analysis.get('suggested_questions', [])
        for q in questions[:4]:
            if st.button(f"❓ {q}", key=f"suggested_{hash(q)}"):
                handle_question(q)
                st.rerun()

    st.divider()

    # Chat input
    question = st.chat_input("Ask about the paper...")
    if question:
        handle_question(question)
        st.rerun()


def render_analysis_panel():
    """Render the document analysis panel."""
    st.markdown("### 📊 Document Analysis")

    analysis = st.session_state.document_analysis
    paper_analysis = st.session_state.paper_analysis

    if not analysis:
        st.info("No analysis available.")
        return

    # Stats
    stats = analysis.get('stats', {})
    cols = st.columns(4)
    stat_items = [
        ('📄', 'Words', stats.get('words', 'N/A')),
        ('⏱️', 'Read Time', stats.get('reading_time', 'N/A')),
        ('💬', 'Sentences', stats.get('sentences', 'N/A')),
        ('📊', 'Figures', len(paper_analysis.get('figures', [])) if paper_analysis else 0),
    ]

    for i, (icon, label, value) in enumerate(stat_items):
        with cols[i]:
            st.metric(f"{icon} {label}", value)

    st.divider()

    # Summary
    st.markdown("**📋 Summary**")
    summary = analysis.get('summary', '')
    if summary:
        st.info(summary)

    # Keywords
    st.markdown("**🏷️ Key Topics**")
    keywords = analysis.get('keywords', [])
    if keywords:
        keyword_html = " ".join([
            f'<span style="background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%); '
            f'color: white; padding: 6px 14px; border-radius: 20px; margin: 4px; '
            f'display: inline-block; font-size: 0.85rem;">{kw}</span>'
            for kw in keywords[:12]
        ])
        st.markdown(keyword_html, unsafe_allow_html=True)

    st.divider()

    # Key takeaways (generated on demand)
    st.markdown("**💡 Key Takeaways**")
    if st.button("Generate Key Takeaways", key="gen_takeaways"):
        with st.spinner("Generating..."):
            takeaways = st.session_state.paper_analyzer.get_key_takeaways(
                st.session_state.raw_text
            )
            for i, takeaway in enumerate(takeaways, 1):
                st.markdown(f"{i}. {takeaway}")

    # Prerequisites
    st.markdown("**🧠 Prerequisites**")
    if st.button("Show Prerequisites", key="gen_prereqs"):
        with st.spinner("Analyzing..."):
            prereqs = st.session_state.paper_analyzer.get_prerequisites(
                st.session_state.raw_text
            )
            for prereq in prereqs:
                st.markdown(f"• {prereq}")


def render_sidebar():
    """Render the sidebar."""
    with st.sidebar:
        # Logo
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <span style="font-size: 2.5rem;">📚</span>
            <h2 style="margin: 0.5rem 0 0 0; background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PaperMind</h2>
            <p style="color: #64748b; font-size: 0.85rem; margin: 0;">AI Research Assistant</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Upload
        st.markdown("### 📤 Upload Paper")
        pdf_docs = st.file_uploader(
            "Drop your PDF here",
            accept_multiple_files=True,
            type=['pdf'],
            label_visibility="collapsed"
        )

        if st.button("🚀 Analyze Paper", type="primary", use_container_width=True):
            if pdf_docs:
                if process_documents(pdf_docs):
                    st.success("✅ Paper analyzed!")
                    st.rerun()
            else:
                st.warning("Please upload a PDF first.")

        if st.session_state.documents_processed:
            st.success(f"✅ {st.session_state.current_filename}")

        st.divider()

        # Actions
        st.markdown("### ⚙️ Actions")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_manager.clear_history()
                st.rerun()

        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        # Export
        if st.session_state.messages:
            st.divider()
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'application': 'PaperMind',
                'conversations': st.session_state.messages
            }
            st.download_button(
                label="💾 Export Chat",
                data=json.dumps(export_data, indent=2),
                file_name=f"papermind_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        # Footer
        st.divider()
        st.markdown("""
        <div style="text-align: center; color: #64748b; font-size: 0.75rem;">
            <p>Built with LangChain & Streamlit</p>
            <p>© 2024 PaperMind</p>
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="PaperMind - AI Research Assistant",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply dark theme
    st.markdown(DarkTheme.get_css(), unsafe_allow_html=True)

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Main content
    if not st.session_state.documents_processed:
        # Welcome screen
        st.markdown(DarkTheme.render_welcome(), unsafe_allow_html=True)
        st.markdown(DarkTheme.render_features(), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.info("👈 Upload your research paper from the sidebar to get started!")

    else:
        # Three-panel layout using columns
        left_col, center_col, right_col = st.columns([1, 2, 1.5])

        with left_col:
            render_left_panel()

        with center_col:
            # Tabs for Chat and Analysis
            tab1, tab2 = st.tabs(["💬 Chat", "📊 Analysis"])

            with tab1:
                render_chat_panel()

            with tab2:
                render_analysis_panel()

        with right_col:
            # Document info and citations
            st.markdown("### 📄 Document Info")

            if st.session_state.current_filename:
                st.markdown(f"**File:** {st.session_state.current_filename}")

            paper_analysis = st.session_state.paper_analysis
            if paper_analysis:
                # Citations
                citations = paper_analysis.get('citations', [])
                if citations:
                    st.markdown("**📚 Top References**")
                    for cit in citations[:5]:
                        st.markdown(f"• {cit.authors} ({cit.year}) - cited {cit.cited_count}x")

                # Section summary on demand
                sections = paper_analysis.get('sections', [])
                if sections:
                    st.divider()
                    st.markdown("**📑 Section Summaries**")
                    selected_section = st.selectbox(
                        "Select section",
                        options=[s.title for s in sections],
                        key="section_select"
                    )

                    if st.button("Generate Summary", key="gen_section_summary"):
                        section = next((s for s in sections if s.title == selected_section), None)
                        if section:
                            with st.spinner("Generating..."):
                                summary = st.session_state.paper_analyzer.generate_section_summary(
                                    section,
                                    st.session_state.explanation_level
                                )
                                st.info(summary)

        # Status bar
        if st.session_state.document_analysis:
            stats = st.session_state.document_analysis.get('stats', {})
            paper = st.session_state.paper_analysis or {}
            full_stats = {
                'pages': 'N/A',
                'words': stats.get('words', 'N/A'),
                'figures': len([f for f in paper.get('figures', []) if f.type == 'figure']),
                'tables': len([f for f in paper.get('figures', []) if f.type == 'table']),
            }
            st.markdown(DarkTheme.render_status_bar(full_stats), unsafe_allow_html=True)


if __name__ == '__main__':
    main()
