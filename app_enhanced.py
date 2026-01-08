"""
PaperMind: AI-Powered Research Paper Analysis
Clean, professional UI with image and equation rendering.
"""

import io
import json
import logging
import base64
import re
from datetime import datetime
from pathlib import Path
import streamlit as st

from src.config import Config
from src.pdf_processor import PDFProcessor
from src.text_processor import TextProcessor
from src.vector_store import VectorStoreManager
from src.conversation import ConversationManager, ConversationError
from src.document_analyzer import DocumentAnalyzer
from src.paper_analyzer import PaperAnalyzer

# Try to import image extraction libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CSS ====================
CSS = """
<style>
.stApp { background-color: #0f172a; }
footer { visibility: hidden; }

/* Global text color fix */
body, html, div, p, span, label, li, h1, h2, h3, h4, h5, h6 { color: #e2e8f0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1e293b !important;
    border-right: 1px solid #334155;
}
section[data-testid="stSidebar"] > div { background: #1e293b !important; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Main content text - aggressive override */
.stMarkdown, .stMarkdown *, [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {
    color: #e2e8f0 !important;
}
.stCaption, .stCaption *, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: #94a3b8 !important;
}

/* Cards */
.card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.card-title { font-weight: 600; color: #f1f5f9 !important; font-size: 0.9rem; }
.card-content { color: #cbd5e1 !important; font-size: 0.85rem; line-height: 1.5; }

/* Equation display */
.equation-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 2px solid #8b5cf6;
    border-radius: 10px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.equation-formula {
    font-family: 'Times New Roman', serif;
    font-size: 1.2rem;
    color: #f8fafc !important;
    background: #0f172a;
    padding: 1rem;
    border-radius: 6px;
    text-align: center;
    margin-bottom: 0.75rem;
    border: 1px solid #334155;
}

.equation-label {
    color: #a78bfa !important;
    font-size: 0.8rem;
    text-align: right;
    font-weight: 500;
}

/* Figure display */
.figure-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.figure-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #334155;
}

.figure-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #8b5cf6, #a855f7);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: white;
}

.figure-title { color: #f1f5f9 !important; font-size: 0.95rem; font-weight: 600; }
.figure-meta { color: #94a3b8 !important; font-size: 0.75rem; margin-top: 0.25rem; }
.figure-caption { color: #cbd5e1 !important; font-size: 0.85rem; line-height: 1.5; margin-top: 0.5rem; }

/* Image container */
.image-container {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.5rem;
    margin: 0.75rem 0;
    text-align: center;
}

.image-placeholder {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border: 2px dashed #475569;
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    color: #94a3b8;
}

/* Stats */
.stat-value { color: #a78bfa !important; font-size: 1.25rem; font-weight: 600; }
.stat-label { color: #94a3b8 !important; font-size: 0.75rem; }

/* Keywords */
.keyword {
    display: inline-block;
    background: linear-gradient(135deg, #8b5cf6, #a855f7);
    color: white !important;
    padding: 0.25rem 0.6rem;
    border-radius: 12px;
    font-size: 0.75rem;
    margin: 0.15rem;
}

/* Chat */
.user-msg {
    background: rgba(139, 92, 246, 0.2);
    color: #e0e7ff !important;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    margin: 0.5rem 0 0.5rem 15%;
    font-size: 0.9rem;
    border: 1px solid rgba(139, 92, 246, 0.3);
}

.ai-msg {
    background: #1e293b;
    border: 1px solid #334155;
    color: #f1f5f9 !important;
    padding: 0.75rem 1rem;
    border-radius: 10px;
    margin: 0.5rem 15% 0.5rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
}

.ai-msg p, .ai-msg li, .ai-msg span { color: #f1f5f9 !important; }

.source-ref {
    background: rgba(15, 23, 42, 0.7);
    border-left: 3px solid #8b5cf6;
    padding: 0.5rem 0.75rem;
    margin-top: 0.75rem;
    font-size: 0.8rem;
    color: #94a3b8 !important;
    border-radius: 0 6px 6px 0;
}

/* Section header */
.section-title {
    color: #94a3b8 !important;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin: 1.25rem 0 0.75rem 0;
}

/* Welcome */
.welcome-title {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #8b5cf6, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.5rem;
}

.welcome-sub { color: #94a3b8 !important; text-align: center; font-size: 1.1rem; margin-bottom: 1.5rem; }

/* Terms */
.term-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
}

.term-name { color: #a78bfa !important; font-weight: 600; font-size: 0.9rem; }
.term-freq { color: #64748b !important; font-size: 0.75rem; }
.term-context { color: #cbd5e1 !important; font-size: 0.8rem; margin-top: 0.5rem; }

/* Streamlit overrides */
.stButton > button {
    background: #334155 !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1rem !important;
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
    border-radius: 8px;
    padding: 0.75rem;
}

div[data-testid="stMetricValue"] { color: #a78bfa !important; font-size: 1.2rem !important; }
div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.75rem !important; }

.stTabs [data-baseweb="tab-list"] { gap: 0.25rem; background: #1e293b; border-radius: 8px; padding: 0.25rem; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 6px; font-size: 0.85rem; padding: 0.5rem 1rem; color: #94a3b8 !important; }
.stTabs [aria-selected="true"] { background: #8b5cf6 !important; color: white !important; }

.stExpander { background: #1e293b; border: 1px solid #334155; border-radius: 8px; }
.stExpander summary span { color: #f1f5f9 !important; }

.stTextInput input { background: #1e293b !important; border: 1px solid #334155 !important; color: #f1f5f9 !important; }
.stInfo { background: rgba(139, 92, 246, 0.1) !important; border: 1px solid rgba(139, 92, 246, 0.3) !important; }
.stInfo p { color: #e0e7ff !important; }
</style>
"""


