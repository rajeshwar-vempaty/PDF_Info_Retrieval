"""
PaperMind: AI-Powered Research Paper Analysis
Clean, professional UI with image and equation rendering.
Deploy to Streamlit Cloud:
1. Push to GitHub
2. Connect repo at share.streamlit.io
3. Add OPENAI_API_KEY in Secrets
"""
import os
import io
import json
import logging
import base64
import re
from datetime import datetime
from pathlib import Path
import streamlit as st
from src.config import Config


def check_api_key() -> bool:
    """Check if OpenAI API key is configured."""
    # Explicitly load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except (ImportError, Exception):
        pass

    # Check environment variable
    if os.getenv("OPENAI_API_KEY"):
        return True
    # Check Streamlit secrets
    try:
        if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
            os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
            return True
    except Exception:
        pass
    return False


def render_api_key_error():
    """Render a friendly error page when API key is missing."""
    st.set_page_config(page_title="PaperMind - Setup Required", page_icon="🔑", layout="centered")
    st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    .setup-container {
        max-width: 600px;
        margin: 3rem auto;
        padding: 2rem;
        background: #1e293b;
        border-radius: 16px;
        border: 1px solid #334155;
        text-align: center;
    }
    .setup-icon { font-size: 4rem; margin-bottom: 1rem; }
    .setup-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    .setup-subtitle { color: #94a3b8; margin-bottom: 2rem; }
    .step {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
        text-align: left;
    }
    .step-num {
        display: inline-block;
        width: 24px;
        height: 24px;
        background: #8b5cf6;
        color: white;
        border-radius: 50%;
        text-align: center;
        line-height: 24px;
        font-size: 0.8rem;
        margin-right: 0.75rem;
    }
    .step-text { color: #e2e8f0; }
    .code-block {
        background: #0f172a;
        border: 1px solid #475569;
        border-radius: 6px;
        padding: 0.75rem;
        margin-top: 0.5rem;
        font-family: monospace;
        color: #a78bfa;
        font-size: 0.85rem;
    }
    a { color: #8b5cf6 !important; }
    </style>
    <div class="setup-container">
        <div class="setup-icon">🔑</div>
        <div class="setup-title">OpenAI API Key Required</div>
        <div class="setup-subtitle">PaperMind needs an OpenAI API key to analyze papers</div>
        <div class="step">
            <span class="step-num">1</span>
            <span class="step-text">Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a></span>
        </div>
        <div class="step">
            <span class="step-num">2</span>
            <span class="step-text">For <strong>Streamlit Cloud</strong>: Add to app Settings > Secrets</span>
            <div class="code-block">OPENAI_API_KEY = "sk-your-key-here"</div>
        </div>
        <div class="step">
            <span class="step-num">3</span>
            <span class="step-text">For <strong>local development</strong>: Create a .env file</span>
            <div class="code-block">OPENAI_API_KEY=sk-your-key-here</div>
        </div>
        <div style="margin-top: 2rem; color: #64748b; font-size: 0.85rem;">
            After adding your key, refresh this page
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


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

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False


def fetch_scholar_citations(title: str) -> dict:
    """
    Fetch citation count from Google Scholar for a paper title.

    Returns dict with 'citations', 'scholar_url', and 'error' keys.
    """
    result = {'citations': None, 'scholar_url': None, 'error': None}
    if not HAS_URLLIB or not title:
        result['error'] = 'Title not available'
        return result

    try:
        query = urllib.parse.quote(title)
        url = f"https://scholar.google.com/scholar?q={query}"
        result['scholar_url'] = url

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # Look for "Cited by N" pattern
        cited_match = re.search(r'Cited by\s+(\d+)', html)
        if cited_match:
            result['citations'] = int(cited_match.group(1))
        else:
            result['error'] = 'No citation data found'

    except Exception as e:
        result['error'] = str(e)
        logger.debug(f"Scholar lookup failed: {e}")

    return result


def extract_paper_metadata(text: str) -> dict:
    """Extract metadata from paper text: title, authors, year, DOI."""
    metadata = {
        'title': None,
        'authors': [],
        'year': None,
        'doi': None,
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return metadata

    # Title: usually the longest of the first few lines
    candidate_lines = lines[:8]
    title_candidates = [
        l for l in candidate_lines
        if 10 < len(l) < 250
        and not re.match(r'^\d+$', l)
        and not re.match(r'^(abstract|introduction|page)', l, re.IGNORECASE)
    ]
    if title_candidates:
        metadata['title'] = max(title_candidates, key=lambda l: len(l))

    # Year
    year_match = re.search(r'\b(19|20)\d{2}\b', text[:3000])
    if year_match:
        metadata['year'] = year_match.group(0)

    # DOI
    doi_match = re.search(r'(10\.\d{4,}/[^\s]+)', text[:5000])
    if doi_match:
        metadata['doi'] = doi_match.group(1).rstrip('.')

    # Authors: look for comma-separated names before abstract
    abstract_pos = re.search(r'\babstract\b', text, re.IGNORECASE)
    pre_abstract = text[:abstract_pos.start()] if abstract_pos else text[:2000]
    author_match = re.search(
        r'(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)+)',
        pre_abstract
    )
    if author_match:
        author_str = author_match.group(1)
        authors = [a.strip() for a in re.split(r',\s*(?:and\s+)?', author_str) if a.strip()]
        metadata['authors'] = authors[:10]

    return metadata


def extract_sections(text: str) -> list:
    """Extract section structure from paper text."""
    sections = []
    section_pattern = re.compile(
        r'(?:^|\n)\s*'
        r'(\d+\.?\s+)?'
        r'(Abstract|Introduction|Related\s+Work|Background|'
        r'Method(?:ology|s)?|Approach|Framework|'
        r'Experiment(?:s|al)?(?:\s+(?:Setup|Results))?|'
        r'Results?(?:\s+and\s+Discussion)?|'
        r'Discussion|Analysis|Evaluation|'
        r'Conclusion(?:s)?(?:\s+and\s+Future\s+Work)?|'
        r'Future\s+Work|Limitations|'
        r'Acknowledgment(?:s)?|References|Appendix)'
        r'\s*(?:\n|$)',
        re.IGNORECASE | re.MULTILINE
    )

    for match in section_pattern.finditer(text):
        section_num = match.group(1) or ""
        section_name = match.group(2).strip()
        page = max(1, match.start() // 3000 + 1)
        content_start = match.end()
        content_preview = text[content_start:content_start + 300].strip()
        if '.' in content_preview:
            content_preview = content_preview[:content_preview.rfind('.') + 1]
        if len(content_preview) > 200:
            content_preview = content_preview[:200].rsplit(' ', 1)[0] + "..."

        sections.append({
            'number': section_num.strip(),
            'name': section_name,
            'page': page,
            'position': match.start(),
            'preview': content_preview,
        })

    return sections


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
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: #8b5cf6; }
.card-title { font-weight: 600; color: #f1f5f9 !important; font-size: 0.95rem; }
.card-content { color: #cbd5e1 !important; font-size: 0.85rem; line-height: 1.6; }

/* Paper metadata header */
.paper-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.paper-title-main {
    font-size: 1.3rem;
    font-weight: 700;
    color: #f1f5f9 !important;
    line-height: 1.4;
    margin-bottom: 0.75rem;
}
.paper-authors { color: #a78bfa !important; font-size: 0.9rem; margin-bottom: 0.5rem; }
.paper-meta-item {
    display: inline-block;
    background: rgba(139, 92, 246, 0.15);
    color: #c4b5fd !important;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    margin-right: 0.5rem;
    margin-bottom: 0.3rem;
}

/* Section navigation */
.section-nav {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
}
.section-nav-item {
    display: block;
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    color: #cbd5e1 !important;
    font-size: 0.85rem;
    margin-bottom: 0.25rem;
}
.section-num { color: #8b5cf6 !important; font-weight: 600; margin-right: 0.5rem; }
.section-page { color: #64748b !important; font-size: 0.75rem; float: right; }

/* Problem cards for welcome page */
.problem-card {
    background: rgba(139, 92, 246, 0.08);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.problem-title { color: #a78bfa !important; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem; }
.problem-desc { color: #cbd5e1 !important; font-size: 0.8rem; }

/* Notes */
.note-card {
    background: rgba(234, 179, 8, 0.08);
    border: 1px solid rgba(234, 179, 8, 0.25);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.note-timestamp { color: #94a3b8 !important; font-size: 0.7rem; }

/* Search results */
.search-result {
    background: #1e293b;
    border: 1px solid #334155;
    border-left: 3px solid #8b5cf6;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
}
.search-highlight { background: rgba(139, 92, 246, 0.3); padding: 0.1rem 0.3rem; border-radius: 3px; }

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

/* Feature cards for welcome */
.feature-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.25rem;
    text-align: center;
    min-height: 140px;
    transition: all 0.2s;
}
.feature-card:hover { border-color: #8b5cf6; transform: translateY(-2px); }
.feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.feature-title { font-weight: 600; color: #f1f5f9 !important; font-size: 0.95rem; margin-bottom: 0.25rem; }
.feature-desc { color: #94a3b8 !important; font-size: 0.8rem; }

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

.stTextInput input, .stTextArea textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}

.stInfo { background: rgba(139, 92, 246, 0.1) !important; border: 1px solid rgba(139, 92, 246, 0.3) !important; }
.stInfo p { color: #e0e7ff !important; }

.stDownloadButton > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    border: none !important;
    color: white !important;
}
</style>
"""


def extract_images_from_pdf(pdf_file) -> list:
    """Extract page renders and embedded images from PDF using PyMuPDF."""
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

        # First: Render key pages as images (more reliable for showing figures)
        pages_to_render = min(len(doc), 10)  # First 10 pages
        for page_num in range(pages_to_render):
            try:
                page = doc[page_num]
                # Render at 2x zoom for good quality
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                img_count += 1
                images.append({
                    'page': page_num + 1,
                    'index': img_count,
                    'image': pil_image.convert('RGB'),
                    'width': pil_image.width,
                    'height': pil_image.height,
                    'type': 'page'
                })
                pix = None
            except Exception as e:
                logger.debug(f"Page render failed for page {page_num}: {e}")

        # Second: Also try to extract embedded images (diagrams, photos)
        for page_num in range(min(len(doc), 15)):
            try:
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_index, img in enumerate(image_list[:3]):  # Max 3 per page
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        if base_image:
                            image_bytes = base_image["image"]
                            pil_image = Image.open(io.BytesIO(image_bytes))
                            # Only keep larger images (likely figures, not icons)
                            if pil_image.width > 150 and pil_image.height > 150:
                                img_count += 1
                                images.append({
                                    'page': page_num + 1,
                                    'index': img_count,
                                    'image': pil_image.convert('RGB'),
                                    'width': pil_image.width,
                                    'height': pil_image.height,
                                    'type': 'embedded'
                                })
                    except Exception:
                        continue
            except Exception:
                continue
        doc.close()
    except Exception as e:
        logger.error(f"Image extraction failed: {e}")

    return images


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
                ("level", "detailed"), ("images", []), ("equations", []),
                ("citations", None), ("paper_title", None),
                ("metadata", {}), ("sections", []), ("notes", [])]
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

        with st.spinner("Analyzing paper structure..."):
            st.session_state.paper = st.session_state.paper_analyzer.analyze_paper(text)
            st.session_state.analysis = st.session_state.document_analyzer.analyze_document(text)
            st.session_state.metadata = extract_paper_metadata(text)
            st.session_state.sections = extract_sections(text)

        with st.spinner("Building search index..."):
            chunks = st.session_state.text_processor.process(text)
            vectorstore = st.session_state.vectorstore_manager.create_vectorstore(chunks)
            st.session_state.conversation_manager.create_chain(vectorstore)

        with st.spinner("Looking up citations..."):
            paper_title = st.session_state.metadata.get('title')
            if not paper_title:
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                candidate_lines = lines[:5] if len(lines) >= 5 else lines
                if candidate_lines:
                    paper_title = max(candidate_lines, key=lambda l: len(l) if len(l) < 200 else 0)
            st.session_state.paper_title = paper_title
            st.session_state.citations = fetch_scholar_citations(paper_title)

        st.session_state.processed = True
        st.session_state.messages = []
        return True

    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str or "auth" in error_str.lower():
            st.error(
                "**Authentication failed.** Your OpenAI API key was rejected. "
                "Please check that your key is valid and has billing enabled at "
                "[platform.openai.com](https://platform.openai.com/api-keys). "
                "You can update your key in the sidebar under '🔑 API Key'."
            )
        else:
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
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str or "auth" in error_str.lower():
            msg = ("**Authentication error.** Your OpenAI API key is invalid or expired. "
                   "Update it in the sidebar under '🔑 API Key'.")
        else:
            msg = f"Error: {e}"
        st.session_state.messages.append({"role": "assistant", "content": msg})


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

        # API key input (allows override without editing .env)
        with st.expander("🔑 API Key", expanded=not bool(os.getenv("OPENAI_API_KEY"))):
            api_key_input = st.text_input(
                "OpenAI API Key",
                value=os.getenv("OPENAI_API_KEY", ""),
                type="password",
                label_visibility="collapsed",
                placeholder="sk-...",
            )
            if api_key_input and api_key_input != os.getenv("OPENAI_API_KEY", ""):
                os.environ["OPENAI_API_KEY"] = api_key_input
                st.success("API key updated")

        st.divider()

        files = st.file_uploader("Upload PDF", type=['pdf'], accept_multiple_files=True, label_visibility="collapsed")

        if st.button("Analyze Paper", type="primary", width="stretch"):
            if files:
                if process_pdf(files):
                    st.rerun()
            else:
                st.warning("Upload a PDF first")

        if st.session_state.processed:
            st.success(f"Loaded: {st.session_state.filename}")
            img_count = len(st.session_state.images)
            eq_count = len(st.session_state.equations)
            sec_count = len(st.session_state.sections)
            st.caption(f"{img_count} images | {eq_count} equations | {sec_count} sections")

        st.divider()

        st.markdown("**Response Level**")
        st.session_state.level = st.radio(
            "level", ["brief", "detailed", "expert"],
            index=1, horizontal=True, label_visibility="collapsed"
        )

        # Section navigator (when paper is loaded)
        if st.session_state.processed and st.session_state.sections:
            st.divider()
            st.markdown("**Paper Sections**")
            for sec in st.session_state.sections:
                label = f"{sec['number']} {sec['name']}" if sec['number'] else sec['name']
                if st.button(f"  {label}", key=f"nav_{sec['position']}", width="stretch"):
                    ask(f"Summarize the '{sec['name']}' section of this paper.")
                    st.rerun()

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Clear Chat", width="stretch"):
                st.session_state.messages = []
                if "eq_explanations" in st.session_state:
                    st.session_state.eq_explanations = {}
                if "term_definitions" in st.session_state:
                    st.session_state.term_definitions = {}
                st.session_state.conversation_manager.clear_history()
                st.rerun()
        with c2:
            if st.button("Reset All", width="stretch"):
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()


def render_welcome():
    """Render welcome screen."""
    st.markdown('<div class="welcome-title">PaperMind</div>', unsafe_allow_html=True)
    st.markdown('<p class="welcome-sub">AI-Powered Research Paper Analysis</p>', unsafe_allow_html=True)

    st.markdown("""
    <p style="text-align:center; color:#cbd5e1; max-width:600px; margin:0 auto 2rem; font-size: 1rem; line-height: 1.6;">
    Upload a research paper and get instant access to AI-powered analysis.
    PaperMind helps you understand complex papers faster.
    </p>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    features = [
        ("📖", "Smart Glossary", "Auto-detect technical terms with context and AI definitions"),
        ("📐", "Equation Explainer", "Step-by-step breakdowns of mathematical formulas"),
        ("🔍", "Section Navigator", "Jump to any section and get instant AI summaries"),
        ("💬", "Research Q&A", "Ask complex questions and get cited answers"),
    ]
    for i, (icon, title, desc) in enumerate(features):
        with cols[i]:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Common research paper reading problems we solve
    st.markdown('<div class="section-title">Problems We Solve</div>', unsafe_allow_html=True)
    cols2 = st.columns(2)
    problems = [
        ("Dense jargon overload", "Auto-extracted glossary with one-click AI definitions for every technical term."),
        ("Complex math without context", "Every equation is identified and can be explained step-by-step with variable definitions."),
        ("Hard to find key information", "Section-by-section navigation with AI summaries lets you skip to what matters."),
        ("No time to read 20+ pages", "Get a structured overview with stats, keywords, and an extractive summary in seconds."),
        ("Losing track of notes", "Built-in note-taking tied to your paper session, exportable as a text file."),
        ("Understanding figures & tables", "Extracted images with AI-powered figure descriptions on demand."),
    ]
    for i, (title, desc) in enumerate(problems):
        with cols2[i % 2]:
            st.markdown(f"""
            <div class="problem-card">
                <div class="problem-title">{title}</div>
                <div class="problem-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.info("Upload a PDF from the sidebar to begin")


def render_overview():
    """Render overview tab."""
    analysis = st.session_state.analysis
    if not analysis:
        return

    metadata = st.session_state.metadata or {}

    # Paper metadata header
    title = metadata.get('title') or st.session_state.paper_title or "Untitled Paper"
    authors = metadata.get('authors', [])
    year = metadata.get('year')
    doi = metadata.get('doi')

    title_html = sanitize_html(title)
    authors_html = ", ".join(sanitize_html(a) for a in authors) if authors else ""
    meta_items = []
    if year:
        meta_items.append(f'<span class="paper-meta-item">Year: {sanitize_html(year)}</span>')
    if doi:
        meta_items.append(f'<span class="paper-meta-item">DOI: {sanitize_html(doi)}</span>')

    citations_data = st.session_state.citations
    if citations_data and citations_data.get('citations') is not None:
        meta_items.append(f'<span class="paper-meta-item">Cited: {citations_data["citations"]:,} times</span>')

    st.markdown(f"""
    <div class="paper-header">
        <div class="paper-title-main">{title_html}</div>
        {"<div class='paper-authors'>" + authors_html + "</div>" if authors_html else ""}
        <div>{"".join(meta_items)}</div>
    </div>
    """, unsafe_allow_html=True)

    # Google Scholar link
    if citations_data and citations_data.get('scholar_url'):
        scholar_url = citations_data['scholar_url']
        st.markdown(
            f'<div class="card">'
            f'<div class="card-content"><a href="{scholar_url}" target="_blank" '
            f'style="color: #a78bfa;">View on Google Scholar</a></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Stats
    stats = analysis.get('stats', {})
    st.markdown('<div class="section-title">Document Statistics</div>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Words", f"{stats.get('words', 0):,}")
    c2.metric("Read Time", stats.get('reading_time', '-'))
    c3.metric("Sections", len(st.session_state.sections))
    c4.metric("Images", len(st.session_state.images))
    c5.metric("Equations", len(st.session_state.equations))

    # Summary
    st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
    if analysis.get('summary'):
        st.markdown(f"""
        <div class="card">
            <div class="card-content">{sanitize_html(analysis['summary'])}</div>
        </div>
        """, unsafe_allow_html=True)

    # Section breakdown
    sections = st.session_state.sections
    if sections:
        st.markdown('<div class="section-title">Paper Structure</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-nav">', unsafe_allow_html=True)
        for sec in sections:
            num = sanitize_html(sec['number'])
            name = sanitize_html(sec['name'])
            st.markdown(f"""
            <div class="section-nav-item">
                <span class="section-num">{num}</span>{name}
                <span class="section-page">p.{sec['page']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Keywords
    st.markdown('<div class="section-title">Key Topics</div>', unsafe_allow_html=True)
    keywords = analysis.get('keywords', [])[:15]
    if keywords:
        html = "".join([f'<span class="keyword">{sanitize_html(k)}</span>' for k in keywords])
        st.markdown(html, unsafe_allow_html=True)


def render_equations():
    """Render equations tab with proper display."""
    equations = st.session_state.equations

    st.markdown('<div class="section-title">Mathematical Equations</div>', unsafe_allow_html=True)

    if not equations:
        st.markdown("""
        <div class="image-placeholder">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📐</div>
            <div>No equations detected in this paper</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"Found **{len(equations)}** equations in the paper:")

    # Track which equation explanations have been generated
    if "eq_explanations" not in st.session_state:
        st.session_state.eq_explanations = {}

    for eq in equations:
        st.markdown(f"""
        <div class="equation-card">
            <div class="equation-formula">{eq['content']}</div>
            <div class="equation-label">Equation {eq['id']} • Page {eq['page']}</div>
        </div>
        """, unsafe_allow_html=True)

        eq_key = f"eq_{eq['id']}"

        # Show existing explanation or explain button
        if eq_key in st.session_state.eq_explanations:
            with st.expander(f"Explanation for Equation {eq['id']}", expanded=True):
                st.markdown(f'<div class="ai-msg">{st.session_state.eq_explanations[eq_key]}</div>', unsafe_allow_html=True)
        else:
            if st.button(f"🔍 Explain Equation {eq['id']}", key=eq_key):
                with st.spinner(f"Explaining Equation {eq['id']}..."):
                    try:
                        response = st.session_state.conversation_manager.ask(
                            f"Explain this equation step by step, defining each variable: {eq['content']}"
                        )
                        explanation = response.get('answer', 'Could not generate explanation.')
                        st.session_state.eq_explanations[eq_key] = explanation
                    except Exception as e:
                        st.session_state.eq_explanations[eq_key] = f"Error: {e}"
                st.rerun()


def render_figures():
    """Render figures tab with page previews and embedded images."""
    images = st.session_state.images
    paper = st.session_state.paper

    st.markdown('<div class="section-title">Figures & Images</div>', unsafe_allow_html=True)

    if not images:
        st.markdown("""
        <div class="image-placeholder">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🖼️</div>
            <div>No figures could be extracted from this PDF</div>
            <div style="font-size: 0.8rem; margin-top: 0.5rem;">
                PyMuPDF library may not be installed.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Separate page renders from embedded images
    page_images = [img for img in images if img.get('type') == 'page']
    embedded_images = [img for img in images if img.get('type') == 'embedded']

    # Create sub-tabs for Pages and Embedded Images
    if embedded_images:
        fig_tab1, fig_tab2 = st.tabs([f"📄 Pages ({len(page_images)})", f"🖼️ Extracted ({len(embedded_images)})"])
    else:
        fig_tab1 = st.container()
        fig_tab2 = None

    # Page previews
    with fig_tab1:
        if page_images:
            st.markdown(f"**{len(page_images)} pages** rendered from the PDF:")

            # Page selector with navigation callbacks
            page_nums = [img['page'] for img in page_images]

            # Initialize page index in session state
            if "page_idx" not in st.session_state:
                st.session_state.page_idx = 0

            # Clamp to valid range
            st.session_state.page_idx = max(0, min(st.session_state.page_idx, len(page_nums) - 1))

            # Navigation row
            nav1, nav2, nav3 = st.columns([1, 3, 1])
            with nav1:
                if st.button("← Prev", key="prev_page", disabled=st.session_state.page_idx == 0):
                    st.session_state.page_idx -= 1
                    st.rerun()
            with nav2:
                def on_page_change():
                    st.session_state.page_idx = page_nums.index(st.session_state._page_select)

                st.selectbox(
                    "Jump to page:",
                    page_nums,
                    index=st.session_state.page_idx,
                    format_func=lambda x: f"Page {x}",
                    key="_page_select",
                    on_change=on_page_change,
                )
            with nav3:
                if st.button("Next →", key="next_page", disabled=st.session_state.page_idx >= len(page_nums) - 1):
                    st.session_state.page_idx += 1
                    st.rerun()

            selected_page = page_nums[st.session_state.page_idx]

            # Show selected page
            for img_data in page_images:
                if img_data['page'] == selected_page:
                    st.markdown(f"""
                    <div class="figure-card">
                        <div class="figure-header">
                            <div class="figure-icon">📄</div>
                            <div>
                                <div class="figure-title">Page {img_data['page']}</div>
                                <div class="figure-meta">{img_data['width']}×{img_data['height']}px</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.image(img_data['image'], width="stretch")

                    if st.button(f"Explain figures on this page", key=f"explain_page_{img_data['page']}"):
                        ask(f"Describe and explain any figures, charts, tables, or diagrams that appear on page {img_data['page']} of this paper.")
                        st.rerun()
                    break

    # Embedded images
    if fig_tab2 is not None:
        with fig_tab2:
            if embedded_images:
                st.markdown(f"**{len(embedded_images)} embedded images** extracted:")
                cols_per_row = 2
                for i in range(0, len(embedded_images), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(embedded_images):
                            img_data = embedded_images[i + j]
                            with col:
                                st.markdown(f"""
                                <div class="figure-card">
                                    <div class="figure-header">
                                        <div class="figure-icon">🖼️</div>
                                        <div>
                                            <div class="figure-title">Image from Page {img_data['page']}</div>
                                            <div class="figure-meta">{img_data['width']}×{img_data['height']}px</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                st.image(img_data['image'], width="stretch")

    # Also show figure references from text analysis
    if paper:
        figures = [f for f in paper.get('figures', []) if f.type in ['figure', 'table']]
        if figures:
            with st.expander(f"📝 Figure/Table References ({len(figures)} mentioned in text)"):
                for fig in figures[:10]:
                    icon = "📊" if fig.type == "figure" else "📋"
                    st.markdown(f"**{icon} {fig.title}** (Page {fig.page}): {fig.caption}")


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
    st.markdown('<div class="section-title">Technical Terms</div>', unsafe_allow_html=True)

    if not terms:
        st.caption("No technical terms detected.")
        return

    st.markdown(f"Found **{len(terms)}** key technical terms:")

    # Search/filter terms
    term_search = st.text_input("Filter terms", placeholder="Type to filter...", label_visibility="collapsed")
    if term_search:
        terms = [t for t in terms if term_search.lower() in t.term.lower()]

    # Track term definitions
    if "term_definitions" not in st.session_state:
        st.session_state.term_definitions = {}

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

        term_key = f"term_{term.term}"

        # Show existing definition or define button
        if term_key in st.session_state.term_definitions:
            with st.expander(f"Definition of '{term.term}'", expanded=True):
                st.markdown(f'<div class="ai-msg">{st.session_state.term_definitions[term_key]}</div>', unsafe_allow_html=True)
        else:
            if st.button(f"📖 Define '{term.term}'", key=term_key):
                with st.spinner(f"Defining '{term.term}'..."):
                    try:
                        response = st.session_state.conversation_manager.ask(
                            f"Define '{term.term}' in the context of this research paper. What does it mean and why is it important?"
                        )
                        definition = response.get('answer', 'Could not generate definition.')
                        st.session_state.term_definitions[term_key] = definition
                    except Exception as e:
                        st.session_state.term_definitions[term_key] = f"Error: {e}"
                st.rerun()


def render_chat():
    """Render chat interface."""
    st.markdown('<div class="section-title">Quick Actions</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    actions = [
        ("Summary", "Provide a comprehensive summary of this paper including the main problem, approach, and results."),
        ("Key Takeaways", "What are the key takeaways, main contributions, and novel aspects of this paper?"),
        ("Methodology", "Explain the methodology and approach used in this paper step by step."),
        ("Prerequisites", "What background knowledge and prerequisites are needed to understand this paper?"),
    ]

    for i, (label, q) in enumerate(actions):
        with [c1, c2, c3, c4][i]:
            if st.button(label, width="stretch"):
                ask(q)
                st.rerun()

    # Additional quick actions row
    c5, c6, c7, c8 = st.columns(4)
    actions2 = [
        ("Limitations", "What are the limitations and potential weaknesses of this paper?"),
        ("Comparisons", "How does this work compare to existing methods and baselines?"),
        ("Future Work", "What future research directions does this paper suggest?"),
        ("Datasets", "What datasets and evaluation metrics are used in this paper?"),
    ]
    for i, (label, q) in enumerate(actions2):
        with [c5, c6, c7, c8][i]:
            if st.button(label, width="stretch"):
                ask(q)
                st.rerun()

    st.markdown("---")

    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-msg">{sanitize_html(msg["content"])}</div>', unsafe_allow_html=True)
        else:
            content = msg["content"]
            sources_html = ""
            if msg.get("sources"):
                sources_html = '<div class="source-ref">' + "<br>".join(
                    [f"Source: {sanitize_html(s)}" for s in msg["sources"]]
                ) + '</div>'
            st.markdown(f'<div class="ai-msg">{content}{sources_html}</div>', unsafe_allow_html=True)

    # Suggested questions
    if not st.session_state.messages:
        analysis = st.session_state.analysis
        if analysis and analysis.get('suggested_questions'):
            st.markdown('<div class="section-title">Suggested Questions</div>', unsafe_allow_html=True)
            for q in analysis['suggested_questions'][:4]:
                if st.button(f"{q}", key=f"sq_{hash(q)}"):
                    ask(q)
                    st.rerun()

    st.markdown("---")
    question = st.chat_input("Ask about the paper...")
    if question:
        ask(question)
        st.rerun()


def render_search():
    """Render text search tab."""
    st.markdown('<div class="section-title">Search Paper</div>', unsafe_allow_html=True)

    search_query = st.text_input("Search for keywords or phrases in the paper",
                                  placeholder="e.g., attention mechanism, loss function, dataset...",
                                  label_visibility="collapsed")

    if search_query and st.session_state.text:
        text = st.session_state.text
        query_lower = search_query.lower()
        lines = text.split('\n')

        results = []
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                context = '\n'.join(lines[start:end])
                char_pos = sum(len(lines[j]) + 1 for j in range(i))
                page = max(1, char_pos // 3000 + 1)
                results.append({
                    'context': context,
                    'page': page,
                    'line': i + 1,
                })

        if results:
            st.markdown(f"Found **{len(results)}** matches for \"{sanitize_html(search_query)}\":")
            for r in results[:20]:
                context_safe = sanitize_html(r['context'])
                highlighted = re.sub(
                    f'({re.escape(sanitize_html(search_query))})',
                    r'<span class="search-highlight">\1</span>',
                    context_safe,
                    flags=re.IGNORECASE
                )
                st.markdown(f"""
                <div class="search-result">
                    <div style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.25rem;">
                        Page ~{r['page']} | Line {r['line']}
                    </div>
                    <div style="font-size: 0.85rem; line-height: 1.5;">{highlighted}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption(f"No matches found for \"{search_query}\"")
    elif not search_query:
        st.caption("Enter a search term to find specific content in the paper.")

    # AI-powered semantic search
    st.markdown('<div class="section-title">AI-Powered Search</div>', unsafe_allow_html=True)
    ai_query = st.text_input("Ask a specific question to search semantically",
                              placeholder="e.g., What dataset was used for training?",
                              key="ai_search")
    if ai_query:
        if st.button("Search", key="ai_search_btn"):
            ask(ai_query)
            st.rerun()


def render_notes():
    """Render notes and annotations tab."""
    st.markdown('<div class="section-title">Research Notes</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-content">
            Keep track of your thoughts, questions, and key insights as you read the paper.
            Your notes are saved for the current session.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add new note
    new_note = st.text_area("Add a note", placeholder="Type your thoughts, questions, or key insights...",
                             height=100, label_visibility="collapsed")
    note_category = st.selectbox("Category", ["Insight", "Question", "Key Finding", "Critique", "Follow-up"],
                                  label_visibility="collapsed")

    if st.button("Add Note", type="primary"):
        if new_note.strip():
            st.session_state.notes.append({
                'text': new_note.strip(),
                'category': note_category,
                'timestamp': datetime.now().strftime("%H:%M:%S"),
            })
            st.rerun()

    # Display existing notes
    if st.session_state.notes:
        st.markdown(f'<div class="section-title">Your Notes ({len(st.session_state.notes)})</div>',
                     unsafe_allow_html=True)

        for i, note in enumerate(reversed(st.session_state.notes)):
            category_colors = {
                'Insight': '#8b5cf6', 'Question': '#f59e0b',
                'Key Finding': '#10b981', 'Critique': '#ef4444', 'Follow-up': '#3b82f6',
            }
            color = category_colors.get(note['category'], '#8b5cf6')
            st.markdown(f"""
            <div class="note-card" style="border-left: 3px solid {color};">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: {color}; font-weight: 600; font-size: 0.8rem;">{note['category']}</span>
                    <span class="note-timestamp">{note['timestamp']}</span>
                </div>
                <div class="card-content">{sanitize_html(note['text'])}</div>
            </div>
            """, unsafe_allow_html=True)

        # Export notes
        st.markdown("---")
        export_content = _build_export_content()
        st.download_button(
            "Export Notes & Summary",
            data=export_content,
            file_name=f"papermind_notes_{st.session_state.filename or 'paper'}.txt",
            mime="text/plain",
            width="stretch",
        )
    else:
        st.caption("No notes yet. Start adding notes as you read!")


def _build_export_content() -> str:
    """Build export content with summary and notes."""
    lines = []
    lines.append("=" * 60)
    lines.append("PaperMind - Research Notes Export")
    lines.append("=" * 60)
    lines.append("")

    title = st.session_state.paper_title or "Unknown Paper"
    lines.append(f"Paper: {title}")
    lines.append(f"File: {st.session_state.filename or 'N/A'}")
    lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    analysis = st.session_state.analysis
    if analysis and analysis.get('summary'):
        lines.append("-" * 40)
        lines.append("SUMMARY")
        lines.append("-" * 40)
        lines.append(analysis['summary'])
        lines.append("")

    if analysis and analysis.get('keywords'):
        lines.append("-" * 40)
        lines.append("KEY TOPICS")
        lines.append("-" * 40)
        lines.append(", ".join(analysis['keywords'][:15]))
        lines.append("")

    if st.session_state.notes:
        lines.append("-" * 40)
        lines.append("RESEARCH NOTES")
        lines.append("-" * 40)
        for note in st.session_state.notes:
            lines.append(f"[{note['category']}] ({note['timestamp']})")
            lines.append(f"  {note['text']}")
            lines.append("")

    if st.session_state.messages:
        lines.append("-" * 40)
        lines.append("Q&A HISTORY")
        lines.append("-" * 40)
        for msg in st.session_state.messages:
            role = "Q" if msg['role'] == 'user' else "A"
            lines.append(f"{role}: {msg['content']}")
            lines.append("")

    return "\n".join(lines)


def main():
    # Check for API key first
    if not check_api_key():
        render_api_key_error()
        return

    st.set_page_config(page_title="PaperMind", page_icon="📚", layout="wide", initial_sidebar_state="expanded")
    st.markdown(CSS, unsafe_allow_html=True)

    init_state()
    render_sidebar()

    if not st.session_state.processed:
        render_welcome()
    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Chat", "Overview", "Equations",
            "Figures", "Terms", "Search", "Notes",
        ])
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
        with tab6:
            render_search()
        with tab7:
            render_notes()


if __name__ == '__main__':
    main()