def extract_images_from_pdf(pdf_file) -> list:
    """Extract images from PDF using PyMuPDF with multiple extraction methods."""
    images = []

    if not HAS_PYMUPDF or not HAS_PIL:
        logger.warning("PyMuPDF or PIL not available for image extraction")
        return images

    try:
        # Read PDF bytes
        pdf_bytes = pdf_file.read()
        pdf_file.seek(0)  # Reset for other uses

        # Open with PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        img_count = 0

        for page_num in range(min(len(doc), 20)):  # Limit to first 20 pages
            page = doc[page_num]

            # Method 1: Try get_images() for embedded images
            try:
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list[:5]):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if base_image:
                            image_bytes = base_image["image"]
                            pil_image = Image.open(io.BytesIO(image_bytes))

                            # Only keep reasonably sized images (not icons/logos)
                            if pil_image.width > 100 and pil_image.height > 100:
                                img_count += 1
                                images.append({
                                    'page': page_num + 1,
                                    'index': img_count,
                                    'image': pil_image.convert('RGB'),
                                    'width': pil_image.width,
                                    'height': pil_image.height
                                })
                    except Exception as e:
                        logger.debug(f"Failed to extract embedded image: {e}")
                        continue
            except Exception as e:
                logger.debug(f"get_images failed for page {page_num}: {e}")

            # Method 2: Render page regions as images if no embedded images found
            if len(images) == 0 and page_num < 5:
                try:
                    # Render full page at lower resolution for preview
                    mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))

                    if pil_image.width > 100 and pil_image.height > 100:
                        img_count += 1
                        images.append({
                            'page': page_num + 1,
                            'index': img_count,
                            'image': pil_image.convert('RGB'),
                            'width': pil_image.width,
                            'height': pil_image.height,
                            'is_page_render': True
                        })
                    pix = None
                except Exception as e:
                    logger.debug(f"Page render failed: {e}")

        doc.close()
    except Exception as e:
        logger.error(f"Image extraction failed: {e}")

    return images[:15]  # Limit to 15 images


def extract_equations_from_text(text: str) -> list:
    """Extract equations from text with better pattern matching."""
    equations = []

    # Pattern for labeled equations
    patterns = [
        # Equation (1), Eq. 1, etc.
        r'(?:Equation|Eq\.?)\s*\(?(\d+)\)?\s*[:.]?\s*([^\n]+)',
        # Display math with labels
        r'(\([0-9]+\))\s*$.*?([A-Za-z].*?=.*?)(?:\n|$)',
        # Common equation patterns
        r'([A-Z][a-z]*\([^)]+\))\s*=\s*([^,.\n]+)',
        # Attention, Loss, etc. formulas
        r'((?:Attention|Loss|Softmax|ReLU|BLEU)\s*\([^)]*\))\s*=\s*([^\n]+)',
    ]

    eq_id = 1
    seen = set()

    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            content = match.group(0).strip()
            if content not in seen and len(content) > 10:
                seen.add(content)
                equations.append({
                    'id': eq_id,
                    'content': content[:200],
                    'page': max(1, match.start() // 3000 + 1)
                })
                eq_id += 1

    # Also look for math-like expressions
    math_patterns = [
        r'[A-Za-z]+\s*=\s*(?:softmax|sigmoid|tanh|exp|log|sum|max|min)\s*\([^)]+\)',
        r'[A-Za-z]+\s*=\s*\d+\s*[×*/+-]\s*[A-Za-z0-9]+',
        r'∑|∏|∫|√|∂|∇|α|β|γ|θ|λ|σ|μ',
    ]

    for pattern in math_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            content = match.group(0).strip()
            if content not in seen and len(content) > 5:
                seen.add(content)
                equations.append({
                    'id': eq_id,
                    'content': content[:150],
                    'page': max(1, match.start() // 3000 + 1)
                })
                eq_id += 1

    return equations[:20]


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

    defaults = [("messages", []), ("processed", False), ("analysis", None),
                ("paper", None), ("text", ""), ("filename", None),
                ("level", "detailed"), ("images", []), ("equations", [])]

    for key, val in defaults:
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

        with st.spinner("Extracting images..."):
            st.session_state.images = extract_images_from_pdf(files[0])

        with st.spinner("Finding equations..."):
            st.session_state.equations = extract_equations_from_text(text)

        with st.spinner("Analyzing paper..."):
            st.session_state.paper = st.session_state.paper_analyzer.analyze_paper(text)
            st.session_state.analysis = st.session_state.document_analyzer.analyze_document(text)

        with st.spinner("Building search index..."):
            chunks = st.session_state.text_processor.process(text)
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(chunks)
            st.session_state.conversation_manager.create_chain(vectorstore)

        st.session_state.processed = True
        st.session_state.messages = []
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        logger.exception("Processing error")
        return False


def ask(question):
    """Ask a question."""
    if not st.session_state.processed:
        return

    prompts = {'brief': 'Be concise.', 'detailed': 'Explain thoroughly.', 'expert': 'Provide technical depth.'}
    enhanced = f"{question}\n\n{prompts.get(st.session_state.level, '')}"

    st.session_state.messages.append({"role": "user", "content": question})

    try:
        response = st.session_state.conversation_manager.ask(enhanced)
        sources = [d.page_content[:150] + "..." for d in response.get('source_documents', [])[:2]]
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get('answer', 'No answer found.'),
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
            <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">AI Research Assistant</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        files = st.file_uploader("Upload PDF", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")

        if st.button("🚀 Analyze Paper", type="primary", use_container_width=True):
            if files:
                if process_pdf(files):
                    st.rerun()
            else:
                st.warning("Upload a PDF first")

        if st.session_state.processed:
            st.success(f"✓ {st.session_state.filename}")

            # Show extraction stats
            img_count = len(st.session_state.images)
            eq_count = len(st.session_state.equations)
            st.caption(f"📊 {img_count} images, {eq_count} equations found")

        st.divider()

        st.markdown("**Response Level**")
        st.session_state.level = st.radio(
            "level", ["brief", "detailed", "expert"],
            index=1, horizontal=True, label_visibility="collapsed"
        )

        st.divider()

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
    <p style="text-align:center; color:#cbd5e1; max-width:550px; margin:0 auto 2rem; font-size: 1rem;">
    Upload research papers and get instant explanations of complex concepts, equations, and figures.
    </p>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    features = [("📖", "Glossary", "Technical terms explained"),
                ("📐", "Equations", "Step-by-step math"),
                ("🖼️", "Figures", "Image extraction"),
                ("💬", "Q&A", "Ask anything")]

    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class="card" style="text-align:center; min-height: 120px;">
                <div style="font-size:1.75rem; margin-bottom: 0.5rem;">{icon}</div>
                <div class="card-title">{title}</div>
                <div class="card-content">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.info("👈 Upload a PDF from the sidebar to begin")


def render_overview():
    """Render overview tab."""
    analysis = st.session_state.analysis
    if not analysis:
        return

    stats = analysis.get('stats', {})

    st.markdown('<div class="section-title">📊 Document Statistics</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📝 Words", stats.get('words', '-'))
    c2.metric("⏱️ Read Time", stats.get('reading_time', '-'))
    c3.metric("🖼️ Images", len(st.session_state.images))
    c4.metric("📐 Equations", len(st.session_state.equations))

    st.markdown('<div class="section-title">📋 Summary</div>', unsafe_allow_html=True)
    if analysis.get('summary'):
        st.info(analysis['summary'])

    st.markdown('<div class="section-title">🏷️ Key Topics</div>', unsafe_allow_html=True)
    keywords = analysis.get('keywords', [])[:12]
    if keywords:
        html = "".join([f'<span class="keyword">{k}</span>' for k in keywords])
        st.markdown(html, unsafe_allow_html=True)


def render_equations():
    """Render equations tab with proper display."""
    equations = st.session_state.equations

    st.markdown('<div class="section-title">📐 Mathematical Equations</div>', unsafe_allow_html=True)

    if not equations:
        st.markdown("""
        <div class="image-placeholder">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📐</div>
            <div>No equations detected in this paper</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"Found **{len(equations)}** equations in the paper:")

    for eq in equations:
        st.markdown(f"""
        <div class="equation-card">
            <div class="equation-formula">{eq['content']}</div>
            <div class="equation-label">Equation {eq['id']} • Page {eq['page']}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🔍 Explain Equation {eq['id']}", key=f"eq_{eq['id']}"):
            ask(f"Explain this equation step by step, defining each variable: {eq['content']}")
            st.rerun()


def render_figures():
    """Render figures tab with actual images."""
    images = st.session_state.images
    paper = st.session_state.paper

    st.markdown('<div class="section-title">🖼️ Figures & Images</div>', unsafe_allow_html=True)

    # Show extracted images if available
    if images:
        # Separate page renders from actual images
        actual_images = [img for img in images if not img.get('is_page_render')]
        page_renders = [img for img in images if img.get('is_page_render')]

        if actual_images:
            st.markdown(f"Extracted **{len(actual_images)}** images from the paper:")

            # Display images in a grid
            cols_per_row = 2
            for i in range(0, len(actual_images), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(actual_images):
                        img_data = actual_images[i + j]
                        with col:
                            st.markdown(f"""
                            <div class="figure-card">
                                <div class="figure-header">
                                    <div class="figure-icon">🖼️</div>
                                    <div>
                                        <div class="figure-title">Image {img_data['index']}</div>
                                        <div class="figure-meta">Page {img_data['page']} • {img_data['width']}×{img_data['height']}px</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Display the actual image
                            st.image(img_data['image'], use_container_width=True)

                            if st.button(f"🔍 Explain", key=f"img_{i+j}"):
                                ask(f"Describe what Figure/Image {img_data['index']} on page {img_data['page']} might represent based on the paper's content.")
                                st.rerun()
        elif page_renders:
            st.markdown("**Page Previews** (no embedded images found, showing page renders):")
            for img_data in page_renders:
                st.markdown(f"""
                <div class="figure-card">
                    <div class="figure-header">
                        <div class="figure-icon">📄</div>
                        <div>
                            <div class="figure-title">Page {img_data['page']} Preview</div>
                            <div class="figure-meta">{img_data['width']}×{img_data['height']}px</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.image(img_data['image'], use_container_width=True)

    # Also show figure/table references from text
    if paper:
        figures = [f for f in paper.get('figures', []) if f.type in ['figure', 'table']]
        if figures:
            st.markdown("---")
            st.markdown(f"**Figure/Table References** ({len(figures)} found in text):")
            for fig in figures[:10]:
                icon = "📊" if fig.type == "figure" else "📋"
                st.markdown(f"""
                <div class="figure-card">
                    <div class="figure-header">
                        <div class="figure-icon">{icon}</div>
                        <div>
                            <div class="figure-title">{fig.title}</div>
                            <div class="figure-meta">{fig.type.title()} • Page {fig.page}</div>
                        </div>
                    </div>
                    <div class="figure-caption">{fig.caption}</div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🔍 Explain {fig.title}", key=f"fig_{fig.id}"):
                    ask(f"Explain {fig.title} in detail: {fig.caption}")
                    st.rerun()

    # Show message if nothing found
    if not images and (not paper or not paper.get('figures')):
        st.markdown("""
        <div class="image-placeholder">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🖼️</div>
            <div>No figures could be extracted from this PDF</div>
            <div style="font-size: 0.8rem; margin-top: 0.5rem;">
                This PDF may use vector graphics or have images in an unsupported format.
            </div>
        </div>
        """, unsafe_allow_html=True)


def sanitize_html(text: str) -> str:
    """Sanitize text for safe HTML display."""
    if not text:
        return ""
    # Escape HTML special characters
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#39;')
    return text


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

    st.markdown(f"Found **{len(terms)}** key technical terms:")

    for term in terms:
        # Sanitize term name and context for HTML
        term_name = sanitize_html(term.term)
        context = sanitize_html(term.context) if term.context else "No context available"

        # Truncate context nicely
        if len(context) > 150:
            context = context[:150].rsplit(' ', 1)[0] + "..."

        st.markdown(f"""
        <div class="term-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span class="term-name">{term_name}</span>
                <span class="term-freq">{term.frequency}× mentioned</span>
            </div>
            <div class="term-context">{context}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"📖 Define '{term.term}'", key=f"term_{term.term}"):
            ask(f"Define '{term.term}' in the context of this research paper. What does it mean and why is it important?")
            st.rerun()


def render_chat():
    """Render chat interface."""
    st.markdown('<div class="section-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    actions = [("✨ Summary", "Provide a comprehensive summary of this paper."),
               ("💡 Takeaways", "What are the key takeaways and main contributions?"),
               ("📐 Equations", "Explain the main mathematical equations in this paper."),
               ("🧠 Prerequisites", "What background knowledge is needed to understand this paper?")]

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
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Chat", "📊 Overview", "📐 Equations", "🖼️ Figures", "📖 Terms"])

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
